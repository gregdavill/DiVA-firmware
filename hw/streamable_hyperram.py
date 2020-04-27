from migen import *

from litex.soc.interconnect.csr import AutoCSR, CSR, CSRStatus
from litex.soc.interconnect.stream import Endpoint, EndpointDescription, SyncFIFO
from wishbone_stream import StreamReader, StreamWriter
from litex.soc.interconnect.wishbone import InterconnectShared, Arbiter, SRAM, InterconnectPointToPoint

from hyperram import HyperRAM

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
    def __init__(self, hyperram_pads):
        self.submodules.hyperram = hyperram = HyperRAM(hyperram_pads)
        #self.hyperram = hyperram = SRAM(1024)
        
        self.submodules.writer = writer = StreamWriter()
        self.submodules.reader = reader = StreamReader()
        
        self.submodules.arbiter = Arbiter([reader.bus, writer.bus], hyperram.bus)
        #self.submodules.p2p = InterconnectPointToPoint(reader.bus, hyperram.bus)   

        

        self.submodules.source = CSRSource()
        self.submodules.sink = CSRSink()
        


        self.submodules.sink_fifo = sink_fifo = SyncFIFO([("data", 32)], 8, buffered=True)
        self.submodules.source_fifo = source_fifo = SyncFIFO([("data", 32)], 8, buffered=True)

        self.comb += [
            self.source.source.connect(source_fifo.sink),
            source_fifo.source.connect(reader.sink),


            writer.source.connect(sink_fifo.sink),
            sink_fifo.source.connect(self.sink.sink),
        ]

    
# -=-=-=-= tests -=-=-=-=
import unittest 

def write_stream(stream, dat):
    yield stream.data.eq(dat)
    yield stream.valid.eq(1)
    yield
    yield stream.data.eq(0)
    yield stream.valid.eq(0)

from migen.genlib.cdc import MultiReg

from hyperram import HyperBusPHY

class TestWriter(unittest.TestCase):

    def test_dma_write(self):
        def write(dut):
            source = dut.source
            dut = dut.reader
            yield from dut._burst_size.write(2)
            yield from dut._start_address.write(0)
            yield from dut._transfer_size.write(4)
            yield from dut._enable.write(1)
            yield
            yield from write_stream(source.source,0xAA55BEEF)
            for i in range(32):
                yield from write_stream(source.source, 1 << i)
            yield

        def logger(dut):
            for i in range(32):
                yield
                    
        hyperram_pads = Record([
            ("rst_n" , 1),
            ("clk_p" , 1),
            ("clk_n" , 1),
            ("cs_n"  , 1),
            ("dq"    , 8),
            ("rwds"  , 1),
        ])

        
        dut = StreamableHyperRAM(hyperram_pads)
        

    

        run_simulation(dut, [write(dut), logger(dut)], vcd_name='stream.vcd')
    



if __name__ == '__main__':
    unittest.main()