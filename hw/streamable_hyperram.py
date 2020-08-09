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

class EmitterSource(Module):
    def __init__(self):
        self.source = source = Endpoint(EndpointDescription([("data", 32)]))
        data = Signal(32)
        
        self.sync += [
            source.valid.eq(1),
            source.data.eq(data),

            If(source.ready,
                data.eq(data + 1)
            )
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


from math import sin,pi

class StreamableHyperRAM(Module, AutoCSR):
    def __init__(self, hyperram_pads, devices=[], sim=False):
        self.bus = cpu_bus = Interface()
        

        if sim:
            self.submodules.hyperram = hyperram = HyperRAMSim(0x800000, init=[d for d in range(0,800)]*600)
        else:
            self.submodules.hyperram = hyperram = HyperRAMX2(hyperram_pads)

        devices = [d.bus for d in devices]
        
        #self.submodules.writer_pix = writer_pix = StreamWriter(external_sync=True)
        #self.submodules.reader_boson = reader_boson = StreamReader(external_sync=True)
        
        self.submodules.arbiter = Arbiter(devices + [cpu_bus], hyperram.bus)
        
        if not sim:
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
     


class HyperRAMSim(Module):
    def __init__(self, mem_or_size, read_only=None, init=None, bus=None):
        if bus is None:
            bus = Interface()
        self.bus = bus
        bus_data_width = len(self.bus.dat_r)
        if isinstance(mem_or_size, Memory):
            assert(mem_or_size.width <= bus_data_width)
            self.mem = mem_or_size
        else:
            self.mem = Memory(bus_data_width, mem_or_size//(bus_data_width//8), init=init)
        if read_only is None:
            if hasattr(self.mem, "bus_read_only"):
                read_only = self.mem.bus_read_only
            else:
                read_only = False

        ###

        latency = Signal(8)
        address = Signal(32)

        # memory
        port = self.mem.get_port(write_capable=not read_only, we_granularity=0,
            mode=READ_FIRST if read_only else WRITE_FIRST)
        self.specials += self.mem, port
        # generate write enable signal
        if not read_only:
            self.comb += port.we.eq(self.bus.cyc & self.bus.stb & self.bus.we & (self.bus.sel == 0xF) & (latency == 0))
        # address and data
        self.comb += [
            port.adr.eq(address[:len(port.adr)]),
            self.bus.dat_r.eq(port.dat_r)
        ]
        if not read_only:
            self.comb += port.dat_w.eq(self.bus.dat_w),
        # generate ack
        self.sync += [
            self.bus.ack.eq(0),
            If(self.bus.ack & self.bus.we,
                address.eq(address+1)
            ),

            If(self.bus.cyc & self.bus.stb,
                If(latency == 0,
                    If(~self.bus.ack | (bus.cti == 0b010), 
                        If(~self.bus.we,
                            address.eq(address+1),
                        ),
                        self.bus.ack.eq(1),
                    )
                ).Else(
                    latency.eq(latency-1),
                    address.eq(self.bus.adr),
                )
            ),


            If(~self.bus.cyc & ~self.bus.stb, latency.eq(5))
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