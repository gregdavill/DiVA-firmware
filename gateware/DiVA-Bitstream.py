#!/usr/bin/env python3

# This file is Copyright (c) 2020 Gregory Davill <greg.davill@gmail.com>
# License: BSD

# This variable defines all the external programs that this module
# relies on.  lxbuildenv reads this variable in order to ensure
# the build will finish without exiting due to missing third-party
# programs.
LX_DEPENDENCIES = ["riscv", "nextpnr-ecp5", "yosys"]

# Import lxbuildenv to integrate the deps/ directory
import lxbuildenv


import sys
import argparse
import optparse
import subprocess
import os
import shutil

from migen import *

from rtl.platform import bosonHDMI_r0d3


from litex.build.generic_platform import *
from litex.soc.cores.clock import *
from rtl.ecp5_dynamic_pll import ECP5PLL, period_ns
from litex.soc.integration.soc_core import *
from litex.soc.integration.soc import SoCRegion
from litex.soc.integration.builder import *

from litex.soc.cores.bitbang import I2CMaster
from litex.soc.cores.gpio import GPIOOut, GPIOIn

from litex.soc.interconnect import stream, wishbone
from litex.soc.interconnect.stream import Endpoint, EndpointDescription, SyncFIFO, AsyncFIFO, Monitor
from litex.soc.interconnect.csr import *

from migen.genlib.misc import timeline
from migen.genlib.cdc import MultiReg, PulseSynchronizer

from rtl.prbs import PRBSStream
from rtl.edge_detect import EdgeDetect
from rtl.wb_streamer import StreamReader, StreamWriter, StreamBuffers
from rtl.hdmi import HDMI
from rtl.rgb_led import RGB
from rtl.reboot import Reboot
from rtl.buttons import Button
from rtl.streamable_hyperram import StreamableHyperRAM
from rtl.buffered_csr_block import BufferedCSRBlock

from rtl.video.terminal import Terminal
from rtl.video.boson import Boson
from rtl.video.YCrCb import YCbCr2RGB, YCbCr422to444, ycbcr444_layout

from rtl.video.simulated_video import SimulatedVideo
from rtl.video.video_debug import VideoDebug
from rtl.video.video_stream import VideoStream
from rtl.video.framer import Framer, framer_params
from rtl.video.scaler import Scaler

class _CRG(Module, AutoCSR):
    def __init__(self, platform, sys_clk_freq):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_video = ClockDomain()
        self.clock_domains.cd_video_shift = ClockDomain()
        


        self.clock_domains.cd_hr = ClockDomain()
        self.clock_domains.cd_hr_90 = ClockDomain()
        self.clock_domains.cd_hr2x = ClockDomain()
        self.clock_domains.cd_hr2x_90 = ClockDomain()
        self.clock_domains.cd_hr2x_ = ClockDomain()
        self.clock_domains.cd_hr2x_90_ = ClockDomain()

        self.clock_domains.cd_init = ClockDomain()
        

        # # #

        # clk / rst
        clk48 = platform.request("clk48")

        self.submodules.pll = pll = ECP5PLL()
        pll.register_clkin(clk48, 48e6)
        pll.create_clkout(self.cd_hr2x, sys_clk_freq*2, margin=0)
        pll.create_clkout(self.cd_hr2x_90, sys_clk_freq*2, phase=1, margin=0) # SW tunes this phase during init
        
        self.specials += [
        ]

        self.comb += self.cd_sys.clk.eq(self.cd_hr.clk)
        self.comb += self.cd_init.clk.eq(clk48)

        pixel_clk = 40e6
        self.clock_domains.cd_usb_12 = ClockDomain()
        self.clock_domains.cd_usb_48 = ClockDomain()

        self.submodules.video_pll = video_pll = ECP5PLL()
        video_pll.register_clkin(clk48, 48e6)
        video_pll.create_clkout(self.cd_video,    pixel_clk,  margin=0)
        video_pll.create_clkout(self.cd_video_shift,  pixel_clk*5, margin=0)
        video_pll.create_clkout(self.cd_usb_12,    12e6,  margin=0)


        self.comb += self.cd_usb_48.clk.eq(clk48)


        platform.add_period_constraint(self.cd_usb_12.clk, period_ns(12e6))
        platform.add_period_constraint(self.cd_usb_48.clk, period_ns(48e6))
        platform.add_period_constraint(self.cd_sys.clk, period_ns(sys_clk_freq))
        platform.add_period_constraint(clk48, period_ns(48e6))
        platform.add_period_constraint(self.cd_video.clk, period_ns(pixel_clk))
        platform.add_period_constraint(self.cd_video_shift.clk, period_ns(pixel_clk * 5))

        self._slip_hr2x = CSRStorage()
        self._slip_hr2x90 = CSRStorage()

        # ECLK stuff 
        self.specials += [
            Instance("CLKDIVF",
                p_DIV     = "2.0",
                i_ALIGNWD = self._slip_hr2x.storage,
                i_CLKI    = self.cd_hr2x.clk,
                i_RST     = ~pll.locked,
                o_CDIVX   = self.cd_hr.clk),

            Instance("CLKDIVF",
                p_DIV     = "2.0",
                i_ALIGNWD = self._slip_hr2x90.storage,
                i_CLKI    = self.cd_hr2x_90.clk,
                i_RST     = ~pll.locked,
                o_CDIVX   = self.cd_hr_90.clk),
            #AsyncResetSynchronizer(self.cd_hr, reset),
            #AsyncResetSynchronizer(self.cd_sys, reset)
        ]


        self._phase_sel = CSRStorage(2)
        self._phase_dir = CSRStorage()
        self._phase_step = CSRStorage()
        self._phase_load = CSRStorage()

        self.comb += [
            self.pll.phase_sel.eq(self._phase_sel.storage),
            self.pll.phase_dir.eq(self._phase_dir.storage),
            self.pll.phase_step.eq(self._phase_step.storage),
            self.pll.phase_load.eq(self._phase_load.storage),
        ]

        # OSC-G for simulated video streams
        oscg_clk = Signal()
        self.clock_domains.cd_oscg_38M = ClockDomain()
        self.specials += Instance("OSCG",
            p_DIV=8,
            o_OSC=oscg_clk
        )
        self.comb += self.cd_oscg_38M.clk.eq(oscg_clk)


       

