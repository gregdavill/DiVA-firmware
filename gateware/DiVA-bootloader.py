#!/usr/bin/env python3
# This variable defines all the external programs that this module
# relies on.  lxbuildenv reads this variable in order to ensure
# the build will finish without exiting due to missing third-party
# programs.
LX_DEPENDENCIES = ["riscv", "icestorm", "yosys", "nextpnr-ice40"]

# Import lxbuildenv to integrate the deps/ directory
import lxbuildenv

# Disable pylint's E1101, which breaks completely on migen
#pylint:disable=E1101

#from migen import *
from migen import Module, Signal, Instance, ClockDomain, If
from migen.fhdl.specials import TSTriple
from migen.fhdl.decorators import ClockDomainsRenamer

from litex.build.lattice.platform import LatticePlatform
from litex.build.generic_platform import Pins, Subsignal
from litex.soc.integration.doc import AutoDoc, ModuleDoc
from litex.soc.integration.soc_core import SoCCore
from litex.soc.cores.cpu import CPUNone
from litex.soc.integration.builder import Builder
from litex.soc.interconnect import wishbone

from litex.soc.interconnect.wishbone import SRAM

from litex.soc.cores.clock import ECP5PLL
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.soc.cores import spi_flash

from valentyusb.usbcore import io as usbio
from valentyusb.usbcore.cpu import epmem, unififo, epfifo, dummyusb, eptri
from valentyusb.usbcore.endpoint import EndpointType


from rtl.button import Button
from rtl.pwmled import RGB
from rtl.ecpreboot import ECPReboot

import argparse
import os
import subprocess


from litex.build.generic_platform import *

_io = [
    ("clk48", 0,  Pins("M1"),  IOStandard("LVCMOS18")),
    ("rst_n", 0, Pins("V17"), IOStandard("LVCMOS33")),
    ("usr_btn", 0, Pins("F2"),IOStandard("LVCMOS18"), Misc("PULLMODE=UP")),

    ("rgb_led", 0,
        Subsignal("r", Pins("J17"), IOStandard("LVCMOS33")),
        Subsignal("g", Pins("J16"), IOStandard("LVCMOS33")),
        Subsignal("b", Pins("L16"), IOStandard("LVCMOS33")),
    ),

    ("usb", 0,
        Subsignal("d_p", Pins("G16")),
        Subsignal("d_n", Pins("K15")),
        Subsignal("pullup", Pins("H16")),
        Subsignal("sw_sel", Pins("F15")),
        IOStandard("LVCMOS33")
    ),

    ("spiflash4x", 0,
        Subsignal("cs_n", Pins("U17"), IOStandard("LVCMOS33")),
        Subsignal("dq",   Pins("U18 T18 R18 N18"), IOStandard("LVCMOS33")),
    ),
]


class _CRG(Module):
    def __init__(self, platform):
        clk48_raw = platform.request("clk48")

        reset_delay = Signal(64, reset=int(12e6*500e-6))
        self.clock_domains.cd_por = ClockDomain()
        self.reset = Signal()

        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_usb_12 = ClockDomain()
        self.clock_domains.cd_usb_48 = ClockDomain()

        platform.add_period_constraint(self.cd_usb_48.clk, 1e9/48e6)
        platform.add_period_constraint(self.cd_sys.clk, 1e9/12e6)
        platform.add_period_constraint(self.cd_usb_12.clk, 1e9/12e6)

        # POR reset logic- POR generated from sys clk, POR logic feeds sys clk
        # reset.
        self.comb += [
            self.cd_por.clk.eq(self.cd_usb_12.clk),
            self.cd_sys.rst.eq(reset_delay != 0),
            self.cd_usb_12.rst.eq(reset_delay != 0),
        ]

        # POR reset logic- POR generated from sys clk, POR logic feeds sys clk
        # reset.
        self.comb += [
            self.cd_usb_48.rst.eq(reset_delay != 0),
        ]

        self.submodules.pll = pll = ECP5PLL()
        pll.register_clkin(clk48_raw, 48e6)

        pll.create_clkout(self.cd_usb_48, 48e6, 0, with_reset=False)
        pll.create_clkout(self.cd_usb_12, 12e6, 0, with_reset=False)

        self.comb += self.cd_sys.clk.eq(self.cd_usb_12.clk)
        
        self.sync.por += \
            If(reset_delay != 0,
                reset_delay.eq(reset_delay - 1)
            )
        self.specials += AsyncResetSynchronizer(self.cd_por, self.reset)


class Platform(LatticePlatform):
    def __init__(self, device="25F", toolchain="trellis"):
        self.device = device
        self.hw_platform = "DiVA"
        
        LatticePlatform.__init__(self, "LFE5U-" + device + "-8MG285C", _io, [], toolchain=toolchain)

        self.name = 'diva_bootloader'

        self.spi_size = 1*1024*1024
        self.spi_dummy = 6

        self.revision = 'r0.3'


