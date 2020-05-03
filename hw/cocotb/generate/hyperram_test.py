
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



def add_fsm_state_names():
    """Hack the FSM module to add state names to the output"""
    from migen.fhdl.visit import NodeTransformer
    from migen.genlib.fsm import NextState, NextValue, _target_eq
    from migen.fhdl.bitcontainer import value_bits_sign

    class My_LowerNext(NodeTransformer):
        def __init__(self, next_state_signal, next_state_name_signal, encoding,
                     aliases):
            self.next_state_signal = next_state_signal
            self.next_state_name_signal = next_state_name_signal
            self.encoding = encoding
            self.aliases = aliases
            # (target, next_value_ce, next_value)
            self.registers = []

        def _get_register_control(self, target):
            for x in self.registers:
                if _target_eq(target, x[0]):
                    return x[1], x[2]
            raise KeyError

        def visit_unknown(self, node):
            if isinstance(node, NextState):
                try:
                    actual_state = self.aliases[node.state]
                except KeyError:
                    actual_state = node.state
                return [
                    self.next_state_signal.eq(self.encoding[actual_state]),
                    self.next_state_name_signal.eq(
                        int.from_bytes(actual_state.encode(), byteorder="big"))
                ]
            elif isinstance(node, NextValue):
                try:
                    next_value_ce, next_value = self._get_register_control(
                        node.target)
                except KeyError:
                    related = node.target if isinstance(node.target,
                                                        Signal) else None
                    next_value = Signal(bits_sign=value_bits_sign(node.target),
                                        related=related)
                    next_value_ce = Signal(related=related)
                    self.registers.append(
                        (node.target, next_value_ce, next_value))
                return next_value.eq(node.value), next_value_ce.eq(1)
            else:
                return node

    import migen.genlib.fsm as fsm

    def my_lower_controls(self):
        self.state_name = Signal(len(max(self.encoding, key=len)) * 8,
                                 reset=int.from_bytes(
                                     self.reset_state.encode(),
                                     byteorder="big"))
        self.next_state_name = Signal(len(max(self.encoding, key=len)) * 8,
                                      reset=int.from_bytes(
                                          self.reset_state.encode(),
                                          byteorder="big"))
        self.comb += self.next_state_name.eq(self.state_name)
        self.sync += self.state_name.eq(self.next_state_name)
        return My_LowerNext(self.next_state, self.next_state_name,
                            self.encoding, self.state_aliases)

    fsm.FSM._lower_controls = my_lower_controls


if __name__ == "__main__":
    import sys

    platform = Platform()
    design = HyperRAMTest(platform)


    add_fsm_state_names()
    platform.build(design, build_dir='build', run=False)

    #os.system('iverilog hyperram_tb.v build_test/top.v -o build_lcd/a.out')
    #cwd = os.getcwd()
    #os.chdir('build_test')

#    os.system('vvp a.out')

 #   os.chdir(cwd)
