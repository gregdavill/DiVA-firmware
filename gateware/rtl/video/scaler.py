# This file is Copyright (c) 2020 Gregory Davill <greg.davill@gmail.com>
# License: BSD

from migen import *
from litex.soc.interconnect.stream import Endpoint

from litex.soc.interconnect.csr import AutoCSR, CSRStorage
from litex.soc.interconnect.stream import Endpoint

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
        self.output_hold = Signal()
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
            source.valid.eq(valid & ~self.output_hold),
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

        self.bank = Signal()

        self.coeff_data = CSRStorage(32)
        cfg_coeff_stall = self.coeff_data.storage[31]
        cfg_coeff_bank = self.coeff_data.storage[30]
        cfg_coeff_tap = self.coeff_data.storage[24:30]
        cfg_coeff_phase = self.coeff_data.storage[16:24]
        cfg_coeff_dat = self.coeff_data.storage[0:10]

        
        _coeff_data_we_ps = PulseSynchronizer('cpu', 'sys')
        self.comb += _coeff_data_we_ps.i.eq(self.coeff_data.re)
        self.submodules += _coeff_data_we_ps

        coeff_memory = Memory(10*n_taps + 1, n_phase * 2)
        self.specials += coeff_memory

        coeff_memory_we_port = coeff_memory.get_port(write_capable=True)

        # Give CSR storage time to load, and then coeff_memory a cycle to have dat_r prepared
        self.comb += [
            coeff_memory_we_port.we.eq(_coeff_data_we_ps.o),
            If(cfg_coeff_bank,
               coeff_memory_we_port.adr.eq(cfg_coeff_phase + n_phase),
            ).Else(
               coeff_memory_we_port.adr.eq(cfg_coeff_phase),
            )
        ]

        for i in range(n_taps):
            self.comb += If(cfg_coeff_tap == i,
                    coeff_memory_we_port.dat_w.eq(coeff_memory_we_port.dat_r),
                    coeff_memory_we_port.dat_w[i*10:(i+1)*10].eq(cfg_coeff_dat),
                    coeff_memory_we_port.dat_w[-1].eq(cfg_coeff_stall),
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
            If(self.bank,
                coeff_memory_port.adr.eq(phase + n_phase),
            ).Else(
                coeff_memory_port.adr.eq(phase),
            )
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




class ScalerWidth(StallablePipelineActor, MultiTapFilter, AutoCSR):
    def __init__(self):
        self.sink = sink = Endpoint([("data", 32)])
        self.source = source = Endpoint([("data", 32)])
        n_taps = 3
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


class ScaleHeight(StallablePipelineActor, MultiTapFilter, AutoCSR):
    def __init__(self, line_length = 640):
        self.sink = sink = Endpoint([("data", 32)])
        self.source = source = Endpoint([("data", 32)])

        n_taps = 3
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
            self.comb += tap_outputs[i].eq(_outputs[i])
            self.comb += [
                self.filters[i].sink.r.eq(tap_outputs[i][0:8]),
                self.filters[i].sink.g.eq(tap_outputs[i][8:16]),
                self.filters[i].sink.b.eq(tap_outputs[i][16:24]),
            ]

        self.comb += [
            ports[0].dat_w.eq(sink.data),
            self.output_hold.eq(first_line)
        ]

        
        for i in range(n_taps-1):
            self.comb += If(first_line & (i == 0), 
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
        self.comb += first_line.eq((line_count == 0) | ((line_count == 1) & (input_idx < 4)))
        

        self.comb += [
        ]


        # Connect data into pipeline
        self.comb += [
            source.data[0:8].eq(self.out_r),
            source.data[8:16].eq(self.out_g),
            source.data[16:24].eq(self.out_b),
            source.data[24:32].eq(0),
        ]

class Scaler(Module, AutoCSR):
    def __init__(self,line_length=640):
        self.sink = sink = Endpoint([("data", 32)])
        self.source = source = Endpoint([("data", 32)])

        self.submodules.height = ScaleHeight(line_length)
        self.submodules.width = ScalerWidth()
        self.submodules.fifo = SyncFIFO([("data", 32)], 8, True)

        # Filter coeff bank selection
        self.bank = bank = Signal()
        self.comb += [
            self.height.bank.eq(bank),
            self.width.bank.eq(bank),
        ]
        

        self.submodules.pipeline = Pipeline(
            sink,
            self.height,
            self.fifo,
            self.width,
            source,
        )
