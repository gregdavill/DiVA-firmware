from migen import *

from litex.soc.interconnect.csr import AutoCSR, CSR, CSRStatus, CSRStorage
from litex.soc.interconnect.stream import Endpoint, EndpointDescription, SyncFIFO, AsyncFIFO
from wishbone_stream import StreamReader, StreamWriter, dummySource
from litex.soc.interconnect.wishbone import InterconnectShared, Arbiter, SRAM, InterconnectPointToPoint
from migen.genlib.cdc import PulseSynchronizer, MultiReg, BusSynchronizer


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
        self.submodules.hyperram = hyperram = ClockDomainsRenamer({'sys':'ram', 'sys_shift':'ram_shift'})(HyperRAM(hyperram_pads))
        #self.submodules.hyperram = hyperram = HyperRAM(hyperram_pads)
        #self.hyperram = hyperram = ClockDomainsRenamer({'sys':'ram'})(SRAM(1024, False))
        
        self.submodules.writer = writer = ClockDomainsRenamer({'sys':'ram'})(StreamWriter())
        self.submodules.reader = reader = ClockDomainsRenamer({'sys':'ram'})(StreamReader())
        #self.submodules.writer = writer = StreamWriter()
        #self.submodules.reader = reader = StreamReader()
        self.submodules.writer_pix = writer_pix = ClockDomainsRenamer({'sys':'ram'})(StreamWriter(external_sync=True))

        self.submodules.reader_boson = reader_boson = ClockDomainsRenamer({'sys':'ram'})(StreamReader(external_sync=True))
        
        self.submodules.arbiter = ClockDomainsRenamer({'sys':'ram'})(Arbiter([writer_pix.bus, reader_boson.bus, reader.bus, writer.bus], hyperram.bus))
        #self.submodules.arbiter = Arbiter([reader.bus, writer.bus], hyperram.bus)
        #self.submodules.p2p = InterconnectPointToPoint(reader.bus, hyperram.bus)   

        self.writer_addr = CSRStorage(21)
        self.writer_enable = CSR(1)
        self.writer_len = CSRStorage(21)

        self.reader_addr = CSRStorage(21)
        self.reader_enable = CSR(1)
        self.reader_len = CSRStorage(21)
        self.reader_blank = CSRStorage(1)


        self.writer_pix_addr = CSRStorage(21)
        self.writer_pix_enable = CSR(1)
        self.writer_pix_len = CSRStorage(21)


        self.reader_boson_addr = CSRStorage(21)
        self.reader_boson_enable = CSR(1)
        self.reader_boson_len = CSRStorage(21)

        # CPU addressable logic 
        self.clear = CSR(1)
        self.submodules.source = CSRSource()
        self.submodules.sink = CSRSink()

        self.loadn = CSRStorage()
        self.move = CSRStorage()
        self.direction = CSRStorage()

        self.comb += [
            hyperram.loadn.eq(self.loadn.storage),
            hyperram.move.eq(self.move.storage),
            hyperram.direction.eq(self.direction.storage),
        ]
        


        self.pixels = Endpoint(EndpointDescription([("data", 32)]))
        self.pixels_reset = Signal()

        self.boson = Endpoint(EndpointDescription([("data", 32)]))
        self.boson_sync = Signal()

        # Patch values across clock domains
        #self.specials += [
        #    MultiReg(self.writer_addr.storage, writer.start_address, "sys"),
        #    MultiReg(self.writer_len.storage, writer.transfer_size, "sys"),
        #    MultiReg(self.reader_addr.storage, reader.start_address, "sys"),
        #    MultiReg(self.reader_len.storage, reader.transfer_size, "sys"),
        #]

        self.sync += [
            writer.start_address.eq(self.writer_addr.storage),
            writer.transfer_size.eq(self.writer_len.storage),
            reader.start_address.eq(self.reader_addr.storage),
            reader.transfer_size.eq(self.reader_len.storage),
            writer_pix.start_address.eq(self.writer_pix_addr.storage),
            writer_pix.transfer_size.eq(self.writer_pix_len.storage),

            reader_boson.start_address.eq(self.reader_boson_addr.storage),
            reader_boson.transfer_size.eq(self.reader_boson_len.storage),
        ]

        self.submodules.writer_en = writer_en = PulseSynchronizer("sys", "ram")
        self.submodules.reader_en = reader_en = PulseSynchronizer("sys", "ram")
        self.submodules.writer_pix_en = writer_pix_en = PulseSynchronizer("sys", "ram")
        self.submodules.writer_pix_restart = writer_pix_restart = PulseSynchronizer("sys", "ram")

        self.submodules.reader_boson_en = reader_boson_en = PulseSynchronizer("sys", "ram")


        self.comb += [
            writer_en.i.eq(self.writer_enable.re),
            writer.enable.eq(writer_en.o),
            reader_en.i.eq(self.reader_enable.re),
            reader.enable.eq(reader_en.o),

            writer_pix_en.i.eq(self.writer_pix_enable.re),
            writer_pix.enable.eq(writer_pix_en.o),

            writer_pix_restart.i.eq(self.pixels_reset),
            writer_pix.start.eq(writer_pix_restart.o),

            reader_boson_en.i.eq(self.reader_boson_enable.re),
            reader_boson.enable.eq(reader_boson_en.o),
        ]

       

        self.submodules.sink_fifo = sink_fifo = ResetInserter(["sys", "ram"])(
                ClockDomainsRenamer({'write':'ram', 'read':'sys'})(AsyncFIFO([("data", 32)], 4, buffered=False))
            )
        self.submodules.source_fifo = source_fifo = ResetInserter(["sys", "ram"])(
                ClockDomainsRenamer({'write':'sys', 'read':'ram'})(AsyncFIFO([("data", 32)], 4, buffered=False))
            )

        self.submodules.pix_fifo = pix_fifo = ResetInserter(["sys", "ram"])(
                ClockDomainsRenamer({'write':'ram', 'read':'sys'})(AsyncFIFO([("data", 32)], 256, buffered=False))
            )


        self.submodules.boson_fifo = boson_fifo = ResetInserter(["boson_rx", "ram"])(
                ClockDomainsRenamer({'write':'boson_rx', 'read':'ram'})(AsyncFIFO([("data", 32)], 256, buffered=False))
            )

        self.submodules.ram_ps = ram_ps = PulseSynchronizer("sys", "ram")
        self.submodules.boson_ps = boson_ps = PulseSynchronizer("sys", "ram")

        self.submodules.dummy_source = dummySource()

        boson_sync_ = Signal()
        self.sync += [
            boson_sync_.eq(self.boson_sync)
        ]

        self.comb += [
            If(self.reader_blank.storage,
                self.dummy_source.source.connect(source_fifo.sink),
            ).Else(
                self.source.source.connect(source_fifo.sink),
            ),
                source_fifo.source.connect(reader.sink),


            writer.source.connect(sink_fifo.sink),
            sink_fifo.source.connect(self.sink.sink),

            
            sink_fifo.reset_sys.eq(self.clear.re),
            source_fifo.reset_sys.eq(self.clear.re),

            self.boson.connect(boson_fifo.sink),
            boson_fifo.source.connect(reader_boson.sink),

            boson_ps.i.eq(self.boson_sync & ~boson_sync_),
            reader_boson.start.eq(boson_ps.o),

            #boson_rst.eq(boson_cnt != 0),
            boson_fifo.reset_boson_rx.eq(~self.boson_sync),
            boson_fifo.reset_ram.eq(~self.boson_sync),



            ram_ps.i.eq(self.clear.re),

            sink_fifo.reset_ram.eq(ram_ps.o),
            source_fifo.reset_ram.eq(ram_ps.o),



            pix_fifo.reset_sys.eq(0),
            pix_fifo.reset_ram.eq(0),

            # Pixel interface
            writer_pix.source.connect(pix_fifo.sink),
            pix_fifo.source.connect(self.pixels),
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

from hyperram import HyperBusPHY

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
        clocks={"sys": 20, "ram": 8, "ram_shift": (8,4)})
    



if __name__ == '__main__':
    unittest.main()