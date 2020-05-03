#!/usr/bin/env python3
import sys
import argparse
import optparse
import subprocess

from migen import *
import orangecrab


from math import log2, ceil

import os
import shutil
from hdmi import HDMI
from terminal import Terminal



from litex.soc.cores.uart import WishboneStreamingBridge

from litescope import LiteScopeAnalyzer

#from file_helper import package_file

#from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.build.generic_platform import *
from litex.boards.platforms import versa_ecp5

from litex.soc.cores.clock import *
from ecp5_dynamic_pll import ECP5PLL, period_ns
from litex.soc.integration.soc_core import *
from litex.soc.integration.soc import SoCRegion
from litex.soc.integration.builder import *


from litex.soc.interconnect import wishbone

from litex.soc.cores.gpio import GPIOOut
from rgb_led import RGB
from hyperram import HyperRAM

from streamable_hyperram import StreamableHyperRAM

from wishbone_stream import StreamReader, StreamWriter, dummySink, dummySource

from boson import Boson
from YCrCb import YCrCbConvert


from litex.soc.interconnect import stream

from migen.genlib.misc import timeline

#from hyperRAM.hyperbus_fast import HyperRAM
#from dma.dma import StreamWriter, StreamReader, dummySink, dummySource

#from litex.soc.interconnect.stream import BufferizeEndpoints, DIR_SOURCE, PulseSynchronizer

from litex.soc.interconnect.csr import *

class hr_io_tunner(Module, AutoCSR):
    def __init__(self):
        self.loadn = CSRStorage()
        self.move = CSRStorage()
        self.direction = CSRStorage()

class _CRG(Module, AutoCSR):
    def __init__(self, platform, sys_clk_freq):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_video = ClockDomain()
        self.clock_domains.cd_video_shift = ClockDomain()

        self.clock_domains.cd_hr = ClockDomain()
        self.clock_domains.cd_hr2x = ClockDomain()
        self.clock_domains.cd_hr2x_90 = ClockDomain()
        self.clock_domains.cd_hr2x_ = ClockDomain()
        self.clock_domains.cd_hr2x_90_ = ClockDomain()

        self.clock_domains.cd_init = ClockDomain()
        
        #pixel_clock = (16e6)

        self.stop = Signal()

        # # #

        # clk / rst
        clk48 = platform.request("clk48")

        self.submodules.pll = pll = ECP5PLL()
        pll.register_clkin(clk48, 48e6)
        pll.create_clkout(self.cd_hr2x_, sys_clk_freq*2, margin=0)
        pll.create_clkout(self.cd_hr2x_90_, sys_clk_freq*2, phase=1, margin=0) # SW tunes this phase during init
        self.specials += [
            AsyncResetSynchronizer(self.cd_sys, ~pll.locked)
        ]

        self.comb += self.cd_sys.clk.eq(self.cd_hr.clk)
        self.comb += self.cd_init.clk.eq(clk48)

        pixel_clk = 75e6

        self.submodules.video_pll = video_pll = ECP5PLL()
        video_pll.register_clkin(clk48, 48e6)
        video_pll.create_clkout(self.cd_video,    pixel_clk,  margin=0)
        video_pll.create_clkout(self.cd_video_shift,  pixel_clk*5, margin=0)

        stop = Signal()
        reset = Signal()

        # ECLK initialization sequence ---------------------------------------------
        t = 8 # in cycles
        self.sync.init += [
            # Wait DDRDLLA Lock
            timeline(ResetSignal("init"), [
                (1*t,  []), # Freeze DDRDLLA
                (2*t,  [stop.eq(1)]),   # Stop ECLK domain
                (3*t,  [reset.eq(1)]),  # Reset ECLK domain
                (4*t,  [reset.eq(0)]),  # Release ECLK domain reset
                (5*t,  [stop.eq(0)]),   # Release ECLK domain stop
            ])
        ]

        # ------------------------------------------------------------------------------------------
        self.comb += [
            ResetSignal("hr2x").eq(reset),
            ResetSignal("hr2x_90").eq(reset)
        ]

        # ECLK stuff 
        self.specials += [
            Instance("ECLKSYNCB",
                i_ECLKI = self.cd_hr2x_.clk,
                i_STOP  = self.stop,
                o_ECLKO = self.cd_hr2x.clk),
            Instance("ECLKSYNCB",
                i_ECLKI = self.cd_hr2x_90_.clk,
                i_STOP  = self.stop,
                o_ECLKO = self.cd_hr2x_90.clk),
            Instance("CLKDIVF",
                p_DIV     = "2.0",
                i_ALIGNWD = 0,
                i_CLKI    = self.cd_hr2x.clk,
                i_RST     = self.cd_hr2x.rst,
                o_CDIVX   = self.cd_hr.clk),
            AsyncResetSynchronizer(self.cd_hr, ~pll.locked)
        ]

        #platform.add_period_constraint(self.cd_sys.clk, period_ns(sys_clk_freq))
        #platform.add_period_constraint(self.cd_sys_shift.clk, period_ns(sys_clk_freq))

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


       