class BaseSoC(SoCCore, AutoDoc):
    """Fomu Bootloader and Base SoC

    Fomu is an FPGA that fits in your USB port.  This reference manual
    documents the basic SoC that runs the bootloader, and that can be
    reused to run your own RISC-V programs.

    This reference manual only describes a particular version of the SoC.
    The register sets described here are guaranteed to be available
    with a given ``major version``, but are not guaranteed to be available on
    any other version.  Naturally, you are free to create your own SoC
    that does not provide these hardware blocks. To see what the version of the
    bitstream you're running, check the ``VERSION`` registers.
    """

    csr_map = {
        "ctrl":           0,  # provided by default (optional)
        "crg":            1,  # user
        "uart_phy":       2,  # provided by default (optional)
        "uart":           3,  # provided by default (optional)
        "identifier_mem": 4,  # provided by default (optional)
        "timer0":         5,  # provided by default (optional)
        "cpu_or_bridge":  8,
        "usb":            9,
        "picorvspi":      10,
        "touch":          11,
        "reboot":         12,
        "rgb":            13,
        "version":        14,
        "lxspi":          15,
        "messible":       16,
        "button":         17,
    }

    SoCCore.mem_map = {
        "rom":              0x00000000,  # (default shadow @0x80000000)
        "sram":             0x10000000,  # (default shadow @0xa0000000)
        "spiflash":         0x20000000,  # (default shadow @0xa0000000)
        "main_ram":         0x40000000,  # (default shadow @0xc0000000)
        "csr":              0xe0000000,  # (default shadow @0xe0000000)
        "vexriscv_debug":   0xf00f0000,
    }

    interrupt_map = {
        "timer0": 2,
        "usb": 3,
    }
    interrupt_map.update(SoCCore.interrupt_map)

    
    
    def __init__(self, platform, boot_source="rand",
                 debug=None, bios_file=None,
                 use_dsp=False, placer="heap", output_dir="build",
                 pnr_seed=0,
                 **kwargs):
        # Disable integrated RAM as we'll add it later
        self.integrated_sram_size = 0

        self.output_dir = output_dir
        
        clk_freq = int(12e6)

        SoCCore.__init__(self, platform, clk_freq, cpu_variant='minimal', integrated_sram_size=8*1024, integrated_rom_size=8*1024, with_uart=False, csr_data_width=32, **kwargs)
        self.platform = platform

        self.submodules.crg = _CRG(platform)
        self.add_config("ECP5")
        self.add_config("QSPI_ENABLE")
        
        # The litex SPI module supports memory-mapped reads, as well as a bit-banged mode
        # for doing writes.
        spi_pads = platform.request("spiflash4x")
        self.submodules.lxspi = spi_flash.SpiFlashDualQuad(spi_pads, dummy=platform.spi_dummy, endianness="little")
        self.lxspi.add_clk_primitive(platform.device)
        self.register_mem("spiflash", self.mem_map["spiflash"], self.lxspi.bus, size=platform.spi_size)

        # Add USB pads, as well as the appropriate USB controller.  If no CPU is
        # present, use the DummyUsb controller.
        usb_pads = platform.request("usb")
        usb_iobuf = usbio.IoBuf(usb_pads.d_p, usb_pads.d_n, usb_pads.pullup)
        self.submodules.usb = eptri.TriEndpointInterface(usb_iobuf, debug=False)
        
        if hasattr(usb_pads, "sw_sel"):
            self.comb += usb_pads.sw_sel.eq(1)

        btn = platform.request("usr_btn")
        self.submodules.button = Button(btn)

        bootloader_size = 256*1024
        self.add_constant("FLASH_MAX_ADDR", value=platform.spi_size)

        self.submodules.reboot = ECPReboot(self)
        self.submodules.rgb = RGB(platform.request("rgb_led"))

        git_version_subprocess = subprocess.Popen("git describe --tags", shell=True, stdout=subprocess.PIPE)
        git_version = git_version_subprocess.stdout.read().decode("utf-8").strip()

        config = [
            ("USB_VENDOR_ID", 0x16d0),     # MCS Electronics
            ("USB_PRODUCT_ID", 0x0fad),    # Assigned to DiVA DFU
            ("USB_DEVICE_VER", 0x0101),    # Bootloader version
            ("USB_MANUFACTURER_NAME", "Get Labs"),
            ("USB_PRODUCT_NAME", "Boson DiVA r0.3 - DFU Bootloader {}".format(git_version))
        ]
        for (name,value) in config:
            self.add_constant("CONFIG_" + name, value)

def main():
    platform = Platform()

    output_dir = 'build'
    os.environ["LITEX"] = "1" # Give our Makefile something to look for

    soc = BaseSoC(platform)
    builder = Builder(soc)
    builder.software_packages = [
        ("bios", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "firmware", "bootloader-fw")))
    ]
    vns = builder.build()
    
    soc.do_exit(vns)

    # create a bitstream for loading into FLASH
    #input_config = os.path.join(output_dir, "gateware", "top.config")
    output_bitstream = os.path.join(builder.gateware_dir, f"{platform.name}.bit")
    input_config = os.path.join(builder.gateware_dir, f"{platform.name}.config")
        

    os.system(f"ecppack --freq 38.8 --compress --bootaddr 0x40000 --input {input_config} --bit {output_bitstream}")


    print(
    f"""Foboot build complete.
        File size: 0x{os.path.getsize(output_bitstream) :08X}
    """)


if __name__ == "__main__":
    main()
