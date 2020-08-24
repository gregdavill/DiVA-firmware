# This file is Copyright (c) 2020 Gregory Davill <greg.davill@gmail.com>
# License: BSD

from migen import *
from litex.soc.interconnect.stream import Endpoint
from migen.genlib.cdc import MultiReg
from edge_detect import EdgeDetect

from litex.soc.interconnect.csr import AutoCSR, CSR, CSRStatus, CSRStorage
from litex.soc.interconnect.stream import Endpoint, EndpointDescription, AsyncFIFO

class ScalerWidth(Module, AutoCSR):
    def __init__(self):
        self.sink = sink = Endpoint([("data", 32)])
        self.source = source = Endpoint([("data", 32)])
        

        self.enable = CSRStorage(1)



        counter = Signal(8, reset=0xCC)
        overflow = Signal(1, reset=1)
        overflow_r = Signal(1)

        ce = Signal()
        ce_r = Signal()
        ce_x = Signal()
        ce_x1 = Signal()
        

        r_next = Signal(32)
        r_last = Signal(32)
        
        base_x = Signal(32)
        offset_x = Signal(16)        
        offset_r = Signal(8)        
        slope_red = Signal(9)

        output_r = Signal(8)
        output_g = Signal(8)
        output_b = Signal(8)

        self.sync += [
            If(sink.valid & source.ready,
                Cat(counter, overflow).eq(counter + int(2**len(counter) * (4/5)) + (counter > 0)),
            ),
            overflow_r.eq(overflow),
        ]

        self.comb += [
            sink.ready.eq(overflow & source.ready)
        ]


        self.sync += [
            If(source.ready,
                ce.eq(0),
                If(sink.ready & sink.valid,
                    r_next.eq(sink.data),
                    ce.eq(1),
                ),
                r_last.eq(r_next),
                ce_r.eq(ce),
                ce_x.eq(ce_r),
                ce_x1.eq(ce_x),
            )
            
        ]

        self.sync += [
            If(source.ready,
                slope_red.eq(sink.data[0:8] - r_next[0:8]) 
            )
        ]

        self.sync += [
            If(source.ready,
            #    offset_r.eq(counter),
                
            #    offset_x.eq(offset_r * slope_red),
                base_x.eq(r_last),

                output_r.eq(base_x[0:8]),
                output_g.eq(base_x[8:16]),
                output_b.eq(base_x[16:24]),
            )
        ]


#        self.specials += MultiReg((overflow | overflow_r), source.valid, n=3)
        self.comb += [
            source.valid.eq(ce_x | ce_x1),
            source.data.eq(Cat(output_r,output_g,output_b, C(0, 8)))

        ]



