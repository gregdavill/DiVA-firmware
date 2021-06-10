# This file is Copyright (c) 2020 Gregory Davill <greg.davill@gmail.com>
# License: BSD

import unittest

from migen import *

from litex.soc.interconnect import wishbone
from litex.soc.interconnect.stream import EndpointDescription, Endpoint

from litex.soc.interconnect.csr import *

def data_stream_description(dw):
    payload_layout = [("data", dw)]
    return EndpointDescription(payload_layout)

class dummySource(Module):
    def __init__(self):
        self.source = source = Endpoint(data_stream_description(32))
        counter = Signal(32)

        self.clr = Signal()

        frame = Signal(32)
        v_ctr = Signal(32)
        h_ctr = Signal(32)
        r = Signal(8)
        g = Signal(8)
        b = Signal(8)


        self.comb += [
            source.valid.eq(1),
            source.data.eq(Cat(r,g,b,Signal(8))),   
        ]

        self.sync += [
            If(source.ready,
                h_ctr.eq(h_ctr + 1),
                If(h_ctr >= 800-1,
                    h_ctr.eq(0),
                    v_ctr.eq(v_ctr + 1),
                    If(v_ctr >= 600-1,
                        v_ctr.eq(0),
                        frame.eq(frame + 1)
                    )
                )
            ),

            If(self.clr, 
                v_ctr.eq(0),
                h_ctr.eq(0)
            )
        ]

        speed = 1

        frame_tri = (Mux(frame[8], ~frame[:8], frame[:8]))
        frame_tri2 = (Mux(frame[9], ~frame[1:9], frame[1:9]))

        X = Mux(v_ctr[6], h_ctr + frame[speed:], h_ctr - frame[speed:])
        Y = v_ctr
        self.sync += [
            r.eq(frame_tri[1:]),
            g.eq(v_ctr * Mux(X & Y, 255, 0)),
            b.eq(~(frame_tri2 + (X ^ Y)) * 255)
        ]

class dummySink(Module):
    def __init__(self):
        self.sink = sink = Endpoint(data_stream_description(32))
        
        self.comb += [
            sink.ready.eq(1)
        ]

class StreamBuffers(Module, AutoCSR):
    def __init__(self):
        n_buffers = 3

        buffers = []

        for i in range(n_buffers):
            csr = CSRStorage(32, name=f'adr{i}')
            setattr(self, f'adr{i}', csr)
            buffers += [csr.storage]

        

        # Stream In buffer interface
        self.rx_buffer = Signal(32)
        rx_idx = Signal(3, reset=1)
        self.rx_release = Signal()

        # Stream out interface
        self.tx_buffer = Signal(32)
        tx_idx = Signal(3, reset=0)

        self.sync += [
            If(self.rx_release,
                rx_idx.eq(rx_idx + 1),
                If(rx_idx >= (n_buffers-1),
                    rx_idx.eq(0),
                ),
                tx_idx.eq(tx_idx + 1),
                If(tx_idx >= (n_buffers-1),
                    tx_idx.eq(0),
                ),
            )
        ]

        for i in range(n_buffers):
            self.comb += [
                If(rx_idx == i, 
                    self.rx_buffer.eq(buffers[i])
                ),
                If(tx_idx == i, 
                    self.tx_buffer.eq(buffers[i])
                ),
            ]
    

@ResetInserter()
class StreamWriter(Module, AutoCSR):
    def __init__(self):
        self.bus  = bus = wishbone.Interface()
        self.source = source = Endpoint(data_stream_description(32))

        self._sinks = []

        tx_cnt = Signal(32)
        last_address = Signal()
        busy = Signal()
        done = Signal()
        evt_done = Signal()
        active = Signal()
        burst_end = Signal()
        burst_cnt = Signal(32)
        
        self.start_address = Signal(32)
        adr = Signal(32)

        self.transfer_size = CSRStorage(32)
        self.burst_size = CSRStorage(32, reset=256)

        self.done = CSRStatus()

        self.enable = CSR()
        self._reset = CSR()


        self.start = Signal()
        self.short = Signal()
        self.external_sync = CSRStorage()

        self.sink_csr = CSRStorage(4, name="sink_mux")

        enabled = Signal()
        overflow = Signal()
        underflow = Signal()
        self.comb += [
            overflow.eq(source.ready & ~source.valid),
            underflow.eq(~source.ready & source.valid),

            self.done.status.eq(done)
        ]

        self.comb += [
            bus.sel.eq(0xF),
            bus.we.eq(0),
            bus.cyc.eq(active),
            bus.stb.eq(active),
            bus.adr.eq(adr[:-2] + tx_cnt),

            source.data.eq(bus.dat_r),
            source.valid.eq(bus.ack & active),

            If(~active,
                bus.cti.eq(0b000) # CLASSIC_CYCLE
            ).Elif(burst_end,
                bus.cti.eq(0b111), # END-OF-BURST
            ).Else(
                bus.cti.eq(0b010), # LINEAR_BURST
            ),
        ]

        self.comb += [
            burst_end.eq(last_address | (burst_cnt == self.burst_size.storage - 1)),
            If(self.short,
                last_address.eq(tx_cnt >= self.transfer_size.storage - 1 - 28*640),
            ).Else(
                last_address.eq(tx_cnt >= self.transfer_size.storage - 1),
            )
        ]

        self.sync += [
            If(bus.ack & active,
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
                If(bus.ack & active, 
                    burst_cnt.eq(burst_cnt + 1)
                )
            ),
            If(self.enable.re,
                enabled.eq(self.enable.r[0])
            ),
            
            If(evt_done,
                done.eq(1),
            )
        ]

        # Main FSM
        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            If(busy & source.ready,
                NextState("ACTIVE"),
            ),
            If((self.start & enabled & self.external_sync.storage) | (~self.external_sync.storage & self.enable.re),
                NextValue(busy,1),
                If(self.short,
                    NextValue(adr, self.start_address + 14*640),
                ).Else(
                    NextValue(adr, self.start_address),
                )
            )
        )
        fsm.act("ACTIVE",
            If(~source.ready,
                NextState("IDLE")
            ),
            If(burst_end & bus.ack & active,
                NextState("IDLE"),
                If(last_address,
                    evt_done.eq(1),
                    NextValue(busy,0),
                )
            ),
        )

        self.comb += active.eq(fsm.ongoing("ACTIVE") & source.ready)

    def do_finalize(self):
        self.comb += self.reset.eq(self._reset.re)

    def add_sink(self, sink, sink_name, ext_start=Signal()):
        self._sinks += [(sink, sink_name, ext_start)]
        #s,name = self._sinks[i]
        self.comb += [
            If(self.sink_csr.storage == (len(self._sinks) - 1),
                self.source.connect(sink),
                self.start.eq(ext_start)
            )
        ]
          

