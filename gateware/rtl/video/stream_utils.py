# This file is Copyright (c) 2020 Gregory Davill <greg.davill@gmail.com>
# License: BSD

from migen import *
from litex.soc.interconnect.stream import Endpoint
from migen.genlib.cdc import MultiReg
from rtl.edge_detect import EdgeDetect

from litex.soc.interconnect.csr import AutoCSR, CSR, CSRStatus, CSRStorage
from litex.soc.interconnect.stream import Endpoint, EndpointDescription, AsyncFIFO

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


        

## Unit tests 
import unittest

from litex.soc.interconnect.stream_sim import PacketStreamer, PacketLogger, Packet, Randomizer
from litex.soc.interconnect.stream import Pipeline

class TestStream(unittest.TestCase):
    def testPrepend(self):
        data = [i for i in range(2,10)]
        length = 5
        def generator(dut):
            
            d = Packet(data)
            yield from dut.prepend.length.write(length-1)
            yield from dut.streamer.send_blocking(d)

        def checker(dut):
            yield from dut.logger.receive()
            assert(dut.logger.packet == ([data[0]]*(length) + data))


        class DUT(Module):
            def __init__(self):
                self.submodules.prepend = StreamPrepend()
                
                self.submodules.streamer = PacketStreamer([("data", 32)])
                self.submodules.logger = PacketLogger([("data", 32)])

                self.submodules.pipeline = Pipeline(
                    self.streamer,
                    self.prepend,
                    self.logger
                )
                


        dut = DUT()
        generators = {
            "sys" :   [generator(dut),
                        checker(dut),
                      dut.streamer.generator(),
                      dut.logger.generator(),
                      ]
        }
        clocks = {"sys": 10}
        run_simulation(dut, generators, clocks,  vcd_name='test.vcd')


    def testAppend(self):
        data = [i for i in range(32,38)]
        length = 3
        def generator(dut):
            
            d = Packet(data)
            yield from dut.append.length.write(length-1)
            yield from dut.streamer.send_blocking(d)

        def checker(dut):
            yield from dut.logger.receive()
            assert(dut.logger.packet == (data + [data[-1]]*(length)))


        class DUT(Module):
            def __init__(self):
                self.submodules.append = StreamAppend()
                
                self.submodules.streamer = PacketStreamer([("data", 32)])
                self.submodules.logger = PacketLogger([("data", 32)])

                self.submodules.pipeline = Pipeline(
                    self.streamer,
                    self.append,
                    self.logger
                )
                


        dut = DUT()
        generators = {
            "sys" :   [generator(dut),
                        checker(dut),
                      dut.streamer.generator(),
                      dut.logger.generator(),
                      ]
        }
        clocks = {"sys": 10}
        run_simulation(dut, generators, clocks,  vcd_name='test.vcd')

