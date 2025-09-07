
from migen import *
from litex.soc.interconnect.stream import AsyncFIFO, SyncFIFO, Endpoint
from litex.gen import *


class AsyncSyncWatermarkedFIFO(LiteXModule):
    def __init__(self, layout, depth=None, buffered=False):

        self._afifo = afifo = AsyncFIFO(layout, depth=4, buffered=False)
        self._fifo = fifo = SyncFIFO(layout, depth=depth, buffered=buffered)
        self.sink = afifo.sink
        self.source = Endpoint(fifo.source.description)

        _timeout_value = 1024
        timeout = Signal(max=_timeout_value)

        fsm = FSM(reset_state="FILL")
        self.submodules += fsm
        
        self.submodules += afifo, fifo

        self.comb += [
            afifo.source.connect(fifo.sink)
        ]

        # Track the "last" element in a packet. 
        # If the FIFO contains a 'last' we hold the FSM in DRAIN until it leaves
        last = Signal()
        self.sync += [
            # Sent on entering FIFO
            If(fifo.source.valid & fifo.source.ready & fifo.source.last,
                last.eq(1)
            ),

            # Clear on leaving the FIFO
            If(fifo.sink.valid & fifo.sink.ready & fifo.sink.last,
                last.eq(0)
            ),
        ]


        fsm.act("FILL",
            If(fifo.source.valid,
                If(last | (timeout == 0) | (fifo.level > 64),
                    NextState("DRAIN"),
                ).Else(
                    NextValue(timeout, timeout - 1)
                )
            ).Else(
                NextValue(timeout, _timeout_value)
            )
        )
        fsm.act("DRAIN",
            If(~fifo.source.valid & ~last,
                NextState("FILL"),
                NextValue(timeout, _timeout_value)
            ),
            fifo.source.connect(self.source)
        )



class SyncAsyncWatermarkedFIFO(LiteXModule):
    def __init__(self, layout, depth=None, buffered=False):

        self._fifo = fifo = SyncFIFO(layout, depth=depth, buffered=buffered)
        self._afifo = afifo = AsyncFIFO(layout, depth=4, buffered=False)
        self.sink = Endpoint(fifo.sink.description)
        self.source = afifo.source

        fsm = FSM(reset_state="FILL")
        self.submodules += fsm
        
        self.submodules += afifo, fifo

        self.comb += [
            fifo.source.connect(afifo.sink)
        ]

        fsm.act("FILL",
            If(~fifo.sink.ready,
                NextState("DRAIN")
            ),
            self.sink.connect(fifo.sink)
        )
        fsm.act("DRAIN",
            If(fifo.sink.ready,
                If(fifo.level < (depth-64),
                    NextState("FILL"),
                )
            )
        )