class DiVA_SoC(SoCCore):
    csr_map = {
        "rgb"        :  10, 
        "crg"        :  11, 
        "hyperram"   :  12,
        "terminal"   :  13,
        "analyzer"   :  14,
        "hdmi_i2c"   :  15,
        "i2c0"        :  16,
        "button"     :  18,
        "reader"     :  19,
        "writer"     :  20,
        "buffers"     :  21,
        "prbs"       :  23,
        "reboot"     :  25,
        "video_debug":  26,
        "framer"     :  27,
        "scaler"     :  28,
        "boson"      :  29,
        "pipeline_config" : 30,
    }
    csr_map.update(SoCCore.csr_map)

    mem_map = {
        "hyperram"  : 0x10000000,
        "terminal"  : 0x30000000,
    }
    mem_map.update(SoCCore.mem_map)

    interrupt_map = {

    }
    interrupt_map.update(SoCCore.interrupt_map)

    def __init__(self):
        
        self.platform = platform = bosonHDMI_r0d3.Platform()
        
        sys_clk_freq = 82.5e6
        SoCCore.__init__(self, platform, clk_freq=sys_clk_freq,
                          cpu_type='serv', with_uart=True, uart_name='stream',
                          csr_data_width=32,
                          ident="Boson DiVA SoC", ident_version=True, wishbone_timeout_cycles=128,
                          integrated_rom_size=32*1024)

        self.platform.toolchain.build_template[0] = "yosys -q -l {build_name}.rpt {build_name}.ys"
        self.platform.toolchain.build_template[1] += f" --log {platform.name}.log --router router1"

        # Fake a UART stream, to enable easy firmware reuse.
        self.comb += self.uart.source.ready.eq(1)
    
        # crg
        self.submodules.crg = _CRG(platform, sys_clk_freq)
     
        ## Create VGA terminal
        self.submodules.terminal = terminal = ClockDomainsRenamer({'vga':'video'})(Terminal())
        self.register_mem("terminal", self.mem_map["terminal"], terminal.bus, size=0x100000)

        # User inputs
        button = platform.request("button")
        self.submodules.button = Button(button)

        self.submodules.rgb = RGB(platform.request("rgb_led"))
        
        # HyperRAM
        self.submodules.writer = writer = StreamWriter()
        self.submodules.reader = reader = StreamReader()

        # Attach a StreamBuffer module to handle buffering of frames
        self.submodules.buffers = buffers = StreamBuffers()
        self.comb += [
            buffers.rx_release.eq(reader.evt_done),
            reader.start_address.eq(buffers.rx_buffer),
            writer.start_address.eq(buffers.tx_buffer),
        ]


        self.submodules.hyperram = hyperram = StreamableHyperRAM(platform.request("hyperRAM"), devices=[reader, writer])
        self.register_mem("hyperram", self.mem_map['hyperram'], hyperram.bus, size=0x800000)

        # Boson video stream
        self.submodules.boson = boson = Boson(platform, platform.request("boson"), sys_clk_freq)

        self.submodules.YCbCr = ycrcb = ClockDomainsRenamer({"sys":"boson_rx"})(ResetInserter()(YCbCr2RGB()))
        self.submodules.YCbCr422_444 = ycrcb422_444 = ClockDomainsRenamer({"sys":"boson_rx"})(YCbCr422to444())

        
        fifo = AsyncFIFO([("data", 32)], depth=512)
        fifo = ResetInserter(["read","write"])(fifo)
        fifo = ClockDomainsRenamer({"read":"sys","write":"boson_rx"})(fifo)
        
        self.submodules.video_debug = video_debug = ClockDomainsRenamer({"pixel":"boson_rx"})(VideoDebug(int(self.clk_freq)))
        
        self.submodules.pipeline_config = pipeline_config = BufferedCSRBlock(
            [
                ("scaler_enable", 1),
                ("scaler_fill", 1),
            ] + framer_params()
        )  

        self.submodules.framer = framer = Framer()
        self.comb += [
            framer.params.x_start.eq(pipeline_config.x_start),
            framer.params.y_start.eq(pipeline_config.y_start),
            framer.params.x_stop.eq(pipeline_config.x_stop),
            framer.params.y_stop.eq(pipeline_config.y_stop),
        ]

        self.submodules.scaler = scaler = ResetInserter(["video"])(ClockDomainsRenamer({"sys":"video", "cpu":"sys"})((Scaler())))
        self.submodules.fifo2 = fifo2 = ResetInserter()(ClockDomainsRenamer({"sys":"video"})(SyncFIFO([("data", 32)], depth=32)))

        self.submodules += fifo

        self.comb += [
            video_debug.vsync.eq(boson.vsync),
            video_debug.hsync.eq(boson.hsync),

            boson.source.connect(ycrcb422_444.sink, omit=['data']),
            ycrcb422_444.source.connect(ycrcb.sink),
            ycrcb.source.connect(fifo.sink, omit=['r','g','b']),

            ycrcb422_444.sink.y.eq(boson.source.data[0:8]),
            ycrcb422_444.sink.cb_cr.eq(boson.source.data[8:16]),

            fifo.sink.data[0:8].eq(ycrcb.source.r),
            fifo.sink.data[8:16].eq(ycrcb.source.g),
            fifo.sink.data[16:24].eq(ycrcb.source.b),

            fifo.source.connect(reader.sink),
        ]

        boson_stream_start = Signal()
        reader.add_source(fifo.source, "boson_stream", boson_stream_start)




        ## HDMI output
        hdmi_pins = platform.request('hdmi')
        self.submodules.hdmi = hdmi =  HDMI(platform, hdmi_pins)
        self.submodules.hdmi_i2c = I2CMaster(platform.request("hdmi_i2c"))


        # I2C
        self.submodules.i2c0 = I2CMaster(platform.request("i2c"))

        self.submodules.reboot = Reboot(platform.request("rst_n"))


        fifo0 = AsyncFIFO([("data", 32)], depth=128)
        fifo0 = ResetInserter(["read","write"])(fifo0)
        fifo0 = ClockDomainsRenamer({"read":"video","write":"sys"})(fifo0)
        self.submodules += fifo0

        self.comb += [
            If(pipeline_config.scaler_enable,
                fifo0.source.connect(scaler.sink),
                scaler.source.connect(fifo2.sink),
                fifo2.source.connect(framer.sink),
            ).Else(
                fifo0.source.connect(framer.sink),
            ),

            writer.short.eq(pipeline_config.scaler_fill),
        ]

        boson_sink_start = Signal()
        writer.add_sink(fifo0.sink, "boson", boson_sink_start)

        # prbs tester
        self.submodules.prbs = PRBSStream()
        reader.add_source(self.prbs.source.source, "prbs")
        writer.add_sink(self.prbs.sink.sink, "prbs")

        # enable
        self.submodules.vsync_rise = vsync_rise = EdgeDetect(mode="rise", input_cd="video", output_cd="sys")
        self.comb += vsync_rise.i.eq(terminal.vsync)

        self.submodules.vsync_rise_term = vsync_rise_term = EdgeDetect(mode="rise", input_cd="video", output_cd="video")
        self.comb += vsync_rise_term.i.eq(terminal.vsync)
        self.submodules.vsync_fall_term = vsync_fall_term = EdgeDetect(mode="fall", input_cd="video", output_cd="video")
        self.comb += vsync_fall_term.i.eq(terminal.vsync)



        self.submodules.vsync_boson = vsync_boson = EdgeDetect(mode="fall", input_cd="boson_rx", output_cd="sys")
        self.comb += vsync_boson.i.eq(boson.vsync)


        self.comb += [
            boson_sink_start.eq(vsync_rise.o),
            scaler.reset_video.eq(vsync_rise_term.o),
            fifo2.reset.eq(vsync_rise_term.o),

            fifo0.reset_read.eq(vsync_rise_term.o),
            fifo0.reset_write.eq(vsync_rise.o),

            pipeline_config.csr_sync.eq(vsync_fall_term.o)
        ]
        
        # delay vsync pulse from boson by 500 clocks, then use it to reset the fifo
        fifo_rst = Signal()
        self.sync += [
             timeline(vsync_boson.o, [
                (101,  [fifo_rst.eq(1)]),   # Reset FIFO
                (102,  [fifo_rst.eq(0)]),  # Clear Reset
                (110,  [boson_stream_start.eq(1)]),
                (111,  [boson_stream_start.eq(0)])
            ])
        ]
        #self.specials += MultiReg(fifo_rst, fifo.reset_write, odomain="boson_rx")

        fifo_rst_ps = PulseSynchronizer("sys", "boson_rx")
        self.comb += fifo_rst_ps.i.eq(fifo_rst)
        self.comb += fifo.reset_write.eq(fifo_rst_ps.o)
        self.comb += fifo.reset_read.eq(fifo_rst)
        self.submodules += fifo_rst_ps
       

        terminal_mask = Signal()
        ## Connect VGA pins
        self.comb += [
            fifo.reset_read.eq(fifo_rst),
            ycrcb.reset.eq(fifo_rst),
            ycrcb422_444.reset.eq(fifo_rst),

            # attach framer to video generator
            framer.vsync.eq(terminal.vsync),
            framer.hsync.eq(terminal.hsync),
            

            hdmi.vsync.eq(terminal.vsync),
            hdmi.hsync.eq(terminal.hsync),
            hdmi.blank.eq(terminal.blank),

            # Mask Through on 0xFFFF00 pixels
            terminal_mask.eq((terminal.red == 0xaa) & (terminal.green == 0x00) & (terminal.blue == 0xaa)),
            
            If(terminal_mask,
                If(framer.data_valid,
                    hdmi.r.eq(framer.red),
                    hdmi.g.eq(framer.green),
                    hdmi.b.eq(framer.blue),
                )
            ).Else(
                hdmi.r.eq(terminal.red),
                hdmi.g.eq(terminal.green),
                hdmi.b.eq(terminal.blue),  
            )
        ]

        
        usb_pads = self.platform.request("usb")

        # Select Boson as USB target
        if hasattr(usb_pads, "sw_sel"):
            self.comb += usb_pads.sw_sel.eq(0)
        
        # Enable USB
        if hasattr(usb_pads, "sw_oe"):
            self.comb += usb_pads.sw_oe.eq(0)

        analyser = False
        if analyser:
            # USB with Clock-Domain-Crossing support
            import os
            import sys
            os.system("git clone https://github.com/gregdavill/valentyusb -b hw_cdc_eptri")
            sys.path.append("valentyusb")

            import valentyusb.usbcore.io as usbio
            import valentyusb.usbcore.cpu.cdc_eptri as cdc_eptri
            usb_pads = self.platform.request("usb")
            usb_iobuf = usbio.IoBuf(usb_pads.d_p, usb_pads.d_n, usb_pads.pullup)
            self.submodules.uart_usb = cdc_eptri.CDCUsb(usb_iobuf)

            # Select ECP5 as USB target
            if hasattr(usb_pads, "sw_sel"):
                self.comb += usb_pads.sw_sel.eq(1)
            
            # Enable USB
            if hasattr(usb_pads, "sw_oe"):
                self.comb += usb_pads.sw_oe.eq(0)
            

            self.submodules.bridge = Stream2Wishbone(self.uart_usb, sys_clk_freq)
            self.add_wb_master(self.bridge.wishbone)

            self.submodules.analyzer = LiteScopeAnalyzer(hyperram.dbg, 64)

        # Add git version into firmware 
        def get_git_revision():
            try:
                r = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                        stderr=subprocess.DEVNULL)[:-1].decode("utf-8")
            except:
                r = "--------"
            return r
        self.add_constant("DIVA_GIT_SHA1", get_git_revision())

    def do_exit(self, vns):
        if hasattr(self, "analyzer"):
            self.analyzer.export_csv(vns, "test/analyzer.csv")


    def PackageFirmware(self, builder):  
        self.finalize()

        os.makedirs(builder.output_dir, exist_ok=True)

        src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "firmware", "DiVA-fw"))
        builder.add_software_package("DiVA-fw", src_dir)

        builder._prepare_rom_software()
        builder._generate_includes()
        builder._generate_rom_software(compile_bios=False)

        firmware_file = os.path.join(builder.output_dir, "software", "DiVA-fw","DiVA-fw.bin")
        firmware_data = get_mem_data(firmware_file, self.cpu.endianness)
        self.initialize_rom(firmware_data)

        # lock out compiling firmware during build steps
        builder.compile_software = False


