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

from migen.genlib.resetsync import AsyncResetSynchronizer
from litex.build.generic_platform import *
from litex.soc.cores.clock import *
from rtl.ecp5_dynamic_pll import ECP5PLL, period_ns
from litex.soc.integration.soc_core import *
from litex.soc.integration.soc import SoC, SoCRegion
from litex.soc.integration.builder import *

from litex.soc.cores.bitbang import I2CMaster
from litex.soc.cores.gpio import GPIOOut, GPIOIn

from litex.soc.interconnect import stream, wishbone
from litex.soc.interconnect.wishbone import Interface, Crossbar
from litex.soc.interconnect.csr import *

from litex.soc.cores.led import LedChaser

from valentyusb.usbcore.io import IoBuf
from valentyusb.usbcore.cpu.eptri import TriEndpointInterface

from migen.genlib.misc import timeline
from migen.genlib.cdc import MultiReg, PulseSynchronizer

from rtl.prbs import PRBSStream
from rtl.edge_detect import EdgeDetect
from rtl.wb_streamer import StreamReader, StreamWriter, StreamBuffers
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

from rtl.cdc_csr import CSRClockDomainWrapper

from rtl.hdmi import HDMI
from rtl.video.ppu import VideoCore


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
        pll.create_clkout(self.cd_hr2x, sys_clk_freq * 2, margin=0)
        pll.create_clkout(self.cd_hr2x_90, sys_clk_freq * 2, phase=1, margin=0)  # SW tunes this phase during init

        self.comb += self.cd_init.clk.eq(clk48)

        pixel_clk = 74.25e6
        self.clock_domains.cd_usb_12 = ClockDomain()
        self.clock_domains.cd_usb_24 = ClockDomain()
        self.clock_domains.cd_usb_48 = ClockDomain()

        self.submodules.video_pll = video_pll = ECP5PLL()
        video_pll.register_clkin(self.cd_hr2x.clk, sys_clk_freq * 2)
        video_pll.create_clkout(self.cd_video, pixel_clk, margin=0)
        video_pll.create_clkout(self.cd_video_shift, pixel_clk * 5, margin=0)

        self.comb += self.cd_usb_48.clk.eq(clk48)
        self.specials += [
            AsyncResetSynchronizer(self.cd_usb_48, ~pll.locked),
            AsyncResetSynchronizer(self.cd_usb_24, ~pll.locked),
            AsyncResetSynchronizer(self.cd_usb_12, ~pll.locked),
        ]

        self.comb += self.cd_sys.clk.eq(self.cd_hr.clk)

        self.specials += [
            Instance("CLKDIVF",
                     p_DIV="2.0",
                     i_ALIGNWD=0,
                     i_CLKI=self.cd_usb_48.clk,
                     i_RST=~pll.locked,
                     o_CDIVX=self.cd_usb_24.clk),
            Instance("CLKDIVF",
                     p_DIV="2.0",
                     i_ALIGNWD=0,
                     i_CLKI=self.cd_usb_24.clk,
                     i_RST=~pll.locked,
                     o_CDIVX=self.cd_usb_12.clk),
        ]

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
                     p_DIV="2.0",
                     i_ALIGNWD=self._slip_hr2x.storage,
                     i_CLKI=self.cd_hr2x.clk,
                     i_RST=~pll.locked,
                     o_CDIVX=self.cd_hr.clk),
            Instance("CLKDIVF",
                     p_DIV="2.0",
                     i_ALIGNWD=self._slip_hr2x90.storage,
                     i_CLKI=self.cd_hr2x_90.clk,
                     i_RST=~pll.locked,
                     o_CDIVX=self.cd_hr_90.clk),
            AsyncResetSynchronizer(self.cd_hr2x, ~pll.locked),
            AsyncResetSynchronizer(self.cd_hr, ~pll.locked),
            AsyncResetSynchronizer(self.cd_sys, ~pll.locked),
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
        self.specials += Instance("OSCG", p_DIV=8, o_OSC=oscg_clk)
        self.comb += self.cd_oscg_38M.clk.eq(oscg_clk)


