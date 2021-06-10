# This file is Copyright (c) 2020 Gregory Davill <greg.davill@gmail.com>
# License: BSD

from migen import *
from litex.soc.interconnect.stream import Endpoint

from litex.soc.interconnect.csr import AutoCSR, CSRStorage
from litex.soc.interconnect.stream import Endpoint

from litex.soc.interconnect.stream import *

@ResetInserter()
class StreamPrepend(Module, AutoCSR):
    def __init__(self):
        self.sink = sink = Endpoint([("data", 32)])
        self.source = source = Endpoint([("data", 32)])

        self.length = CSRStorage(8)
        delay_count = Signal(8)


        _valid = Signal()
        self.sync += _valid.eq(sink.valid)

        self.submodules.fsm = fsm = FSM(reset_state='PASS')

        fsm.act('PASS', 
            sink.connect(source),
            If(~sink.valid,
                If(self.length.storage > 0,
                    NextState('DELAY'),
                    NextValue(delay_count, self.length.storage)
                )
            )
        )

        fsm.act('DELAY', 
            sink.connect(source, omit=['first','ready']),
            If(delay_count == 0,
                NextState('PASS'),
            ).Elif(sink.valid & source.ready,
                NextValue(delay_count, delay_count - 1),
            ),
        )



@ResetInserter()
class StreamAppend(Module, AutoCSR):
    def __init__(self):
        self.sink = sink = Endpoint([("data", 32)])
        self.source = source = Endpoint([("data", 32)])

        self.length = CSRStorage(8)
        delay_count = Signal(8)


        _valid = Signal()
        self.sync += _valid.eq(sink.valid)

        self.submodules.fsm = fsm = FSM(reset_state='PASS')

        fsm.act('PASS', 
            sink.connect(source,omit=['last','ready']),
            If(sink.last,
                If(self.length.storage > 0,
                    NextState('DELAY'),
                    NextValue(delay_count, self.length.storage)
                ).Else(
                    source.last.eq(1),
                )
            ).Else(
                sink.ready.eq(source.ready)
            )
        )

        fsm.act('DELAY', 
            sink.connect(source, omit=['last','ready']),
            If(delay_count == 0,
                sink.ready.eq(source.ready),
                source.last.eq(1),
                NextState('PASS'),
            ).Elif(sink.valid & source.ready,
                NextValue(delay_count, delay_count - 1),
            ),
        )
