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
        
        self._start_address = CSRStorage(32)
        self._transfer_size = CSRStorage(32)
        self._burst_size = CSRStorage(32)
        self._evt_enable = CSRStorage(1)
        self._tx_cnt = CSRStatus(32)
        self._busy = CSRStatus()
        self._enable = CSR()
        self._reset = CSR()

        self.evt_start = Signal()
        self.evt_done = evt_done = Signal()
        
        # Connect Status registers
        self.comb += [
            self._tx_cnt.status.eq(tx_cnt),
            self._busy.status.eq(busy)
        ]

        self.comb += [
            bus.sel.eq(0xF),
            bus.we.eq(0),
            bus.cyc.eq(active),
            bus.stb.eq(active),
            bus.adr.eq(self._start_address.storage + tx_cnt),

            source.data.eq(bus.dat_r),
            source.valid.eq(bus.ack)
        ]

        self.comb += [
            If(self._burst_size.storage == 1,
                burst_end.eq(1),
            ).Else(
                burst_end.eq(last_address | (burst_cnt == self._burst_size.storage - 1)),
            )
        ]

        self.sync += [
            last_address.eq(tx_cnt == self._transfer_size.storage - 1),
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

            If(self._reset.re,
                tx_cnt.eq(0),
                burst_cnt.eq(0),
            )
        ]

        # Main FSM
        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            If(busy & source.ready,
                NextState("ACTIVE"),
            ),
            If(self._enable.re | (self._evt_enable.storage & self.evt_start),
                NextValue(busy,1),
            )
        )
        fsm.act("ACTIVE",
            If(~source.ready,
                NextState("IDLE")
            ),
            If(burst_end & bus.ack,
                NextState("IDLE"),
                If(last_address,
                    evt_done.eq(1),
                    NextValue(busy,0),
                )
            ),

            If(self._reset.re,
                NextValue(busy, 0),
                NextState("IDLE")
            )
        )

        self.comb += active.eq(fsm.ongoing("ACTIVE") & source.ready)

class StreamReader(Module, AutoCSR):
    def __init__(self):
        self.bus  = bus = wishbone.Interface()
        self.sink = sink = Endpoint(data_stream_description(32))

        tx_cnt = Signal(32)
        last_address = Signal()
        busy = Signal()
        done = Signal()
        active = Signal()
        burst_cnt = Signal(32)
        burst_end = Signal()
        
        self._start_address = CSRStorage(32)
        self._transfer_size = CSRStorage(32)
        self._burst_size = CSRStorage(32)
        self._evt_enable = CSRStorage(1)
        self._tx_cnt = CSRStatus(32)
        self._busy = CSRStatus()
        self._done = CSRStatus()
        self._enable = CSR()
        self._reset = CSR()


        self.evt_start = Signal()
        self.evt_done = evt_done = Signal()
        
        # Connect Status registers
        self.comb += [
            self._tx_cnt.status.eq(tx_cnt),
            self._busy.status.eq(busy),
            self._done.status.eq(done)
        ]

        self.comb += [
            bus.sel.eq(0xF),
            bus.we.eq(active),
            bus.cyc.eq(active),
            bus.stb.eq(active),
            bus.adr.eq(self._start_address.storage + tx_cnt),
            bus.dat_w.eq(sink.data),

            sink.ready.eq(bus.ack)
        ]

        self.comb += [
            If(self._burst_size.storage == 1,
                burst_end.eq(1),
            ).Else(
                burst_end.eq(last_address | (burst_cnt == self._burst_size.storage - 1)),
            )
        ]

        self.sync += [
            last_address.eq(tx_cnt == self._transfer_size.storage - 1),
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

            If(self._reset.re,
                tx_cnt.eq(0),
                burst_cnt.eq(0),
                done.eq(0),
            ),

            If(evt_done,
                done.eq(1),
            )

        ]

        # Main FSM
        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            If(busy & sink.valid,
                NextState("ACTIVE"),
            ),
            If(self._enable.re | (self._evt_enable.storage & self.evt_start),
                NextValue(busy,1),
            )
        )
        fsm.act("ACTIVE",
            If(~sink.valid,
                NextState("IDLE")
            ),
            If(burst_end & bus.ack,
                NextState("IDLE"),
                If(last_address,
                    NextValue(busy,0),
                    evt_done.eq(1)
                )
            ),

            If(self._reset.re,
                NextValue(busy, 0),
                NextState("IDLE")
            )
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
                self.submodules.wb_mem = wishbone.SRAM(32, 8, init=[i for i in range(8)])
                self.comb += self.writer.bus.connect(self.wb_mem.bus)

        dut = test()
        

        run_simulation(dut, [write(dut), logger(dut)], vcd_name='write.vcd')
    

class TestReader(unittest.TestCase):

    def test_dma_write(self):
        def write(dut):
            dut = dut.reader
            yield from dut._burst_size.write(3)
            yield from dut._start_address.write(0)
            yield from dut._transfer_size.write(7)
            yield from dut._enable.write(1)
            yield
            yield
            yield
            ...

        def logger(dut):
            mem = dut.wb_mem
            dut = dut.reader
            j = 0
            for i in range(32):
                if (yield ((dut.sink.ready == 0) & (dut.sink.valid))):
                    yield
                else:
                    yield dut.sink.valid.eq(1)
                    yield dut.sink.data.eq(j)
                    j = j + 1
                    yield

            yield
            yield
            for i in range(7):
                yield from dut._start_address.write(i)
                yield
                assert (yield dut.bus.dat_r) == i
                
                    

        class test(Module):
            def __init__(self):    
                self.submodules.reader = StreamReader()
                self.submodules.wb_mem = wishbone.SRAM(32,read_only=None, init=[0 for i in range(8)])
                self.comb += self.reader.bus.connect(self.wb_mem.bus)

        dut = test()
        

        run_simulation(dut, [write(dut), logger(dut)], vcd_name='read.vcd')
    


class TestReaderFIFO(unittest.TestCase):

    def test_dma_write(self):
        def write(dut):
            dut = dut.reader
            yield from dut._burst_size.write(16)
            yield from dut._start_address.write(0)
            yield from dut._transfer_size.write(16)
            yield from dut._enable.write(1)
            yield
            yield
            yield
            ...

        def logger(dut):
            mem = dut.wb_mem
            reader = dut.reader
            dut = dut.fifo
            j = 0
            for i in range(16):
                    yield dut.sink.valid.eq(1)
                    yield dut.sink.data.eq(0xAA000000 | j)
                    yield 
                    yield dut.sink.valid.eq(0)
                    for _ in range(random.randint(1,5)):
                        yield
                    j = j + 1
                    

            yield
            yield
            for i in range(16):
                yield from reader._start_address.write(i)
                yield
                assert (yield reader.bus.dat_r) == (0xAA000000 | i)
            
                
                    

        class test(Module):
            def __init__(self):    
                self.submodules.fifo = ClockDomainsRenamer({"write": "sys1", "read": "sys"})(AsyncFIFO([("data",32)], 8))
                self.submodules.reader = StreamReader()
                self.submodules.wb_mem = wishbone.SRAM(64,read_only=None, init=[0 for i in range(16)])
                self.comb += self.reader.bus.connect(self.wb_mem.bus)
                self.comb += self.fifo.source.connect(self.reader.sink)
                

        dut = test()
        

        run_simulation(dut, [write(dut), logger(dut)], vcd_name='fifo.vcd', clocks={"sys":10, "sys1":20})
    

if __name__ == '__main__':
    unittest.main()