class DiVA_SoC(SoCCore):
    csr_map = {}
    csr_map.update(SoCCore.csr_map)

    mem_map = {
        **SoCCore.mem_map,
        **{
            "sram": 0x10000000,
            "csr": 0xf0000000,
            "vexriscv_debug": 0xf00f0000,
            "hyperram": 0x20000000,
            "spiflash": 0x30000000,
        },
    }

    interrupt_map = {}
    interrupt_map.update(SoCCore.interrupt_map)

    def __init__(self):

        self.platform = platform = bosonHDMI_r0d3.Platform()

        sys_clk_freq = 82.5e6
        SoCCore.__init__(
            self,
            platform,
            clk_freq=sys_clk_freq,
            cpu_type='vexriscv',
            cpu_variant='standard',
            with_uart=False,
            csr_data_width=32,
            ident_version=False,
            wishbone_timeout_cycles=128,
            integrated_sram_size=32 * 1024,
            cpu_reset_address=self.mem_map['sram'],
        )

        # Toolchain config
        platform.toolchain.build_template[0] = "yosys -q -l {build_name}.rpt {build_name}.ys"
        platform.toolchain.build_template[1] += f" --log {platform.name}.log --router router1"
        platform.toolchain.yosys_template[-1] += ' -abc2 '  # abc2/nowidelut generally give higher freq

        # crg -------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq)

        # Timers -----------------------------------------------------------------------------------
        self.add_timer(name="timer1")
        self.add_timer(name="timer2")

        # User inputs -----------------------------------------------------------------------------
        self.submodules.button = Button(platform.request("button"))

        # Leds -------------------------------------------------------------------------------------
        _led_pins = platform.request_all("user_led")
        led_pins = Signal(len(_led_pins))
        self.comb += _led_pins.eq(~led_pins)
        self.submodules.leds = LedChaser(pads=led_pins, sys_clk_freq=sys_clk_freq)

        # SPI Flash --------------------------------------------------------------------------------
        self.add_spi_flash(mode="4x", dummy_cycles=6)
        self.add_constant("SPIFLASH_PAGE_SIZE", 256)
        self.add_constant("SPIFLASH_SECTOR_SIZE", 4096)

        # HyperRAM with DMAs -----------------------------------------------------------------------
        self.submodules.writer = writer = StreamWriter()
        self.submodules.reader = reader = StreamReader()
        self.submodules.hyperram = hyperram = StreamableHyperRAM(platform.request("hyperRAM"), devices=[reader, writer])
        self.register_mem("hyperram", self.mem_map['hyperram'], hyperram.bus, size=0x800000)

        # Attach a StreamBuffer module to handle buffering of frames
        self.submodules.buffers = buffers = StreamBuffers()
        self.comb += [
            buffers.rx_release.eq(reader.evt_done),
            reader.start_address.eq(buffers.rx_buffer),
            writer.start_address.eq(buffers.tx_buffer),
        ]

        # PRBS Tester, used to test HyperRAM DMAs --------------------------------------------------
        self.submodules.prbs = PRBSStream()
        reader.add_source(self.prbs.source.source, "prbs")
        writer.add_sink(self.prbs.sink.sink, "prbs")

        self.submodules.scaler = scaler = ResetInserter(["video"])(ClockDomainsRenamer({
            "sys": "video",
            "cpu": "sys"
        })((Scaler())))

        # Pixel Processing Unit
        self.submodules.ppu = ppu = VideoCore()

        self.submodules.fifo = fifo = ClockDomainsRenamer({
            "read": "video",
            "write": "sys"
        })(stream.AsyncFIFO([('data', 24)], 1024))
        self.submodules.fifo1 = fifo1 = ResetInserter()(ClockDomainsRenamer({"sys": "video"
                                                                            })(stream.SyncFIFO([("data", 32)],
                                                                                               depth=32)))
        writer.add_sink(fifo.sink, "pixel_sink", ppu.next_frame)

        self.comb += [
            fifo.source.connect(scaler.sink),
            scaler.source.connect(fifo1.sink),
            fifo1.source.connect(ppu.pixel_sink),
        ]

        self.add_interrupt("ppu")
        #self.add_wb_master(ppu.bus)

        cpu_bus = Interface()
        self.add_memory_region("ppumem", 0x40000000, 0x2000000)
        self.add_wb_slave(0x40000000, cpu_bus)

        self.submodules.ppu_mem0 = wishbone.SRAM(0x2000)
        self.submodules.ppu_mem1 = wishbone.SRAM(0x2000)

        self.add_constant("PPUMEM0_BASE", 0x40000000)
        self.add_constant("PPUMEM0_SIZE", 0x1000)
        self.add_constant("PPUMEM1_BASE", 0x41000000)
        self.add_constant("PPUMEM1_SIZE", 0x1000)

        self.submodules += Crossbar(
            masters=[cpu_bus, ppu.bus],
            slaves=[
                (mem_decoder(0x40000000, size=0x2000), self.ppu_mem0.bus),
                (mem_decoder(0x41000000, size=0x2000), self.ppu_mem1.bus),
            ],
        )

        # DVI output, over HDMI connector ---------------------------------------------------------
        self.submodules.hdmi_i2c = I2CMaster(platform.request("hdmi_i2c"))
        self.submodules.hdmi = hdmi = HDMI(platform.request("hdmi"))
        self.comb += [
            ppu.source.connect(hdmi.sink, omit=['data']),
            hdmi.sink.r.eq(ppu.source.data[0:8]),
            hdmi.sink.g.eq(ppu.source.data[8:16]),
            hdmi.sink.b.eq(ppu.source.data[16:24]),
        ]

        # i2c0 -----------------------------------------------------------------------------------
        # Connected to I2C EEPROM used to store setting
        self.submodules.i2c0 = I2CMaster(platform.request("i2c"))

        # Reboot ---------------------------------------------------------------------------------
        self.submodules.reboot = Reboot(platform.request("rst_n"))

        # USB -------------------------------------------------------------------------------------
        usb_pads = platform.request("usb")

        # Select Boson as USB target
        if hasattr(usb_pads, "sw_sel"):
            self.comb += usb_pads.sw_sel.eq(1)

        # Enable USB
        if hasattr(usb_pads, "sw_oe"):
            self.comb += usb_pads.sw_oe.eq(0)

        # Attach USB to a seperate CSR bus that's decoupled from our CPU clock
        # This is a pretty ugly solution. It would be nice to be able to handle this in a neater fashion.
        usb_iobuf = IoBuf(usb_pads.d_p, usb_pads.d_n, usb_pads.pullup)
        self.submodules.usb = CSRClockDomainWrapper(usb_iobuf, platform)
        self.add_interrupt('usb')

        from litex.soc.integration.soc_core import SoCRegion
        self.bus.add_slave('usb', self.usb.bus, SoCRegion(origin=0xe0000000, size=0x1000, cached=False))

        # Add git version into firmware
        def get_git_revision():
            try:
                r = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                            stderr=subprocess.DEVNULL)[:-1].decode("utf-8")
            except:
                r = "--------"
            return r

        self.add_constant("DIVA_GIT_SHA1", get_git_revision())

    def finalize(self, *args, **kwargs):
        csrs = self.usb.get_csr()
        self.add_csr_region("usb", 0xe0000000, 32, csrs)

        return super().finalize(*args, **kwargs)

    def do_exit(self, vns):
        if hasattr(self, "analyzer"):
            self.analyzer.export_csv(vns, "test/analyzer.csv")

    def PackageFirmware(self, builder):
        # Remove un-needed sw packages
        builder.software_packages = []
        builder.add_software_package("libcompiler_rt")
        builder.add_software_package("libbase")

        builder.add_software_package("tinyusb", "{}/../firmware/tinyusb".format(os.getcwd()))
        builder.add_software_package("DiVA-fw", "{}/../firmware/DiVA-fw".format(os.getcwd()))

        builder._prepare_rom_software()
        builder._generate_includes()
        builder._generate_rom_software(compile_bios=False)

        # lock out compiling firmware during build steps
        builder.compile_software = False

    def PackageBooter(self, builder):
        self.finalize()

        os.makedirs(builder.output_dir, exist_ok=True)

        # Remove un-needed sw packages
        builder.software_packages = []
        builder.add_software_package("booter", "{}/../firmware/booter".format(os.getcwd()))

        builder._prepare_rom_software()
        builder._generate_includes()
        builder._generate_rom_software(compile_bios=False)