class DiVA_SoC(SoCCore):
    csr_map = {
        "rgb"        :  10, 
        "crg"        :  11, 
        "test"       :  12,
        "terminal"   :  13,
        "analyzer"   :  14,
        "reader"   :  16,
        "writer"   :  17,
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

        self.platform = platform = orangecrab.Platform()
        
        sys_clk_freq = int(82.5e6)
        SoCCore.__init__(self, platform, clk_freq=sys_clk_freq,
                          cpu_type='serv', with_uart=True, uart_name='stub',
                          csr_data_width=32,
                          ident="HyperRAM Test SoC", ident_version=True, wishbone_timeout_cycles=128,
                          integrated_rom_size=16*1024)
    
        # crg
        self.submodules.crg = _CRG(platform, sys_clk_freq)

        self.submodules.rgb = RGB(platform.request("rgb_led"))
        
        # HyperRAM
        hyperram = HyperRAM(platform.request("hyperRAM"))
        self.submodules += hyperram
        self.add_wb_slave(self.mem_map["hyperram"], hyperram.bus)
        self.add_memory_region("hyperram", self.mem_map["hyperram"], 0x800000)
        
        self.submodules.test = hr_io_tunner()

        self.comb += [
            hyperram.loadn.eq(self.test.loadn.storage),
            hyperram.move.eq(self.test.move.storage),
            hyperram.direction.eq(self.test.direction.storage),
        ]


        self.submodules.writer = writer = StreamWriter()
        self.submodules.reader = reader = StreamReader()

        self.submodules.d_sink = dSink = dummySink()
        self.submodules.d_source = dSource = dummySource()

        self.add_wb_master(writer.bus)
        self.add_wb_master(reader.bus)

        self.comb += [
            writer.source.connect(dSink.sink),
            dSource.source.connect(reader.sink)
            
        ]
        

        #self.submodules.test = StreamableHyperRAM(platform.request("hyperRAM"))

        #self.submodules.boson = Boson(platform, platform.request("boson"))
        #self.submodules.YCrCb = ClockDomainsRenamer({"sys":"boson_rx"})(YCrCbConvert())



        ## HDMI output 
        hdmi_pins = platform.request('hdmi')
        self.submodules.hdmi = hdmi =  HDMI(platform, hdmi_pins)

        ## Create VGA terminal
        self.submodules.terminal = terminal = ClockDomainsRenamer({'vga':'video'})(Terminal())
        self.register_mem("terminal", self.mem_map["terminal"], terminal.bus, size=0x100000)


        vsync_r = Signal()
        self.sync += [
            vsync_r.eq(terminal.vsync)
        ]

        ## Connect VGA pins
        self.comb += [
            hdmi.vsync.eq(terminal.vsync),
            hdmi.hsync.eq(terminal.hsync),
            hdmi.blank.eq(terminal.blank),
            hdmi.r.eq(terminal.red),
            hdmi.g.eq(terminal.green),
            hdmi.b.eq(terminal.blue),

            #self.test.pixels.connect(terminal.source),
            #self.test.pixels_reset.eq(vsync_r & ~terminal.vsync),

            #self.boson.source.connect(self.YCrCb.sink),
            #self.YCrCb.source.connect(self.test.boson),
            #self.test.boson_sync.eq(self.boson.sync_out)
        ]

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

        src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sw", "DiVA-fw"))
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

    input_config = os.path.join(builder.output_dir, "gateware", "top.config")
    output_config = os.path.join(builder.output_dir, "gateware", "top_patched.config")
    
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
        vns = builder.build()
        soc.do_exit(vns)    


    # Insert Firmware into Gateware
    os.system(f"ecpbram  --input {input_config} --output {output_config} --from {rand_rom} --to {firmware_init}")

    # create a compressed bitstream
    output_bit = os.path.join(builder.output_dir, "gateware", "DiVA.bit")
    os.system(f"ecppack --input {output_config} --compress --freq 38.8 --bit {output_bit}")

    # Add DFU suffix
    os.system(f"dfu-suffix -p 1209 -d 5bf0 -a {output_bit}")

    print(
    f"""DiVA build complete!  Output files:
    
    Bitstream file. (Compressed, Higher CLK)  Load this into FLASH.
        {builder.output_dir}/gateware/DiVA.bit
    
    Source Verilog file.  Useful for debugging issues.
        {builder.output_dir}/gateware/top.v
    """)



if __name__ == "__main__":
    main()

