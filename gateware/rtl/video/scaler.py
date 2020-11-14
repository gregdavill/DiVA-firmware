# This file is Copyright (c) 2020 Gregory Davill <greg.davill@gmail.com>
# License: BSD

from migen import *
from litex.soc.interconnect.stream import Endpoint
from migen.genlib.cdc import MultiReg
from rtl.edge_detect import EdgeDetect

from litex.soc.interconnect.csr import AutoCSR, CSR, CSRStatus, CSRStorage
from litex.soc.interconnect.stream import Endpoint, EndpointDescription, AsyncFIFO

from litex.soc.interconnect.stream import *

def rgb_layout(dw):
    return [("r", dw), ("g", dw), ("b", dw)]

def W(x):
    a = -0.5
    if abs(x) <= 1:
        return (a+2)*abs(x)**3 - (a+3)*abs(x)**2 + 1
    if abs(x) < 2:
        return (a)*abs(x)**3 - (5*a)*abs(x)**2 + 8*a*abs(x) - 4*a
    return 0


class StallablePipelineActor(BinaryActor):
    def __init__(self, latency):
        self.latency = latency
        self.pipe_ce = Signal()
        self.busy    = Signal()
        self.stall   = Signal()
        BinaryActor.__init__(self, latency)

    def build_binary_control(self, sink, source, latency):
        busy  = 0
        valid = sink.valid
        stall_n = Signal()
        for i in range(latency):
            valid_n = Signal()
            self.sync += If(self.pipe_ce & ~(~stall_n & self.stall), valid_n.eq(valid))
            valid = valid_n
            busy = busy | valid

        self.comb += [
            self.pipe_ce.eq((source.ready | ~valid)),
            sink.ready.eq(self.pipe_ce & ~self.stall),
            source.valid.eq(valid),
            self.busy.eq(busy)
        ]
        self.sync += [
            If(self.pipe_ce,
                stall_n.eq(self.stall)
            )
        ]
        first = sink.valid & sink.first
        last  = sink.valid & sink.last
        for i in range(latency):
            first_n = Signal(reset_less=True)
            last_n  = Signal(reset_less=True)
            self.sync += \
                If(self.pipe_ce & ~self.stall,
                    first_n.eq(first),
                    last_n.eq(last)
                )
            first = first_n
            last  = last_n
        self.comb += [
            source.first.eq(first),
            source.last.eq(last)
        ]

# Simple datapath that create n-taps of a delayed signal.
@CEInserter()
class MultiTapDatapath(Module):
    def __init__(self, taps):
        self.sink = sink = Record(rgb_layout(8))
        self.source = source = Record(rgb_layout(8))
        self.ntaps = taps

        # # #
        
        # delay rgb signals
        rgb_delayed = [sink]
        for i in range(taps):
            rgb_n = Record(rgb_layout(8))
            for name in ["r", "g", "b"]:
                self.sync += getattr(rgb_n, name).eq(getattr(rgb_delayed[-1], name))
            rgb_delayed.append(rgb_n)
        
        self.tap = rgb_delayed

class FilterElement(Module):
    latency = 1

    def __init__(self, dw=8):
        self.sink = sink = Signal(dw)
        self.source = source = Signal((24, True))
        self.coef = coef = Signal((10,True))

        sig_in = Signal((dw+1, True))
        sig_out = Signal((24,True))

        mult = Signal(24)

        self.comb += [
            sig_in[:dw].eq(sink),
            sig_in[-1].eq(0),
            source.eq(sig_out)
        ]

        self.sync += mult.eq(sig_in * coef)
        self.comb += sig_out.eq(mult)

@CEInserter()
class RGBFilterElement(Module):
    def __init__(self):
        self.sink = sink = Record(rgb_layout(8))
        self.source = source = Record(rgb_layout((24, True)))
        self.coef = coef = Signal((10,True))

        fr = FilterElement()
        fg = FilterElement()
        fb = FilterElement()
        self.submodules += fr, fg, fb

        # Inputs
        self.comb += [
            fr.sink.eq(sink.r),
            fg.sink.eq(sink.g),
            fb.sink.eq(sink.b),
        
            fr.coef.eq(coef),
            fg.coef.eq(coef),
            fb.coef.eq(coef),
        
        ]

        # Outputs
        self.comb += [
            source.r.eq(fr.source),
            source.g.eq(fg.source),
            source.b.eq(fb.source),
        ]