def CreateFirmwareInit(init, output_file):
    content = ""
    for d in init:
        content += "{:08x}\n".format(d)
    with open(output_file, "w") as o:
        o.write(content)


def main():
    parser = argparse.ArgumentParser(description="Build DiVA Gateware")
    parser.add_argument("--update-firmware",
                        default=False,
                        action='store_true',
                        help="compile firmware and update existing gateware")
    args = parser.parse_args()

    soc = DiVA_SoC()
    builder = Builder(soc, output_dir="build", csr_csv="build/csr.csv")

    # Check if we have the correct files
    firmware_file = os.path.join(builder.output_dir, "software", "DiVA-fw", "DiVA-fw.bin")

    rand_rom = os.path.join(builder.output_dir, "gateware", "rand.data")

    input_config = os.path.join(builder.output_dir, "gateware", f"{soc.platform.name}.config")

    # Create 256bytes rand fill for BRAM
    if (os.path.exists(rand_rom) == False) or (args.update_firmware == False):
        os.makedirs(os.path.join(builder.output_dir, 'software'), exist_ok=True)
        os.makedirs(os.path.join(builder.output_dir, 'gateware'), exist_ok=True)
        os.system(f"ecpbram  --generate {rand_rom} --seed {0} --width {32} --depth {2048 // 4}")

        # patch random file into BRAM
        data = []
        with open(rand_rom, 'r') as inp:
            for d in inp.readlines():
                data += [int(d, 16)]
        soc.sram.mem.init = data

        # Build gateware
        vns = builder.build(nowidelut=False)
        soc.do_exit(vns)

    # create a compressed bitstream
    output_bit = os.path.join(builder.output_dir, "gateware", "diva.bit")
    os.system(f"ecppack --freq 38.8 --compress --input {input_config} --bit {output_bit}")

    # Determine Bitstream size
    stage_1_filesize = os.path.getsize(output_bit)
    gateware_offset = 0x00040000
    firmware_offset = (stage_1_filesize + 0x200) & ~(0x100 - 1)  # Add some fudge factor.
    firmware_offset += gateware_offset  # bitstream offset
    print(f"Compressed file size: 0x{stage_1_filesize:0x}")
    print(f"Placing firmware at: 0x{firmware_offset:0x}")

    # Finalise the gateware aspects of the design.
    # Alter the spiflash origin so that our actual address is valid in the linker when compiling
    # Compile booter, it makes use of SPIFLASH_BASE for the boot address
    soc.finalize()
    soc.mem_regions['spiflash'].origin += firmware_offset
    soc.PackageBooter(builder)

    booter_file = "{}/software/booter/booter.bin".format(builder.output_dir)
    booter_init = "{}/software/booter/booter.init".format(builder.output_dir)
    CreateFirmwareInit(get_mem_data(booter_file, soc.cpu.endianness), booter_init)

    # Insert Firmware into Gateware
    os.system(f"ecpbram  --input {input_config} --output {input_config} --from {rand_rom} --to {booter_init}")

    # create a compressed bitstream
    output_dfu = os.path.join(builder.output_dir, "gateware", "diva.dfu")
    os.system(f"ecppack --freq 38.8 --compress --input {input_config} --bit {output_bit}")

    # Due to bitstream compression the final size might change when we patch in the booter firmware.
    stage_2_filesize = os.path.getsize(output_bit)
    assert firmware_offset > stage_2_filesize  # Sanity check that our bitstream didn't change too much.
    print(f"Compressed file size: 0x{stage_2_filesize:0x}")

    # Build firmware
    soc.PackageFirmware(builder)

    # Combine FLASH firmware
    from util.combine import CombineBinaryFiles
    flash_regions_final = {
        "build/gateware/diva.bit": gateware_offset,  # SoC ECP5 Bitstream
        "build/software/DiVA-fw/DiVA-fw.bin": firmware_offset,  # Circuit PYthon
    }
    CombineBinaryFiles(flash_regions_final, output_dfu)

    # Add DFU suffix
    os.system(f"dfu-suffix -p 16d0 -d 0fad -a {output_dfu}")

    print(f"""DiVA build complete!  
    
  DiVA.dfu size={os.path.getsize(output_dfu) / 1024 :.2f}KB ({os.path.getsize(output_dfu)} bytes) 
    FLASH Usage: {(float)(os.path.getsize(output_dfu)) / (((1024*1024) - gateware_offset)/100) :.2f} %
    
    
  Load using `dfu-util -D DiVA.dfu`
        {builder.output_dir}/gateware/DiVA.dfu
    """)


if __name__ == "__main__":
    main()