def CreateFirmwareInit(init, output_file):
    content = ""
    for d in init:
        content += "{:08x}\n".format(d)
    with open(output_file, "w") as o:
        o.write(content)    
     
def main():
    parser = argparse.ArgumentParser(
        description="Build DiVA Gateware")
    parser.add_argument(
        "--update-firmware", default=False, action='store_true',
        help="compile firmware and update existing gateware"
    )
    args = parser.parse_args()

    soc = DiVA_SoC()
    builder = Builder(soc, output_dir="build", csr_csv="build/csr.csv")

    # Build firmware
    soc.PackageFirmware(builder)
        

    # Check if we have the correct files
    firmware_file = os.path.join(builder.output_dir, "software", "DiVA-fw", "DiVA-fw.bin")
    firmware_data = get_mem_data(firmware_file, soc.cpu.endianness)
    firmware_init = os.path.join(builder.output_dir, "software", "DiVA-fw", "DiVA-fw.init")
    CreateFirmwareInit(firmware_data, firmware_init)
    
    rand_rom = os.path.join(builder.output_dir, "gateware", "rand.data")
    
    input_config = os.path.join(builder.output_dir, "gateware", f"{soc.platform.name}.config")
    output_config = os.path.join(builder.output_dir, "gateware", f"{soc.platform.name}_patched.config")
    
    # If we don't have a random file, create one, and recompile gateware
    if (os.path.exists(rand_rom) == False) or (args.update_firmware == False):
        os.makedirs(os.path.join(builder.output_dir,'gateware'), exist_ok=True)
        os.makedirs(os.path.join(builder.output_dir,'software'), exist_ok=True)

        os.system(f"ecpbram  --generate {rand_rom} --seed {0} --width {32} --depth {soc.integrated_rom_size}")

        # patch random file into BRAM
        data = []
        with open(rand_rom, 'r') as inp:
            for d in inp.readlines():
                data += [int(d, 16)]
        soc.initialize_rom(data)

        # Build gateware
        vns = builder.build(nowidelut=False)
        soc.do_exit(vns)    


    # Insert Firmware into Gateware
    os.system(f"ecpbram  --input {input_config} --output {output_config} --from {rand_rom} --to {firmware_init}")

    # create a compressed bitstream
    output_bit = os.path.join(builder.output_dir, "gateware", "DiVA.dfu")
    os.system(f"ecppack --freq 38.8 --compress --input {output_config} --bit {output_bit}")

    # Add DFU suffix
    os.system(f"dfu-suffix -p 16d0 -d 0fad -a {output_bit}")

    print(
    f"""DiVA build complete!  Output files:
    
    Bitstream file. (Compressed, Higher CLK)  Load this into FLASH.
        {builder.output_dir}/gateware/DiVA.bit
    
    Source Verilog file.  Useful for debugging issues.
        {builder.output_dir}/gateware/top.v
    """)



if __name__ == "__main__":
    main()

