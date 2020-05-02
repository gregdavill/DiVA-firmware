
from migen import *

from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.soc.cores.clock import *

import os, shutil

from hyperram import HyperRAM


from migen import Module, Signal, ClockDomain
from migen.fhdl.structure import ResetSignal

from litex.build.sim.platform import SimPlatform
from litex.build.generic_platform import Pins, Subsignal
from litex.soc.integration.soc_core import SoCCore
from litex.soc.integration.builder import Builder


_io = [
    # Wishbone
    ("wishbone", 0, Subsignal("adr", Pins(30)), Subsignal("dat_r", Pins(32)), 
     Subsignal("dat_w", Pins(32)), Subsignal("sel", Pins(4)), Subsignal("cyc", Pins(1)),
     Subsignal("stb", Pins(1)), Subsignal("ack", Pins(1)), Subsignal("we", Pins(1)),
     Subsignal("cti", Pins(3)), Subsignal("bte", Pins(2)), Subsignal("err", Pins(1))),
    ("hyperRAM", 0,
    Subsignal("rst_n", Pins(1)),
    Subsignal("clk_p", Pins(1)),
    Subsignal("clk_n", Pins(1)),
    Subsignal("cs_n",  Pins(1)),
    Subsignal("dq",    Pins(8)),
    Subsignal("rwds",  Pins(1)),
    Subsignal("dbg0",  Pins(1)),
    Subsignal("dbg1",  Pins(1)),
    ),

    ("clock_2x_in", 0, Pins(1)),
    ("clock_2x_in_90", 0, Pins(1)),
    ("clock", 0, Pins(1)),
    ("reset", 0, Pins(1)),
    
]

_connectors = []



class Platform(SimPlatform):
    def __init__(self, toolchain="verilator"):
        SimPlatform.__init__(self,
                             "sim",
                             _io,
                             _connectors,
                             toolchain="verilator")

    def create_programmer(self):
        raise ValueError("programming is not supported")


class HyperRAMTest(Module):
    def __init__(self, platform):
        
        reset = platform.request("reset")


        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_hr2x = ClockDomain()
        self.clock_domains.cd_hr2x_90 = ClockDomain()
        self.clock_domains.cd_hr = ClockDomain()

        clk_hr = Signal()
        self.comb += self.cd_hr2x.clk.eq(platform.request("clock_2x_in"))
        self.comb += self.cd_hr2x_90.clk.eq(platform.request("clock_2x_in_90"))

        self.sync.hr2x += clk_hr.eq(~clk_hr)

        self.comb += self.cd_sys.clk.eq(clk_hr)
        self.comb += self.cd_hr.clk.eq(clk_hr)

        self.comb += platform.request("clock").eq(clk_hr)
        self.comb += self.cd_hr2x.rst.eq(reset)
        


        hr = HyperRAM(platform.request("hyperRAM"))
        self.submodules += hr

        self.comb += hr.bus.connect_to_pads(platform.request("wishbone"), mode="slave")


if __name__ == "__main__":
    import sys

    platform = Platform()
    design = HyperRAMTest(platform)


#         add_fsm_state_names()
    platform.build(design, build_dir='build', run=False)

    #os.system('iverilog hyperram_tb.v build_test/top.v -o build_lcd/a.out')
    #cwd = os.getcwd()
    #os.chdir('build_test')

#    os.system('vvp a.out')

 #   os.chdir(cwd)
