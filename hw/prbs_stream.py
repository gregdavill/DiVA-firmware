# This file is Copyright (c) 2020 Gregory Davill <greg.davill@gmail.com>
# License: BSD

import unittest

from migen import *

from litex.soc.interconnect import wishbone
from litex.soc.interconnect.stream import EndpointDescription, Endpoint
from litex.soc.interconnect import stream_sim

from litex.soc.interconnect.csr import *

from litex.soc.cores.prbs import PRBS31Generator

def data_stream_description(dw):
    payload_layout = [("data", dw)]
    return EndpointDescription(payload_layout)

class prbsSource(Module, AutoCSR):
    def __init__(self):
        self.source = source = Endpoint(data_stream_description(32))
        
        self.submodules.prbs = prbs = ResetInserter()(CEInserter()(PRBS31Generator(32)))
        self.reset = CSR(1)

        self.comb += [
            source.valid.eq(1),
            source.data.eq(prbs.o),
            prbs.ce.eq(source.ready),
            prbs.reset.eq(self.reset.re)
        ]


class prbsSink(Module, AutoCSR):
    def __init__(self):
        self.sink = sink = Endpoint(data_stream_description(32))
        

        self.submodules.prbs = prbs = ResetInserter()(CEInserter()(PRBS31Generator(32)))
        
        good = Signal(32)
        bad = Signal(32)

        self.reset = CSR(1)
        self.good = CSRStatus(32)
        self.bad = CSRStatus(32)
        

        self.sync += [
            If(self.reset.re,
                good.eq(0),
                bad.eq(0),
            ),
            If(sink.valid,
                If(prbs.o == sink.data,
                    good.eq(good + 1)
                ).Else(
                    bad.eq(bad + 1)
                ),
            ),
        ]

        self.comb += [
            sink.ready.eq(1),
            self.good.status.eq(good),
            self.bad.status.eq(bad),


            prbs.ce.eq(sink.valid),
            prbs.reset.eq(self.reset.re)
        ]