class MultiTapFilter(Module, AutoCSR):
    def __init__(self, n_taps, n_phase):
        self.filters = filters = []
        for i in range(n_taps):
            f = RGBFilterElement()
            filters += [f]

            self.submodules += f
            self.comb += f.ce.eq(self.pipe_ce & self.busy)


        self.phase_ce = Signal()

        self.coeff_phase = CSRStorage(8)
        self.coeff_tap = CSRStorage(8)
        self.coeff_data = CSRStorage(10)
        self.coeff_stall = CSRStorage()
        self.coeff_en = CSRStorage()

        

        coeff_memory = Memory(10*n_taps + 1, n_phase)
        self.specials += coeff_memory

        coeff_memory_we_port = coeff_memory.get_port(write_capable=True)
        self.comb += [
            coeff_memory_we_port.we.eq(self.coeff_en.storage),
            coeff_memory_we_port.adr.eq(self.coeff_phase.storage),
        ]

        for i in range(n_taps):
            self.comb += If(self.coeff_tap.storage == i,
                    coeff_memory_we_port.dat_w.eq(coeff_memory_we_port.dat_r),
                    coeff_memory_we_port.dat_w[i*10:(i+1)*10].eq(self.coeff_data.storage),
                    coeff_memory_we_port.dat_w[n_taps*10].eq(self.coeff_stall.storage),
                )
        
        coeff_memory_port = coeff_memory.get_port(has_re=True)
        self.specials += coeff_memory_port, coeff_memory_we_port

        self.phases = phases = CSRStorage(8)
        self.starting_phase = starting_phase = CSRStorage(8)

        self.phase = phase = Signal(8, reset=0)

        self.sync += [
            If(self.phase_ce,
                phase.eq(phase + 1),
                If((phase >= (phases.storage - 1)) | (phase >= n_phase),
                    phase.eq(0),
                ),
                self.stall.eq(coeff_memory_port.dat_r[-1])
            ),
        ]

        self.comb += [
            coeff_memory_port.re.eq(self.pipe_ce),
            coeff_memory_port.adr.eq(phase),
        ]

        # Connect up CSRs to filters
        for t in range(n_taps):
            self.comb += filters[t].coef.eq(coeff_memory_port.dat_r[t*10:((t+1)*10)])


        self.out_r = Signal(8)
        self.out_g = Signal(8)
        self.out_b = Signal(8)
        
        for ch in ['r', 'g', 'b']:
            
            # Sum up output from all filter taps
            sum0 = Signal(24)
            v = 0
            for f in filters:
                v += getattr(f.source, ch)
            self.sync += If(self.pipe_ce & self.busy,
                    sum0.eq(v)
                )
            
            # Combine that into an 8bit output, 
            # take care of negative, overflow, underflow, and fixed point multiplication scaling
            bitnarrow = Signal(8)
            self.comb += [
                If(sum0[-1] == 1,
                    bitnarrow.eq(0),  # Saturate negative values to 0
                ).Elif(sum0[8:] > 255,
                    bitnarrow.eq(255),
                ).Else(
                    bitnarrow.eq(sum0[8:]),
                )
            ]

            # Connect channel to output
            self.comb += {
                'r': self.out_r,
                'g': self.out_g,
                'b': self.out_b,
            }[ch].eq(bitnarrow)




