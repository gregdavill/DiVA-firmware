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
        self.coef = coef = Signal((12,True))

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
        self.coef = coef = Signal((12,True))

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


@ResetInserter()
class ScalerWidth(StallablePipelineActor, AutoCSR):
    def __init__(self):
        self.sink = sink = Endpoint([("data", 32)])
        self.source = source = Endpoint([("data", 32)])
        StallablePipelineActor.__init__(self, 5)

        filters = [
            RGBFilterElement(), 
            RGBFilterElement(), 
            RGBFilterElement(),
            RGBFilterElement(),
            RGBFilterElement(),
        ]
        for f in filters:
            self.submodules += f
            self.comb += f.ce.eq(self.pipe_ce)


        def coef(value, cw=None):
            return int(value * 2**cw) if cw is not None else value
        for i in range(5):
            d = []
            for p in range(5):
                name = f'filter_coeff_tap{i}_phase{p}'
                d = coef(W((float(4-i) + float(p)*0.2)-2.0), 8)
                #print(name, d)
                csr = CSRStorage(16, name=name, reset=d)
                setattr(self, name, csr) 

        self.enable = CSRStorage(1)
        self.phases = phases = CSRStorage(8)
        self.starting_phase = starting_phase = CSRStorage(8)

        self.phase = phase = Signal(8, reset=0)

        self.submodules.tap_datapath = tap_dp = MultiTapDatapath(5)
        self.comb += self.tap_datapath.ce.eq(self.pipe_ce & ~self.stall)

        self.sync += [
            If(self.pipe_ce & self.busy,
                phase.eq(phase + 1),
                If(phase >= (phases.storage - 1),
                    phase.eq(0),
                ),
            ),
        ]

        self.comb += self.stall.eq(phase == 4)
        
        for i in range(5):
            self.comb += filters[i].sink.eq(tap_dp.tap[i])

        self.comb += [
                
            If(phase == 0, 
                filters[0].coef.eq(self.filter_coeff_tap0_phase0.storage),
                filters[1].coef.eq(self.filter_coeff_tap1_phase0.storage),
                filters[2].coef.eq(self.filter_coeff_tap2_phase0.storage),
                filters[3].coef.eq(self.filter_coeff_tap3_phase0.storage),
                filters[4].coef.eq(self.filter_coeff_tap4_phase0.storage),
            ),
            If(phase == 1, 
                filters[0].coef.eq(self.filter_coeff_tap0_phase1.storage),
                filters[1].coef.eq(self.filter_coeff_tap1_phase1.storage),
                filters[2].coef.eq(self.filter_coeff_tap2_phase1.storage),
                filters[3].coef.eq(self.filter_coeff_tap3_phase1.storage),
                filters[4].coef.eq(self.filter_coeff_tap4_phase1.storage),
            ),
            If(phase == 2, 
                filters[0].coef.eq(self.filter_coeff_tap0_phase2.storage),
                filters[1].coef.eq(self.filter_coeff_tap1_phase2.storage),
                filters[2].coef.eq(self.filter_coeff_tap2_phase2.storage),
                filters[3].coef.eq(self.filter_coeff_tap3_phase2.storage),
                filters[4].coef.eq(self.filter_coeff_tap4_phase2.storage),
            ),
            If(phase == 3, 
                filters[0].coef.eq(self.filter_coeff_tap0_phase3.storage),
                filters[1].coef.eq(self.filter_coeff_tap1_phase3.storage),
                filters[2].coef.eq(self.filter_coeff_tap2_phase3.storage),
                filters[3].coef.eq(self.filter_coeff_tap3_phase3.storage),
                filters[4].coef.eq(self.filter_coeff_tap4_phase3.storage),
            ),
            If(phase == 4, 
                filters[0].coef.eq(self.filter_coeff_tap0_phase4.storage),
                filters[1].coef.eq(self.filter_coeff_tap1_phase4.storage),
                filters[2].coef.eq(self.filter_coeff_tap2_phase4.storage),
                filters[3].coef.eq(self.filter_coeff_tap3_phase4.storage),
                filters[4].coef.eq(self.filter_coeff_tap4_phase4.storage),
            ),
        ]

        out_r = Signal(24)
        self.sync += [
            If(self.pipe_ce & self.busy,
                out_r.eq(
                    filters[0].source.r +
                    filters[1].source.r +
                    filters[2].source.r +
                    filters[3].source.r +
                    filters[4].source.r),
            )
        ]

        out_r_bitnarrow = Signal(8)
        self.comb += [
            If(out_r[-1] == 1,
                out_r_bitnarrow.eq(0),  # Saturate negative values to 0
            ).Elif(out_r[8:] > 255,
                out_r_bitnarrow.eq(255),
            ).Else(
                out_r_bitnarrow.eq(out_r[8:]),
            )
        ]

        out_g = Signal(24)
        self.sync += [
            If(self.pipe_ce & self.busy,
                out_g.eq(
                    filters[0].source.g +
                    filters[1].source.g +
                    filters[2].source.g +
                    filters[3].source.g +
                    filters[4].source.g),
            )
        ]

        out_g_bitnarrow = Signal(8)
        self.comb += [
            If(out_g[-1] == 1,
                out_g_bitnarrow.eq(0),  # Saturate negative values to 0
            ).Elif(out_g[8:] > 255,
                out_g_bitnarrow.eq(255),
            ).Else(
                out_g_bitnarrow.eq(out_g[8:]),
            )
        ]

        out_b = Signal(24)
        self.sync += [
            If(self.pipe_ce & self.busy,
                out_b.eq(
                    filters[0].source.b +
                    filters[1].source.b +
                    filters[2].source.b +
                    filters[3].source.b +
                    filters[4].source.b),
            )
        ]

        out_b_bitnarrow = Signal(8)
        self.comb += [
            If(out_b[-1] == 1,
                out_b_bitnarrow.eq(0),  # Saturate negative values to 0
            ).Elif(out_b[8:] > 255,
                out_b_bitnarrow.eq(255),
            ).Else(
                out_b_bitnarrow.eq(out_b[8:]),
            )
        ]

        self.comb += [
            self.tap_datapath.sink.r.eq(sink.data[0:8]),
            source.data[0:8].eq(out_r_bitnarrow),
            self.tap_datapath.sink.g.eq(sink.data[8:16]),
            source.data[8:16].eq(out_g_bitnarrow),
            self.tap_datapath.sink.b.eq(sink.data[16:24]),
            source.data[16:24].eq(out_b_bitnarrow),
            source.data[24:32].eq(0),
        ]
        

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

