#!/usr/bin/env python3

# This file is Copyright (c) 2020 Gregory Davill <greg.davill@gmail.com>
# License: BSD

import sys
import argparse
import optparse
import subprocess

from migen import *
import bosonHDMI_r0d2


from math import log2, ceil

import os
import shutil
from hdmi import HDMI
from terminal import Terminal



#from litex.soc.cores.uart import WishboneStreamingBridge
from litex.soc.cores.uart import Stream2Wishbone

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

from streamable_hyperram import StreamableHyperRAM

from wishbone_stream import StreamReader, StreamWriter, dummySink, dummySource

from boson import Boson
from YCrCb import YCrCbConvert

from sw_i2c import I2C

from litex.soc.interconnect import stream

from migen.genlib.misc import timeline


from sim import Platform

#from hyperRAM.hyperbus_fast import HyperRAM
#from dma.dma import StreamWriter, StreamReader, dummySink, dummySource

#from litex.soc.interconnect.stream import BufferizeEndpoints, DIR_SOURCE, PulseSynchronizer

from litex.soc.interconnect.csr import *

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
        
        #pixel_clock = (16e6)

        self.stop = Signal()

        # # #

        # clk / rst
        clk48 = platform.request("clk48")

        self.submodules.pll = pll = ECP5PLL()
        pll.register_clkin(clk48, 48e6)
        pll.create_clkout(self.cd_hr2x, sys_clk_freq*2, margin=0)
        pll.create_clkout(self.cd_hr2x_90, sys_clk_freq*2, phase=1, margin=0) # SW tunes this phase during init
        pll.create_clkout(self.cd_hr, sys_clk_freq, margin=0) # SW tunes this phase during init
        self.specials += [
            AsyncResetSynchronizer(self.cd_sys, ~pll.locked),
            AsyncResetSynchronizer(self.cd_init, ~pll.locked),
        ]

        self.comb += self.cd_sys.clk.eq(self.cd_hr.clk)
        self.comb += self.cd_init.clk.eq(clk48)

        pixel_clk = 40e6
        #pixel_clk = sys_clk_freq

        self.clock_domains.cd_usb_12 = ClockDomain()
        self.clock_domains.cd_usb_48 = ClockDomain()

        self.submodules.video_pll = video_pll = ECP5PLL()
        video_pll.register_clkin(clk48, 48e6)
        video_pll.create_clkout(self.cd_video,    pixel_clk,  margin=1e-2)
        video_pll.create_clkout(self.cd_usb_12,    12e6,  margin=0)
        video_pll.create_clkout(self.cd_video_shift,  pixel_clk*5, margin=1e-2)


        self.comb += self.cd_usb_48.clk.eq(clk48)


        platform.add_period_constraint(self.cd_usb_12.clk, period_ns(12e6))
        platform.add_period_constraint(self.cd_usb_48.clk, period_ns(48e6))
        platform.add_period_constraint(self.cd_sys.clk, period_ns(sys_clk_freq))
        platform.add_period_constraint(clk48, period_ns(48e6))
        platform.add_period_constraint(self.cd_video.clk, period_ns(pixel_clk))
        platform.add_period_constraint(self.cd_video_shift.clk, period_ns(pixel_clk * 5))

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
        "hyperram"   :  12,
        "terminal"   :  13,
        "analyzer"   :  14,
        "hdmi_i2c"   :  15,
        "i2c"        :  16,
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

    def __init__(self, sim=False):

        if sim:
            self.platform = platform = Platform()
        else:
            self.platform = platform = bosonHDMI_r0d2.Platform()
        
        sys_clk_freq = 82.5e6
        SoCCore.__init__(self, platform, clk_freq=sys_clk_freq,
                          cpu_type='serv', with_uart=True, uart_name='stream',
                          csr_data_width=32,
                          ident="HyperRAM Test SoC", ident_version=True, wishbone_timeout_cycles=64,
                          integrated_rom_size=16*1024)

        # Fake a UART stream, to enable easy firmware reuse.
        self.comb += self.uart.source.ready.eq(1)
    
        # crg
        if sim:
            clk = platform.request("clk")
            rst = platform.request("rst")
            self.clock_domains.cd_sys = ClockDomain()
            self.comb += self.cd_sys.clk.eq(clk)

            self.comb += self.cd_sys.rst.eq(rst)
            
        else:
            self.submodules.crg = _CRG(platform, sys_clk_freq)

        if not sim:
            self.submodules.rgb = RGB(platform.request("rgb_led"))
        
        # HyperRAM
        if sim:
            ...
            #self.submodules.hyperram = hyperram = wishbone.SRAM(0x8000)
            #self.register_mem("hyperram", self.mem_map['hyperram'], hyperram.bus, size=0x800000)

        else:
            self.submodules.hyperram = hyperram = StreamableHyperRAM(platform.request("hyperRAM"))
            self.register_mem("hyperram", self.mem_map['hyperram'], hyperram.bus, size=0x800000)

        #self.submodules.boson = Boson(platform, platform.request("boson"), sys_clk_freq)
        #self.submodules.YCrCb = ClockDomainsRenamer({"sys":"boson_rx"})(YCrCbConvert())

        ## HDMI output 
        if not sim:
            hdmi_pins = platform.request('hdmi')
            self.submodules.hdmi = hdmi =  HDMI(platform, hdmi_pins)
            self.submodules.hdmi_i2c = I2C(platform.request("hdmi_i2c"))


            # I2C
            self.submodules.i2c = I2C(platform.request("i2c"))

        ## Create VGA terminal
        if sim:
            self.submodules.terminal = terminal = ClockDomainsRenamer({'vga':'sys'})(Terminal(platform.request("video")))
        else:
            self.submodules.terminal = terminal = ClockDomainsRenamer({'vga':'video'})(Terminal())
        self.register_mem("terminal", self.mem_map["terminal"], terminal.bus, size=0x100000)


        #vsync_r = Signal()
        #self.sync.video += [
        #    vsync_r.eq(terminal.vsync)
        #]

        ## Connect VGA pins
        if not sim:
            self.comb += [
                hdmi.vsync.eq(terminal.vsync),
                hdmi.hsync.eq(terminal.hsync),
                hdmi.blank.eq(terminal.blank),
                hdmi.r.eq(terminal.red),
                hdmi.g.eq(terminal.green),
                hdmi.b.eq(terminal.blue),
            ]

        

        analyser = True
        if analyser and not sim:
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
            

            self.submodules.bridge = Stream2Wishbone(self.uart_usb, sys_clk_freq)
            self.add_wb_master(self.bridge.wishbone)

            #self.submodules.analyzer = LiteScopeAnalyzer(hyperram.dbg, 32)

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
    parser.add_argument(
        "--sim", default=False, action='store_true',
        help="simulate"
    )
    args = parser.parse_args()

    soc = DiVA_SoC(sim=args.sim)
    builder = Builder(soc, output_dir="build", csr_csv="build/csr.csv")

    # Build firmware
    soc.PackageFirmware(builder)
        

    if args.sim:
        ...
        builder.build(run=False)


    else:
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