@ResetInserter()
class ScalerWidth(StallablePipelineActor, MultiTapFilter, AutoCSR):
    def __init__(self):
        self.sink = sink = Endpoint([("data", 32)])
        self.source = source = Endpoint([("data", 32)])
        n_taps = 4
        n_phase = 128

        StallablePipelineActor.__init__(self, n_taps + 1)
        MultiTapFilter.__init__(self, n_taps, n_phase)
        
        self.comb += [
            self.phase_ce.eq(self.pipe_ce & self.busy)
        ]


        self.submodules.tap_datapath = tap_dp = MultiTapDatapath(n_taps)
        self.comb += self.tap_datapath.ce.eq(self.pipe_ce & ~self.stall)
        
        for i in range(n_taps):
            self.comb += self.filters[i].sink.eq(tap_dp.tap[i])


        # Connect data into pipeline
        self.comb += [
            self.tap_datapath.sink.r.eq(sink.data[0:8]),
            self.tap_datapath.sink.g.eq(sink.data[8:16]),
            self.tap_datapath.sink.b.eq(sink.data[16:24]),

            source.data[0:8].eq(self.out_r),
            source.data[8:16].eq(self.out_g),
            source.data[16:24].eq(self.out_b),
            source.data[24:32].eq(0),
        ]


@ResetInserter()
class ScaleHeight(StallablePipelineActor, MultiTapFilter, AutoCSR):
    def __init__(self, line_length = 640):
        self.sink = sink = Endpoint([("data", 32)])
        self.source = source = Endpoint([("data", 32)])
        n_taps = 4
        n_phase = 128

        StallablePipelineActor.__init__(self, n_taps + 1)
        MultiTapFilter.__init__(self, n_taps, n_phase)

        input_idx = Signal(16)
        line_count = Signal(16)

        first_line = Signal()

        line_end = Signal()
        ports = []
        _outputs = []
        tap_outputs = []

        # delay data
        sink_delayed = [sink.data]
        for i in range(6):
            data_n = Signal(24)
            self.sync += If(self.pipe_ce & self.busy,
                data_n.eq(sink_delayed[-1])
            )
            sink_delayed.append(data_n)

        stall = Signal(n_taps)
        self.sync += [
            If(self.pipe_ce & self.busy,
                stall.eq(Cat(self.stall,stall[:-1]))
            )
        ]

        for i in range(n_taps):
            linebuffer = Memory(24, line_length, name=f'linebuffer{i}')
            self.specials += linebuffer
    
            # Fill line-buffer
            wr = linebuffer.get_port(write_capable=True, mode=READ_FIRST, has_re=True)
            ports += [wr]

            self.specials += wr
            self.comb += [
                wr.adr.eq(input_idx),
                wr.we.eq(self.pipe_ce & self.busy & ~Cat(self.stall,stall[:-1])[i]),
                wr.re.eq(self.pipe_ce & self.busy),
            ]

            # delay output by tap_number
            s = wr.dat_r
            for _ in range(n_taps - i):
                _s = Signal(24)
                self.sync += If(self.pipe_ce & self.busy, _s.eq(s))
                s = _s
                
            _outputs += [s]




        for i in range(n_taps):
            tap_outputs += [Signal(24, name=f'tap_out{i}')]
            self.comb += If(first_line, 
                tap_outputs[i].eq(sink_delayed[5])
            ).Else(
                tap_outputs[i].eq(_outputs[i])
            )
            self.comb += [
                self.filters[i].sink.r.eq(tap_outputs[i][0:8]),
                self.filters[i].sink.g.eq(tap_outputs[i][8:16]),
                self.filters[i].sink.b.eq(tap_outputs[i][16:24]),
            ]

        self.comb += [
            ports[0].dat_w.eq(sink.data)
        ]

        
        for i in range(n_taps-1):
            self.comb += If(first_line, 
                ports[i+1].dat_w.eq(sink_delayed[i+1])
            ).Else(
                ports[i+1].dat_w.eq(ports[i].dat_r)
            )
        

        # Increment input address, along with an address per line
        self.sync += [

            self.phase_ce.eq(0),
            If(self.pipe_ce & self.busy,
                input_idx.eq(input_idx + 1),
                If(input_idx == (line_length - 3),
                    self.phase_ce.eq(1),
                ),
                If(input_idx >= (line_length - 1),
                    input_idx.eq(0),
                    line_count.eq(line_count + 1)
                ),
            )
        ]

        # Load new coefs at the end of each line.
        self.comb += line_end.eq(input_idx == (line_length - 1))
        self.comb += first_line.eq(line_count == 0 | ((line_count == 1) & (input_idx < 4)))
        

        self.comb += [
        ]


        # Connect data into pipeline
        self.comb += [
            source.data[0:8].eq(self.out_r),
            source.data[8:16].eq(self.out_g),
            source.data[16:24].eq(self.out_b),
            source.data[24:32].eq(0),
        ]

