# This file is Copyright (c) 2018 Dolu1990 <charles.papon.90@gmail.com>
# This file is Copyright (c) 2018-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# This file is Copyright (c) 2018-2019 Sean Cross <sean@xobs.io>
# This file is Copyright (c) 2019 Tim 'mithro' Ansell <me@mith.ro>
# This file is Copyright (c) 2019 David Shah <dave@ds0.me>
# This file is Copyright (c) 2019 Antmicro <www.antmicro.com>
# This file is Copyright (c) 2019 Kurt Kiefer <kekiefer@gmail.com>

# License: BSD

import os

from migen import *

from litex.soc.interconnect import wishbone
from litex.soc.interconnect.csr import *
from litex.soc.cores.cpu import CPU


CPU_VARIANTS = {
    "minimal":          "VexRiscv_Min",
    "minimal+debug":    "VexRiscv_MinDebug",
    "lite":             "VexRiscv_Lite",
    "lite+debug":       "VexRiscv_LiteDebug",
    "standard":         "VexRiscv",
    "standard+debug":   "VexRiscv_Debug",
    "full":             "VexRiscv_Full",
    "full+debug":       "VexRiscv_FullDebug",
    "linux":            "VexRiscv_Linux",
    "linux+debug":      "VexRiscv_LinuxDebug",
    "linux+no-dsp":     "VexRiscv_LinuxNoDspFmax",
}


GCC_FLAGS = {
    #                               /-------- Base ISA
    #                               |/------- Hardware Multiply + Divide
    #                               ||/----- Atomics
    #                               |||/---- Compressed ISA
    #                               ||||/--- Single-Precision Floating-Point
    #                               |||||/-- Double-Precision Floating-Point
    #                               imacfd
    "minimal":          "-march=rv32i      -mabi=ilp32",
    "minimal+debug":    "-march=rv32i      -mabi=ilp32",
    "lite":             "-march=rv32i      -mabi=ilp32",
    "lite+debug":       "-march=rv32i      -mabi=ilp32",
    "standard":         "-march=rv32i      -mabi=ilp32",
    "standard+debug":   "-march=rv32i      -mabi=ilp32",
    "full":             "-march=rv32i     -mabi=ilp32",
    "full+debug":       "-march=rv32i     -mabi=ilp32",
    "linux":            "-march=rv32i    -mabi=ilp32",
    "linux+debug":      "-march=rv32i    -mabi=ilp32",
    "linux+no-dsp":     "-march=rv32i    -mabi=ilp32",
}


class VexRiscvTimer(Module, AutoCSR):
    def __init__(self):
        self._latch    = CSR()
        self._time     = CSRStatus(64)
        self._time_cmp = CSRStorage(64, reset=2**64-1)
        self.interrupt = Signal()

        # # #

        time = Signal(64)
        self.sync += time.eq(time + 1)
        self.sync += If(self._latch.re, self._time.status.eq(time))

        time_cmp = Signal(64, reset=2**64-1)
        self.sync += If(self._latch.re, time_cmp.eq(self._time_cmp.storage))

        self.comb += self.interrupt.eq(time >= time_cmp)


class serv(CPU, AutoCSR):
    name                 = "vexriscv"
    data_width           = 32
    endianness           = "little"
    gcc_triple           = ("riscv64-unknown-elf", "riscv32-unknown-elf", "riscv-none-embed",
                            "riscv64-linux", "riscv-sifive-elf", "riscv64-none-elf")
    linker_output_format = "elf32-littleriscv"
    io_regions           = {0x80000000: 0x80000000} # origin, length

    @property
    def mem_map_linux(self):
        return {
            "rom":          0x00000000,
            "sram":         0x10000000,
            "main_ram":     0x40000000,
            "csr":          0xf0000000,
        }

    @property
    def gcc_flags(self):
        flags = GCC_FLAGS[self.variant]
        flags += " -D__vexriscv__"
        return flags

    def __init__(self, platform, variant="standard"):
        #assert variant in CPU_VARIANTS, "Unsupported variant %s" % variant
        self.platform         = platform
        self.variant          = variant
        self.external_variant = None
        self.reset            = Signal()
        self.ibus             = ibus = wishbone.Interface()
        self.dbus             = dbus = wishbone.Interface()
        self.buses            = [ibus, dbus]
        self.interrupt        = Signal(32)

        i_addr = Signal(32)
        d_addr = Signal(32)

        self.comb += [
            ibus.sel.eq(0xF),
            ibus.stb.eq(ibus.cyc),
            dbus.stb.eq(dbus.cyc),
            ibus.adr.eq(i_addr[2:]),
            dbus.adr.eq(d_addr[2:]),
            
        ]

        self.cpu_params = dict(
                i_clk=ClockSignal(),
                i_i_rst=ResetSignal() | self.reset,
                i_i_timer_irq     = 0,

                o_o_ibus_adr      = i_addr,
                o_o_ibus_cyc      = ibus.cyc,
                i_i_ibus_rdt      = ibus.dat_r,
                i_i_ibus_ack      = ibus.ack,
                
                o_o_dbus_adr      = d_addr,
                o_o_dbus_dat      = dbus.dat_w,
                o_o_dbus_sel      = dbus.sel,
                o_o_dbus_we       = dbus.we,
                o_o_dbus_cyc      = dbus.cyc,
                i_i_dbus_rdt      = dbus.dat_r,
                i_i_dbus_ack      = dbus.ack,
            )

        if "linux" in variant:
            self.add_timer()
            self.mem_map = self.mem_map_linux

        if "debug" in variant:
            self.add_debug()

   
    def set_reset_address(self, reset_address):
        assert not hasattr(self, "reset_address")
        self.reset_address = reset_address
        #self.cpu_params.update(i_externalResetVector=Signal(32, reset=reset_address))

    def add_timer(self):
        self.submodules.timer = VexRiscvTimer()
        #self.cpu_params.update(i_timerInterrupt=self.timer.interrupt)

    @staticmethod
    def add_sources(platform, variant="standard"):
        vdir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "deps","serv","rtl")
        platform.add_source_dir(vdir)
        platform.add_verilog_include_path(vdir)


    def do_finalize(self):
        assert hasattr(self, "reset_address")
        #self.cpu_params.update(p_RF_WIDTH=32)
        self.specials += Instance("serv_rf_top", **self.cpu_params)
