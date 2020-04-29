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

from wishbone_stream import StreamReader, StreamWriter

from boson import Boson

#from hyperRAM.hyperbus_fast import HyperRAM
#from dma.dma import StreamWriter, StreamReader, dummySink, dummySource

#from litex.soc.interconnect.stream import BufferizeEndpoints, DIR_SOURCE, PulseSynchronizer

from litex.soc.interconnect.csr import *

class _CRG(Module, AutoCSR):
    def __init__(self, platform, sys_clk_freq):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys_shift = ClockDomain()
        self.clock_domains.cd_shift = ClockDomain()
        self.clock_domains.cd_ram = ClockDomain()
        self.clock_domains.cd_ram_shift = ClockDomain()
        
        pixel_clock = (64e6)

        # # #

        # clk / rst
        clk48 = platform.request("clk48")

        self.submodules.pll = pll = ECP5PLL()
        pll.register_clkin(clk48, 48e6)
        pll.create_clkout(self.cd_sys, pixel_clock, margin=0)
        #pll.create_clkout(self.cd_sys_shift, pixel_clock, phase=1, margin=0)
        pll.create_clkout(self.cd_shift, pixel_clock * 5, margin=0)


        self.submodules.ram_pll = ram_pll = ECP5PLL()
        ram_pll.register_clkin(clk48, 48e6)
        ram_pll.create_clkout(self.cd_ram, 165e6, margin=0)
        ram_pll.create_clkout(self.cd_ram_shift, 165e6, phase=1, margin=0)

        self.specials += [
            AsyncResetSynchronizer(self.cd_sys, ~pll.locked),
            #AsyncResetSynchronizer(self.cd_sys_shift, ~pll.locked),
            AsyncResetSynchronizer(self.cd_shift, ~pll.locked)
        ]

        #platform.add_period_constraint(self.cd_sys.clk, period_ns(sys_clk_freq))
        #platform.add_period_constraint(self.cd_sys_shift.clk, period_ns(sys_clk_freq))

        self._phase_sel = CSRStorage(2)
        self._phase_dir = CSRStorage()
        self._phase_step = CSRStorage()
        self._phase_load = CSRStorage()

        self.comb += [
            self.ram_pll.phase_sel.eq(self._phase_sel.storage),
            self.ram_pll.phase_dir.eq(self._phase_dir.storage),
            self.ram_pll.phase_step.eq(self._phase_step.storage),
            self.ram_pll.phase_load.eq(self._phase_load.storage),
        ]


class DiVA_SoC(SoCCore):
    csr_map = {
        "rgb"        :  10, 
        "crg"        :  11, 
        "test"       :  12,
        "terminal"   :  13,
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
        
        sys_clk_freq = int(75e6)
        SoCCore.__init__(self, platform, clk_freq=sys_clk_freq,
                          cpu_type='serv', with_uart=True, uart_name='stub',
                          csr_data_width=32,
                          ident="HyperRAM Test SoC", ident_version=True, wishbone_timeout_cycles=128,
                          integrated_rom_size=16*1024)
    
        # crg
        self.submodules.crg = _CRG(platform, sys_clk_freq)

        self.submodules.rgb = RGB(platform.request("rgb_led"))
        
        # HyperRAM
#        hyperram = ClockDomainsRenamer({'sys':'ram', 'sys_shift':'ram_shift'})(HyperRAM(platform.request("hyperRAM")))
#        self.submodules += hyperram
        

        self.submodules.test = StreamableHyperRAM(platform.request("hyperRAM"))

        self.submodules.boson = Boson(platform, platform.request("boson"))

        #self.add_wb_slave(self.mem_map["hyperram"], hyperram.bus)
        #self.add_memory_region("hyperram", self.mem_map["hyperram"], 0x800000)


        ## HDMI output 
        hdmi_pins = platform.request('hdmi')
        self.submodules.hdmi = hdmi =  HDMI(platform, hdmi_pins)

        ## Create VGA terminal
        #mem_map["terminal"] = 0x30000000
        self.submodules.terminal = terminal = ClockDomainsRenamer({'vga':'sys'})(Terminal())
        self.register_mem("terminal", self.mem_map["terminal"], terminal.bus, size=0x100000)
        #self.add_memory_region("terminal", 0x30000000, 0x100000)

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

            self.test.pixels.connect(terminal.source),
            self.test.pixels_reset.eq(vsync_r & ~terminal.vsync),

            self.boson.source.connect(self.test.boson)
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