@ResetInserter()
class Scaler(Module, AutoCSR):
    def __init__(self,line_length=640):
        self.enable = CSRStorage(1)
        self.sink = sink = Endpoint([("data", 32)])
        self.source = source = Endpoint([("data", 32)])


        self.submodules.height = ScaleHeight(line_length)
        self.submodules.width = ScalerWidth()

        self.submodules.fifo = SyncFIFO([("data", 32)], 8, True)
        

        self.submodules.pipeline = Pipeline(
            sink,
            self.height,
            self.fifo,
            self.width,
            source,
        )




## Unit tests 
import unittest


from litex.soc.interconnect.stream_sim import PacketStreamer, PacketLogger, Packet, Randomizer
from litex.soc.interconnect.stream import Pipeline

from .stream_utils import StreamAppend, StreamPrepend

class TestScaler(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        self.data = [int(math.sin(i/4)*127 + 127) for i in range(16)]
        self.golden = [150, 169, 192, 213, 229, 242, 250, 253, 251, 244, 232, 216, 197, 175, 150, 125, 100, 75, 54, 53]
        unittest.TestCase.__init__(self, methodName=methodName)

    def testWidth(self):
        def generator(dut):
            d = Packet(self.data)
            yield from dut.scaler.phases.write(5)
            yield from dut.scaler.starting_phase.write(1)
            yield dut.scaler.reset.eq(1)
            yield
            yield dut.scaler.reset.eq(0)
            yield
            yield from dut.streamer.send_blocking(d)
        
        def checker(dut):
            yield from dut.logger.receive()
            print(dut.logger.packet)
            assert(self.golden == dut.logger.packet)

        class DUT(Module):
            def __init__(self):
                self.submodules.scaler = ScalerWidth()
                self.sink = Endpoint([("data", 32)])

                self.submodules.streamer = PacketStreamer([("data", 32)])
                self.submodules.logger = PacketLogger([("data", 32)])

                self.submodules.pipeline = Pipeline(
                    self.streamer,
                    self.scaler,
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
        run_simulation(dut, generators, clocks,  vcd_name='test0.vcd')

    def testWidthRandom(self):
        def generator(dut):
            d = Packet(self.data)
            yield from dut.scaler.phases.write(5)
            yield from dut.scaler.starting_phase.write(1)
            yield dut.scaler.reset.eq(1)
            yield
            yield dut.scaler.reset.eq(0)
            yield
            yield from dut.streamer.send_blocking(d)
        
        def checker(dut):
            yield from dut.logger.receive()
            assert(self.golden == dut.logger.packet)

        class DUT(Module):
            def __init__(self):
                self.submodules.scaler = ScalerWidth()
                self.sink = Endpoint([("data", 32)])

                self.submodules.streamer = PacketStreamer([("data", 32)])
                self.submodules.loggerrandomiser = Randomizer([("data", 32)], level=50)
                self.submodules.logger = PacketLogger([("data", 32)])

                self.submodules.pipeline = Pipeline(
                    self.streamer,
                    self.scaler,
                    self.loggerrandomiser,
                    self.logger
                )
                


        dut = DUT()
        generators = {
            "sys" :   [generator(dut),
                      checker(dut),
                      dut.streamer.generator(),
                      dut.logger.generator(),
                      dut.loggerrandomiser.generator()
                      ]
        }
        clocks = {"sys": 10}
        run_simulation(dut, generators, clocks,  vcd_name='test.vcd')


class TestLineBuffer(unittest.TestCase):
    def test0(self):
        self.data = [i for i in range(16)]
        self.data += [0x10 + i for i in range(16)]
        self.data += [0x20 + i for i in range(16)]
        self.data += [0x30 + i for i in range(16)]
        self.data += [0x40 + i for i in range(16)]
        self.data += [0x50 + i for i in range(16)]
        self.data += [0x60 + i for i in range(16)]
        self.data += [0x70 + i for i in range(16)]

        def generator(dut):
            d = Packet(self.data)
            yield dut.scaler.reset.eq(1)
            yield
            yield dut.scaler.reset.eq(0)
            yield

            yield from dut.scaler.phases.write(4)

            yield from dut.streamer.send_blocking(d)
            yield
            yield
            yield
        
        def checker(dut):
            yield from dut.logger.receive()
            print(dut.logger.packet)

            #golden = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43]
            #        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45]

            #assert(dut.logger.packet == golden)

        class DUT(Module):
            def __init__(self):
                self.submodules.scaler = ScaleHeight(line_length=16)
                self.sink = Endpoint([("data", 32)])

                self.submodules.streamer = PacketStreamer([("data", 32)])

                self.submodules.loggerrandomiser = Randomizer([("data", 32)], level=50)
                self.submodules.logger = PacketLogger([("data", 32)])

                self.submodules.pipeline = Pipeline(
                    self.streamer,
                    self.scaler,
                    #self.loggerrandomiser,
                    self.logger
                )
                


        dut = DUT()
        generators = {
            "sys" :   [generator(dut),
                      checker(dut),
                      dut.streamer.generator(),
                      dut.logger.generator(),
                      dut.loggerrandomiser.generator()
                      ]
        }
        clocks = {"sys": 10}
        run_simulation(dut, generators, clocks,  vcd_name='test1.vcd')


class TestCombine(unittest.TestCase):
    def test0(self):
        self.data = [i for i in range(16)]
        self.data += [0x10 + i for i in range(16)]
        self.data += [0x20 + i for i in range(16)]
        self.data += [0x30 + i for i in range(16)]
        self.data += [0x40 + i for i in range(16)]
        self.data += [0x50 + i for i in range(16)]


        def coeff_load(dut, t, p, data, skip):
            yield from dut.coeff_tap.write(t)
            yield from dut.coeff_phase.write(p)
            yield from dut.coeff_data.write(data)
            yield from dut.coeff_stall.write(skip)
            yield from dut.coeff_en.write(1)
            yield from dut.coeff_en.write(0)


        def load_width(dut):
            for i in range(5):
                yield from coeff_load(dut, 1, i, 256, i == 4)


        def load_height(dut):
            for i in range(3):
                yield from coeff_load(dut, 1, i, 256, i == 2)

            
            

        def generator(dut):
            d = Packet(self.data)
            yield dut.scaler.reset.eq(1)
            yield
            yield dut.scaler.reset.eq(0)
            yield
            yield from dut.scaler.width.phases.write(5)
            yield from dut.scaler.height.phases.write(3)
            yield from load_width(dut.scaler.width)
            yield from load_height(dut.scaler.height)
            yield from dut.scaler.width.starting_phase.write(1)

            yield from dut.streamer.send_blocking(d)
            yield
            yield
            yield
        
        def checker(dut):
            yield from dut.logger.receive()
            print(dut.logger.packet)

            
            
            #assert(dut.logger.packet == golden)

        class DUT(Module):
            def __init__(self):
                self.submodules.scaler = Scaler(line_length=16)
                self.sink = Endpoint([("data", 32)])

                self.submodules.streamer = PacketStreamer([("data", 32)])

                self.submodules.loggerrandomiser = Randomizer([("data", 32)], level=50)
                self.submodules.logger = PacketLogger([("data", 32)])

                self.submodules.pipeline = Pipeline(
                    self.streamer,
                    self.scaler,
                    #self.loggerrandomiser,
                    self.logger
                )
                


        dut = DUT()
        generators = {
            "sys" :   [generator(dut),
                      checker(dut),
                      dut.streamer.generator(),
                      dut.logger.generator(),
                      dut.loggerrandomiser.generator()
                      ]
        }
        clocks = {"sys": 10}
        run_simulation(dut, generators, clocks,  vcd_name='test1.vcd')
