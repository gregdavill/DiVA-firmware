# This file is Copyright (c) 2020 Gregory Davill <greg.davill@gmail.com>
# License: BSD

import os

from migen import *

from litex.soc.interconnect.stream import Endpoint, EndpointDescription, SyncFIFO, AsyncFIFO
from litex.soc.interconnect.csr import AutoCSR, CSR, CSRStatus, CSRStorage

from litex.soc.cores.freqmeter import FreqMeter
from rtl.edge_detect import EdgeDetect


from migen.genlib.cdc import MultiReg, PulseSynchronizer

class VideoDebug(Module, AutoCSR):
    def __init__(self, clk_freq):
        
        # VGA input
        self.red   = red   = Signal(8)
        self.green = green = Signal(8)
        self.blue  = blue  = Signal(8)
        self.hsync = hsync = Signal()
        self.vsync = vsync = Signal()
        self.data_valid = data_valid = Signal()


        self.submodules.freq = FreqMeter(period=clk_freq, clk=ClockSignal("pixel"))

        self.submodules.v_edge = v_edge = EdgeDetect(mode="change", input_cd="pixel", output_cd="pixel")
        self.submodules.h_edge = h_edge = EdgeDetect(mode="change", input_cd="pixel", output_cd="pixel")

        vsync_low = Signal(24)
        vsync_high = Signal(24)
        vsync_counter = Signal(24)

        hsync_low = Signal(24)
        hsync_high = Signal(24)
        hsync_counter = Signal(24)

        lines = Signal(16)
        lines_counter = Signal(16)

        self.comb += v_edge.i.eq(vsync)
        self.comb += h_edge.i.eq(hsync)
        self.sync.pixel += [
            vsync_counter.eq(vsync_counter + 1),
            hsync_counter.eq(hsync_counter + 1),
            If(h_edge.o,
                If(hsync,
                    hsync_low.eq(hsync_counter)
                ).Else(
                    hsync_high.eq(hsync_counter),
                    lines_counter.eq(lines_counter + 1)
                ),
                hsync_counter.eq(1)
            ),
            If(v_edge.o,
                If(vsync,
                    vsync_low.eq(vsync_counter)
                ).Else(
                    vsync_high.eq(vsync_counter),
                    lines.eq(lines_counter),
                    lines_counter.eq(1),
                ),
                vsync_counter.eq(1)
            ),

        ]

        # CSRs
        self.latch = CSR()
        self.vsync_low = CSRStatus(24)
        self.vsync_high = CSRStatus(24)
        self.hsync_low = CSRStatus(24)
        self.hsync_high = CSRStatus(24)
        self.lines = CSRStatus(16)

        # output values to CSR

        latch = Signal()
        latch_ps = PulseSynchronizer("sys", "pixel")
        self.submodules += latch_ps
        self.comb += latch_ps.i.eq(self.latch.re)

        _vsync_low = Signal(24)
        _vsync_high = Signal(24)
        _hsync_low = Signal(24)
        _hsync_high = Signal(24)
        _lines = Signal(16)
        
        self.sync.pixel += [
            If(latch_ps.o,
                _vsync_low.eq(vsync_low),
                _vsync_high.eq(vsync_high),
                _hsync_low.eq(hsync_low),
                _hsync_high.eq(hsync_high),
                _lines.eq(lines),
            )
        ]
        self.specials += MultiReg(_vsync_low, self.vsync_low.status)
        self.specials += MultiReg(_vsync_high, self.vsync_high.status)
        self.specials += MultiReg(_hsync_low, self.hsync_low.status)
        self.specials += MultiReg(_hsync_high, self.hsync_high.status)
        self.specials += MultiReg(_lines, self.lines.status)



