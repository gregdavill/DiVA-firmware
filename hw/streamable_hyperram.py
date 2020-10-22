from migen import *

from litex.soc.interconnect.csr import AutoCSR, CSR, CSRStatus, CSRStorage
from litex.soc.interconnect.stream import Endpoint, EndpointDescription, SyncFIFO, AsyncFIFO, Monitor
from wishbone_stream import StreamReader, StreamWriter, dummySource
from litex.soc.interconnect.wishbone import InterconnectShared, Arbiter, SRAM, InterconnectPointToPoint, Interface
from migen.genlib.cdc import PulseSynchronizer, MultiReg, BusSynchronizer

from litehyperbus.core.hyperram_ddrx2 import HyperRAMX2

class CSRSource(Module, AutoCSR):
    def __init__(self):
        self.source = source = Endpoint(EndpointDescription([("data", 32)]))
        self.data = CSR(32)

        self.sync += [
            source.valid.eq(self.data.re),
            source.data.eq(self.data.r)
        ]


class CSRSink(Module, AutoCSR):
    def __init__(self):
        self.sink = sink = Endpoint(EndpointDescription([("data", 32)]))
        self.data = CSR(32)
        self.ready = CSR(1)

        self.sync += [
            sink.ready.eq(self.data.we),
            self.data.w.eq(sink.data),
            self.ready.w.eq(sink.valid)
        ]

class StreamableHyperRAM(Module, AutoCSR):
    def __init__(self, hyperram_pads, devices=[]):
        self.bus = cpu_bus = Interface()

        self.submodules.hyperram = hyperram = HyperRAMX2(hyperram_pads)
        devices = [d.bus for d in devices]
        
        self.submodules.arbiter = Arbiter(devices + [cpu_bus], hyperram.bus)
        
        # Analyser signals for debug
        self.dbg = hyperram.dbg

        # CSRs for adjusting IO delays
        self.io_loadn = CSRStorage()
        self.io_move = CSRStorage()
        self.io_direction = CSRStorage()
        self.clk_loadn = CSRStorage()
        self.clk_move = CSRStorage()
        self.clk_direction = CSRStorage()

        self.comb += [
            hyperram.dly_io.loadn.eq(self.io_loadn.storage),
            hyperram.dly_io.move.eq(self.io_move.storage),
            hyperram.dly_io.direction.eq(self.io_direction.storage),

            hyperram.dly_clk.loadn.eq(self.clk_loadn.storage),
            hyperram.dly_clk.move.eq(self.clk_move.storage),
            hyperram.dly_clk.direction.eq(self.clk_direction.storage),
        ]
     
