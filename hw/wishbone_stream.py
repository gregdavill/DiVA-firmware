# This file is Copyright (c) 2019 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

import unittest

from migen import *

from litex.soc.interconnect import wishbone
from litex.soc.interconnect.stream import SyncFIFO,EndpointDescription, Endpoint, AsyncFIFO
from litex.soc.interconnect import stream_sim

from litex.soc.interconnect.csr import *

import random

def data_stream_description(dw):
    payload_layout = [("data", dw)]
    return EndpointDescription(payload_layout)

class dummySource(Module):
    def __init__(self):
        self.source = source = Endpoint(data_stream_description(32))
        counter = Signal(32)

        self.comb += [
            source.valid.eq(1),
            source.data.eq(counter)
        ]

        self.sync += [
            If(source.ready,
                counter.eq(counter + 1)
            )
        ]

class dummySink(Module):
    def __init__(self):
        self.sink = sink = Endpoint(data_stream_description(32))
        
        self.comb += [
            sink.ready.eq(1)
        ]

class StreamWriter(Module, AutoCSR):
    def __init__(self):
        self.bus  = bus = wishbone.Interface()
        self.source = source = Endpoint(data_stream_description(32))

        tx_cnt = Signal(32)
        last_address = Signal()
        busy = Signal()
        active = Signal()
        burst_cnt = Signal(32)
        burst_end = Signal()
        start_address = Signal(21)
        transfer_size = Signal(21)
        


        self.start_address = Signal(21)
        self.transfer_size = Signal(21)

        burst_size = Signal(8, reset=32)

        #self.tx_cnt = Signal(21)
        #self._busy = CSRStatus()
        self.enable = Signal()
        self.reset = Signal()

        
        
    

        self.comb += [
            bus.sel.eq(0xF),
            bus.we.eq(0),
            bus.cyc.eq(active),
            bus.stb.eq(active),
            bus.adr.eq(start_address + tx_cnt),

            source.data.eq(bus.dat_r),
            source.valid.eq(bus.ack),

            If(~active,
                bus.cti.eq(0b000) # CLASSIC_CYCLE
            ).Elif(burst_end,
                bus.cti.eq(0b111), # END-OF-BURST
            ).Else(
                bus.cti.eq(0b010), # LINEAR_BURST
            )
        ]

        self.comb += [
            

                burst_end.eq(last_address | (burst_cnt == burst_size - 1)),
            #)
        ]

        self.sync += [
            last_address.eq(tx_cnt == transfer_size - 1),
            If(bus.ack,
                If(last_address,
                    tx_cnt.eq(0)
                ).Else(
                    tx_cnt.eq(tx_cnt + 1)
                )
            ),
            # Burst Counter
            If(~active,
                burst_cnt.eq(0)
            ).Else(
                If(bus.ack,
                    burst_cnt.eq(burst_cnt + 1)
                )
            ),

        ]

        # Main FSM
        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            If(busy & source.ready,
                NextState("ACTIVE"),
            ),
            If(self.enable,
                NextValue(busy,1),
                NextValue(start_address, self.start_address),
                NextValue(transfer_size, self.transfer_size),
            )
        )
        fsm.act("ACTIVE",
            If(~source.ready,
                NextState("IDLE")
            ),
            If(burst_end & bus.ack,
                NextState("IDLE"),
                If(last_address,
                    NextValue(busy,0),
                )
            ),

        )

        self.comb += active.eq(fsm.ongoing("ACTIVE") & source.ready)

class StreamReader(Module, AutoCSR):
    def __init__(self):
        self.bus  = bus = wishbone.Interface()
        self.sink = sink = Endpoint(data_stream_description(32))

        tx_cnt = Signal(32)
        last_address = Signal()
        busy = Signal()
        active = Signal()
        burst_cnt = Signal(32)
        burst_end = Signal()
        start_address = Signal(21)
        transfer_size = Signal(21)
        


        self.start_address = Signal(21)
        self.transfer_size = Signal(21)

        burst_size = Signal(8, reset=32)

        #self.tx_cnt = Signal(21)
        #self._busy = CSRStatus()
        self.enable = Signal()
        self.reset = Signal()

        self.comb += [
            bus.sel.eq(0xF),
            bus.we.eq(active),
            bus.cyc.eq(active),
            bus.stb.eq(active),
            bus.adr.eq(start_address + tx_cnt),
            bus.dat_w.eq(sink.data),

            sink.ready.eq(bus.ack),

            If(~active,
                bus.cti.eq(0b000) # CLASSIC_CYCLE
            ).Elif(burst_end,
                bus.cti.eq(0b111), # END-OF-BURST
            ).Else(
                bus.cti.eq(0b010), # LINEAR_BURST
            )
        ]

        self.comb += [
            #If(self._burst_size.storage == 1,
            #    burst_end.eq(1),
            #).Else(
                burst_end.eq(last_address | (burst_cnt == burst_size - 1)),
            #)
        ]

        self.sync += [
            last_address.eq(tx_cnt == transfer_size - 1),
            If(bus.ack,
                If(last_address,
                    tx_cnt.eq(0)
                ).Else(
                    tx_cnt.eq(tx_cnt + 1)
                )
            ),
            # Burst Counter
            If(~active,
                burst_cnt.eq(0)
            ).Else(
                If(bus.ack,
                    burst_cnt.eq(burst_cnt + 1)
                )
            ),
        ]

        # Main FSM
        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            If(busy & sink.valid,
                NextState("ACTIVE"),
            ),
            If(self.enable,
                NextValue(busy,1),
                NextValue(start_address, self.start_address),
                NextValue(transfer_size, self.transfer_size),
            )
        )
        fsm.act("ACTIVE",
            If(~sink.valid,
                NextState("IDLE")
            ),
            If(burst_end & bus.ack,
                NextState("IDLE"),
                If(last_address,
                    NextValue(busy,0)
                )
            ),
        )

        self.comb += active.eq(fsm.ongoing("ACTIVE") & sink.valid)


# -=-=-=-= tests -=-=-=-=

def write_stream(stream, dat):
    yield stream.data.eq(dat)
    yield stream.valid.eq(1)
    yield
    yield stream.data.eq(0)
    yield stream.valid.eq(0)

class TestWriter(unittest.TestCase):

    def test_dma_write(self):
        def write(dut):
            dut = dut.writer
            yield from dut._burst_size.write(2)
            yield from dut._start_address.write(0)
            yield from dut._transfer_size.write(4)
            yield from dut._enable.write(1)
            yield
            while (yield dut._busy.status != 0):
                yield
            yield
            yield

        def logger(dut):
            dut = dut.writer
            yield dut.source.ready.eq(1)
            yield
                    

        class test(Module):
            def __init__(self):    
                self.submodules.writer = StreamWriter()
                self.submodules.wb_mem = wishbone.SRAM(32, init=[i for i in range(8)])
                self.comb += self.writer.bus.connect(self.wb_mem.bus)

        dut = test()
        

        run_simulation(dut, [write(dut), logger(dut)], vcd_name='write.vcd')
    


if __name__ == '__main__':
    unittest.main()