class ScalerHeight(Module, AutoCSR):
    def __init__(self, line_length=800):
        self.sink = sink = Endpoint([("data", 32)])
        self.source = source = Endpoint([("data", 32)])

        line_counter = Signal(12)
        out_counter = Signal(12)
        delay_counter = Signal(12)

        counter = Signal(12)
        overflow = Signal()

        


        out0_set = Signal()
        out1_set = Signal()

        out0_clr = Signal()
        out1_clr = Signal()

        out0_full = Signal()
        out1_full = Signal()


        repeat_set = Signal()
        repeat_clr = Signal()
        repeat = Signal()
        
        pingpong = Signal()

        linebuffer0 = Memory(24, line_length, name="linebuffer0")
        self.specials += linebuffer0
        linebuffer1 = Memory(24, line_length, name="linebuffer1")
        self.specials += linebuffer1

        line0 = linebuffer0.get_port(write_capable=True)
        self.specials += line0
        line1 = linebuffer1.get_port(write_capable=True)
        self.specials += line1


        self.sync += [
            If(out0_set, out0_full.eq(1)),
            If(out0_clr, out0_full.eq(0)),
            If(out1_set, out1_full.eq(1)),
            If(out1_clr, out1_full.eq(0)),
            If(repeat_set, repeat.eq(1)),
            If(repeat_clr, repeat.eq(0)),
        ]

        self.submodules.fsm_in = fsm_in = FSM(reset_state="WAIT")
        self.submodules.fsm_out = fsm_out = FSM(reset_state="WAIT")

        fsm_in.act("WAIT",
            NextValue(line_counter,0),
            If(~out0_full & ~fsm_out.ongoing("OUT0"),
                NextState("FILL0"),
            ).Elif(~out1_full & ~fsm_out.ongoing("OUT1"),
                NextState("FILL1"),
            ),
        )

        fsm_in.act("FILL0",

            line0.adr.eq(line_counter),
            line0.dat_w.eq(sink.data),
            line0.we.eq(sink.valid),
            sink.ready.eq(1),
            NextValue(line_counter, line_counter + sink.valid),

            If(line_counter >= line_length -1,
                NextState("WAIT"),
                NextValue(line_counter,0),
                out0_set.eq(1),
                NextValue(Cat(counter, overflow),counter + int(2**len(counter) * (64/75))),
                If(~overflow,
                    repeat_set.eq(1),
                    NextValue(Cat(counter),counter + 2 * int(2**len(counter) * (64/75))),
                    NextValue(overflow, 1)
                )
            )
        )

        fsm_in.act("FILL1",

            line1.adr.eq(line_counter),
            line1.dat_w.eq(sink.data),
            line1.we.eq(sink.valid),
            sink.ready.eq(1),
            NextValue(line_counter, line_counter + sink.valid),

            If(line_counter >= line_length - 1 ,
                NextState("WAIT"),
                NextValue(line_counter,0),
                out1_set.eq(1),
                NextValue(Cat(counter, overflow),counter + int(2**len(counter) * (64/75))),
                If(~overflow,
                    repeat_set.eq(1),
                    NextValue(Cat(counter),counter + 2 * int(2**len(counter) * (64/75))),
                    NextValue(overflow, 1)
                )
            )
        )



        # Output 

        last_ready = Signal()

        fsm_out.act("WAIT",
            NextValue(last_ready, 0),
            If(out0_full,
                NextValue(out_counter,0),
                NextState("OUT0"),
            ).Elif(out1_full,
                NextValue(out_counter,0),
                NextState("OUT1"),
            )
        )

        def out_state(linebuffer_port, clr_flag, state_name):
            return [ 
                NextValue(last_ready, 1),
                linebuffer_port.adr.eq(out_counter + source.ready),
                source.data.eq(linebuffer_port.dat_r),
                If(source.ready,
                    NextValue(out_counter, out_counter + 1),
                ),
                source.valid.eq(last_ready),

                
                If((out_counter >= line_length-1),
                    NextValue(last_ready, 0),
                    NextValue(out_counter, 0),
                    #NextState(state_name),
                    repeat_clr.eq(1),
                    If(~repeat,
                        clr_flag.eq(1),
                        NextState("WAIT"),
                    )
                )
            ]

        fsm_out.act("OUT0",
            out_state(line0, out0_clr, "OUT0")
        )

        fsm_out.act("OUT1",
            out_state(line1, out1_clr, "OUT1")    
        )



## Unit tests 


import unittest

def write_stream(stream, dat):
    yield stream.data.eq(dat)
    yield stream.valid.eq(1)
    yield
    while (yield stream.ready == 0):
        yield 
    
    yield stream.data.eq(0)
    yield stream.valid.eq(0)

class Test0(unittest.TestCase):

    def test0(self):
        def generator(dut):
            data = [0x00, 0x80, 0x00, 0x80, 0x00, 0x80, 0x00, 0x80]
            data = [i for i in range(8)]
            for i in data:
                yield from write_stream(dut.sink, i)
            
        def logger(dut):
            for _ in range(16):
                yield dut.source.ready.eq(1)
                yield
                #yield dut.source.ready.eq(0)
                yield
                    

        dut = ScalerWidth()
        run_simulation(dut, [generator(dut), logger(dut)], vcd_name='test0.vcd')
    

class Test1(unittest.TestCase):

    def test1(self):
        def generator(dut):
            data = [i for i in range(600)]
            for i in data:
                yield from write_stream(dut.sink, i)
            
        def logger(dut):
            for _ in range(60):
                yield dut.source.ready.eq(0)
                for _ in range(20):
                    yield

                d = []
                for i in range(10):
                    yield dut.source.ready.eq(1)
                    yield
                    d.append((yield dut.source.data))
                    #print(f"{d} > {i}")
                #yield
                print(d)
                #print([i for i in range(10)])
                
                #assert(d == [i for i in range(10)])
                #for i in range(10):
                    

        dut = ScalerHeight(10)
        run_simulation(dut, [generator(dut), logger(dut)], vcd_name='test1.vcd')
    