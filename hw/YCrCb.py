#!/usr/bin/env python3
import sys
import os

from migen import *
from migen.genlib.cdc import MultiReg

from boson import *
from liteeth.common import *
from litex.soc.cores.clock import *

from pycrc.algorithms import Crc

from litex.soc.cores.uart import RS232PHYTX
from litex.soc.interconnect.stream import AsyncFIFO


def clamp(i):
    #return i[0:8]
    return Mux(i > 255, 255, Mux(i[31], 0, i[0:8]))

class YCrCbConvert(Module):
    def __init__(self):
        self.source = source = stream.Endpoint(EndpointDescription([("data", 24)]))
        self.sink = sink = stream.Endpoint(EndpointDescription([("data", 24)]))
        
        Cr = Signal((8,True))
        Cb = Signal((8,True))
        Y =  Signal((32,True))

        r = Signal((32,True))
        g = Signal((32,True))
        b = Signal((32,True))
        
        rgb = Signal(24)
        valid = Signal()

        self.comb += [
            Cr.eq(sink.data[16:24]-C(128,(8,True))),
            Cb.eq(sink.data[8:16]-C(128,(8,True))),
            Y.eq(sink.data[0:8] - C(0,(8,True))),

            r.eq(Y + Cr + (Cr >> 2) + (Cr >> 3) + (Cr >> 5)),
            g.eq(Y - ((Cb >> 2) + (Cb >> 4) + (Cb >> 5)) - ((Cr >> 1) + (Cr >> 3) + (Cr >> 4) + (Cr >> 5))),
            b.eq(Y + Cb + (Cb >> 1) + (Cb >> 2) + (Cb >> 6)),

            rgb[0:8].eq(clamp(r)),
            rgb[8:16].eq(clamp(g)),
            rgb[16:24].eq(clamp(b)),

            valid.eq(sink.valid),
            sink.ready.eq(source.ready)
        ]

        self.sync.boson_rx += [
            source.valid.eq(valid),
            source.data.eq(rgb)
        ]


        





     
        