@ResetInserter()
class StreamReader(Module, AutoCSR):
    def __init__(self):
        self.bus  = bus = wishbone.Interface()
        self.sink = sink = Endpoint(data_stream_description(32))

        self._sources = []

        tx_cnt = Signal(32)
        last_address = Signal()
        busy = Signal()
        done = Signal()
        self.evt_done = evt_done = Signal()
        active = Signal()
        burst_end = Signal()
        burst_cnt = Signal(32)
        
        self.start_address = Signal(32)
        adr = Signal(32)

        self.transfer_size = CSRStorage(32)
        self.burst_size = CSRStorage(32, reset=256)

        self.done = CSRStatus()

        self.enable = CSR()
        self._reset = CSR()

        self.start = Signal()
        self.external_sync = CSRStorage()

        self.source_csr = CSRStorage(4, name="source_mux")

        enabled = Signal()
        overflow = Signal()
        underflow = Signal()
        self.comb += [
            overflow.eq(sink.ready & ~sink.valid),
            underflow.eq(~sink.ready & sink.valid),

            self.done.status.eq(done)
        ]

        self.comb += [
            bus.sel.eq(0xF),
            bus.we.eq(active),
            bus.cyc.eq(active),
            bus.stb.eq(active),
            bus.adr.eq(adr[:-2] + tx_cnt),
            bus.dat_w.eq(sink.data),
            sink.ready.eq(bus.ack & active),

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
                burst_end.eq(last_address | (burst_cnt == self.burst_size.storage - 1)),
                last_address.eq(tx_cnt == self.transfer_size.storage - 1),
            #)
        ]

        self.sync += [

            If(bus.ack & active,
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
                If(bus.ack & active,
                    burst_cnt.eq(burst_cnt + 1)
                )
            ),
            If(self.enable.re,
                enabled.eq(self.enable.r[0])
            ),

            If(evt_done,
                done.eq(1),
            ),
        ]

        # Main FSM
        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            If(busy & sink.valid,
                NextState("ACTIVE"),
            ),
            If((self.start & enabled & self.external_sync.storage) | (~self.external_sync.storage & self.enable.re),
                NextValue(busy,1),
                NextValue(adr, self.start_address),
            )
        )
        fsm.act("ACTIVE",
            If(~sink.valid,
                NextState("IDLE")
            ),
            If(burst_end & bus.ack & active,
                NextState("IDLE"),
                If(last_address,
                    NextValue(busy,0),
                    evt_done.eq(1),
                )
            ),
        )

        self.comb += active.eq(fsm.ongoing("ACTIVE") & sink.valid)

    def do_finalize(self):
        self.comb += [
            self.reset.eq(self._reset.re),
        ]

    def add_source(self, source, source_name, ext_start=Signal()):
        self._sources += [(source, source_name, ext_start)]
        #s,name = self._sinks[i]
        self.comb += [
            If(self.source_csr.storage == (len(self._sources) - 1),
                #self.sink.connect(source),
                source.connect(self.sink),
                self.start.eq(ext_start)
            )
        ]

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
            dut = dut.reader
            yield from dut.start_address.write(0x0)
            yield from dut.transfer_size.write(4)
            yield from dut.burst_size.write(2)
            yield from dut.enable.write(1)
            yield
            for _ in range(64):
                yield
            yield

        def logger(dut):
            yield dut.reader.sink.valid.eq(1)
            for j in range(2):
                while (yield dut.reader.bus.cyc == 0):
                    yield
                for _ in range(4):
                    yield
                for i in range(2):
                    yield dut.reader.bus.ack.eq(1)
                    yield dut.reader.sink.valid.eq(~((j == 1) & (i == 0)))
                    yield
                    #yield
                yield dut.reader.bus.ack.eq(0)
                yield
                    

        class test(Module):
            def __init__(self):    
                self.submodules.reader = StreamReader()
                self.submodules.dummySource = ds = dummySource()

                #self.comb += ds.source.connect(self.reader.sink)
                
        dut = test()
        

        run_simulation(dut, [write(dut), logger(dut)], vcd_name='write.vcd')
    


if __name__ == '__main__':
    unittest.main()