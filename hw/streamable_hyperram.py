from migen import *

from litex.soc.interconnect.csr import AutoCSR, CSR, CSRStatus, CSRStorage
from litex.soc.interconnect.stream import Endpoint, EndpointDescription, SyncFIFO, AsyncFIFO, Monitor
from wishbone_stream import StreamReader, StreamWriter, dummySource
from litex.soc.interconnect.wishbone import InterconnectShared, Arbiter, SRAM, InterconnectPointToPoint, Interface
from migen.genlib.cdc import PulseSynchronizer, MultiReg, BusSynchronizer



from hyperram_x2 import HyperRAMX2

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
        #self.bus = cpu_bus = Interface()
        

        self.submodules.hyperram = hyperram = HyperRAMX2(hyperram_pads)
        
        #self.submodules.writer = writer = StreamWriter()
        #self.submodules.reader = reader = StreamReader()
        #self.submodules.writer_pix = writer_pix = StreamWriter(external_sync=True)
        #self.submodules.reader_boson = reader_boson = StreamReader(external_sync=True)
        
        #self.submodules.arbiter = Arbiter([writer_pix.bus, reader_boson.bus, reader.bus, writer.bus, cpu_bus], hyperram.bus)
        #self.submodules.arbiter = Arbiter([cpu_bus], hyperram.bus)

        self.bus = hyperram.bus
        self.dbg = hyperram.dbg
        # CPU addressable logic 
        


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
     

    
# -=-=-=-= tests -=-=-=-=
import unittest 

def write_stream(stream, dat):
    yield stream.data.eq(dat)
    yield stream.valid.eq(1)
    yield
    yield stream.data.eq(0)
    yield stream.valid.eq(0)

#from migen.genlib.cdc import MultiReg


class TestWriter(unittest.TestCase):

    def test_dma_write(self):
        def write(dut):
            source = dut.source
            #dut = dut.reader

            for j in range(2):
                yield from dut.reader_enable.write(1)
                yield
                yield
                yield
                yield from write_stream(source.source,0xAA55BEEF)
                for _ in range(10):
                    yield

            for j in range(2):
                yield from dut.writer_enable.write(1)
                yield
                yield
                yield
                #yield from write_stream(source.source,0xAA55BEEF)
                for _ in range(200):
                    yield

        def logger(dut):
            for i in range(128):
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
        

    

        run_simulation(dut, [write(dut), logger(dut)], vcd_name='stream.vcd', 
        clocks={"sys": 20, "hr": 8, "ram_shift": (8,4)})
    



if __name__ == '__main__':
    unittest.main()