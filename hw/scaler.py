# This file is Copyright (c) 2020 Gregory Davill <greg.davill@gmail.com>
# License: BSD

from migen import *
from litex.soc.interconnect.stream import Endpoint
from migen.genlib.cdc import MultiReg
from edge_detect import EdgeDetect

from litex.soc.interconnect.csr import AutoCSR, CSR, CSRStatus, CSRStorage
from litex.soc.interconnect.stream import Endpoint, EndpointDescription, AsyncFIFO

@ResetInserter()
class ScalerWidth(Module, AutoCSR):
    def __init__(self):
        self.sink = sink = Endpoint([("data", 32)])
        self.source = source = Endpoint([("data", 32)])
        

        self.enable = CSRStorage(1)



        counter = Signal(8, reset=0)
        overflow = Signal(1, reset=1)
        overflow_r = Signal(1)

        ce = Signal(4)

        r_next = Signal(32)
        r_last = Signal(32)
        
        offset_r = Signal(8) 
        offset_r0 = Signal(8)  


        offset_red = Signal(8) 
        offset_green = Signal(8) 
        offset_blue = Signal(8) 

        slope_red = Signal(8)
        neg_r = Signal()
        neg_red0 = Signal()
        
        slope_green = Signal(8)
        neg_g = Signal()
        neg_green0 = Signal()
        
        slope_blue = Signal(8)
        neg_b = Signal()
        neg_blue0 = Signal()

        output_r = Signal(8)
        output_g = Signal(8)
        output_b = Signal(8)

        self.sync += [
            If(sink.valid & source.ready,
                Cat(counter, overflow).eq(counter + int(2**len(counter) * (4/5)) + (counter > 0)),

                #Cat(counter, overflow).eq(counter + int(2**len(counter) * (1/2))),
            ),
            overflow_r.eq(overflow),
            ce.eq(Cat(sink.valid,ce[0:3]))
        ]

        self.comb += [
            sink.ready.eq(overflow & source.ready)
        ]


        self.sync += [
            If(source.ready,
                If(sink.ready & sink.valid,
                    r_next.eq(sink.data),
                ),
                r_last.eq(r_next),
            )
            
        ]

        self.sync += [
            If(source.ready,
                If(sink.data[0:8] < r_next[0:8],
                    slope_red.eq(r_next[0:8] - sink.data[0:8]),
                    neg_r.eq(1)
                ).Else(
                    slope_red.eq(sink.data[0:8] - r_next[0:8]),
                    neg_r.eq(0)
                ),
                If(sink.data[8:16] < r_next[8:16],
                    slope_green.eq(r_next[8:16] - sink.data[8:16]),
                    neg_g.eq(1)
                ).Else(
                    slope_green.eq(sink.data[8:16] - r_next[8:16]),
                    neg_g.eq(0)
                ),
                If(sink.data[16:24] < r_next[16:24],
                    slope_blue.eq(r_next[16:24] - sink.data[16:24]),
                    neg_b.eq(1)
                ).Else(
                    slope_blue.eq(sink.data[16:24] - r_next[16:24]),
                    neg_b.eq(0)
                ),
                offset_r.eq(256-counter),
            )
        ]

        self.sync += [
            If(source.ready,
                offset_r0.eq(offset_r),

                neg_red0.eq(neg_r),
                neg_green0.eq(neg_g),
                neg_blue0.eq(neg_b),

                offset_red.eq((offset_r0 * slope_red)[-8:]),
                offset_green.eq((offset_r0 * slope_green)[-8:]),
                offset_blue.eq((offset_r0 * slope_blue)[-8:]),
                
                output_r.eq(r_last[0:8]),
                If((offset_red > 0) & (offset_red < 255),
                    If(neg_red0,
                        output_r.eq((r_last[0:8] + offset_red)),
                    ).Else(
                        output_r.eq((r_last[0:8] - offset_red)),
                    )
                ),
                output_g.eq(r_last[8:16]),
                If((offset_green > 0) & (offset_green < 255),
                    If(neg_green0,
                        output_g.eq((r_last[8:16] + offset_green)),
                    ).Else(
                        output_g.eq((r_last[8:16] - offset_green)),
                    )
                ),
                output_b.eq(r_last[16:24]),
                If((offset_blue > 0) & (offset_blue < 255),
                    If(neg_blue0,
                        output_b.eq((r_last[16:24] + offset_blue)),
                    ).Else(
                        output_b.eq((r_last[16:24] - offset_blue)),
                    )
                )
            )
        ]


#        self.specials += MultiReg((overflow | overflow_r), source.valid, n=3)
        self.comb += [
            source.data.eq(Cat(output_r,output_g,output_b, C(0, 8))),
            source.valid.eq(ce[3]),

        ]

        self.specials += MultiReg(sink.last, source.last, n=4)
        #self.specials += MultiReg(sink.valid, source.valid, n=4)


@ResetInserter()
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

        linebuffer0 = Memory(24, line_length+10, name="linebuffer0")
        self.specials += linebuffer0
        linebuffer1 = Memory(24, line_length+10, name="linebuffer1")
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
            line0.we.eq(sink.valid),
            sink.ready.eq(1),
            NextValue(line0.dat_w,sink.data),
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
            #line1.dat_w.eq(sink.data),
            line1.we.eq(sink.valid),
            sink.ready.eq(1),
            NextValue(line1.dat_w,sink.data),
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

                
                If((out_counter > line_length-1),
                    NextValue(last_ready, 0),
                    NextValue(out_counter, 0),
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
            data = [i*16 for i in range(8)]
            data += reversed(data)
            for i in data:
                yield from write_stream(dut.sink, i)
            
        def logger(dut):
            d = []
            for _ in range(20):
                yield dut.source.ready.eq(1)
                while (yield dut.source.valid == 0):
                    yield 
                d.append((yield dut.source.data))
                    #print(f"{d} > {i}")
                #yield
                yield
            data = [i*16 for i in range(8)]
            data += reversed(data)
            print(data)
            print(d)

                    

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
    

from litex.soc.interconnect.stream_sim import PacketStreamer, PacketLogger, Packet, Randomizer
from litex.soc.interconnect.stream import Pipeline


class Test2(unittest.TestCase):

    def test2(self):
        def generator(dut):
            from PIL import Image

            im0 = Image.open('test0.png')
            
            im_data = list(im0.getdata())
            yield
            yield
            yield
            
            out_data = []
            for line in range(51):
                data = []
                for r,g,b in im_data[line*64:(line+1)*64]:
                    data.append(r | g << 8 | b << 16)
                d = Packet(data)
                yield dut.scaler.reset.eq(1)
                yield
                yield dut.scaler.reset.eq(0)
                yield
                yield from dut.streamer.send_blocking(d)
                yield from dut.logger.receive()
                print(line,len(dut.logger.packet))
                for d in dut.logger.packet[:80]:
                    out_data += [(d & 0x000000FF) >> 0, (d & 0x0000FF00) >> 8, (d & 0x00FF0000) >> 16]
            

            im = Image.frombytes("RGB", (80, 51), bytes(out_data))    
            im = im.resize((800, 510), resample=Image.NEAREST)
            im.save("test_out.png")    

            im0 = im0.resize((80,51), resample=Image.BILINEAR)
            im0 = im0.resize((800,510), resample=Image.NEAREST)
            im0.save("test_out0.png") 
                    
        class DUT(Module):
            def __init__(self):
                self.submodules.scaler = ScalerWidth()
                self.sink = Endpoint([("data", 32)])

                self.submodules.streamer = PacketStreamer([("data", 32)])
                self.submodules.streamer_randomizer = Randomizer([("data", 32)], level=50)
                self.submodules.logger = PacketLogger([("data", 32)])
                self.submodules.logger_randomizer = Randomizer([("data", 32)], level=50)

                self.submodules.pipeline = Pipeline(
                    self.streamer,
                    self.streamer_randomizer,
                    self.scaler,
                    self.logger_randomizer,
                    self.logger
                )
                


        dut = DUT()
        generators = {
            "sys" :   [generator(dut),
                      dut.streamer.generator(),
                      #dut.streamer_randomizer.generator(),
                      dut.logger.generator(),
                      #dut.logger_randomizer.generator()
                      ]
        }
        clocks = {"sys": 10}
        run_simulation(dut, generators, clocks,  vcd_name='test2.vcd')


from litex.build.generic_platform import Pins, Subsignal
from litex.build.sim.platform import SimPlatform
from litex.soc.integration.builder import Builder

_io = [
    # Wishbone
    ("sink", 0,
        Subsignal("payload", Pins(32)),
        Subsignal("data", Pins(32)),
        Subsignal("valid",   Pins(1)),
        Subsignal("ready", Pins(1)),
        Subsignal("last",   Pins(1)),
        Subsignal("first",   Pins(1)),
    ),
    ("source", 0,
        Subsignal("payload", Pins(32)),
        Subsignal("data", Pins(32)),
        Subsignal("valid",   Pins(1)),
        Subsignal("ready", Pins(1)),
        Subsignal("last",   Pins(1)),
        Subsignal("first",   Pins(1)),
    ),
    
    ("clk", 0, Pins(1)),
    ("rst", 0, Pins(1)),
]

class DUT(Module):
    def __init__(self, p):
        self.submodules.scaler0 = ScalerWidth()
        self.submodules.scaler1 = ScalerHeight()
        
        sink = p.request("sink")
        source = p.request("source")

        self.submodules.pipeline = pipe = Pipeline(
            self.scaler0,
            self.scaler1,
            
        )

        self.comb += [
            pipe.sink.data.eq(sink.data),
            sink.ready.eq(pipe.sink.ready),
            pipe.sink.valid.eq(sink.valid),
            pipe.sink.last.eq(sink.last),
        ]

        self.comb += [
            source.data.eq(pipe.source.data),
            source.valid.eq(pipe.source.valid),
            source.last.eq(pipe.source.last),
            pipe.source.ready.eq(source.ready),
        ]

        rst = p.request("rst")
        self.comb += [self.scaler1.reset.eq(rst)]
        self.comb += [self.scaler0.reset.eq(rst)]

        


class Platform(SimPlatform):
    default_clk_name = "clk"
    def __init__(self, toolchain="verilator"):
        SimPlatform.__init__(self, "sim", _io, [], toolchain="verilator")

    def create_programmer(self):
        raise ValueError("programming is not supported")

def generate():
    platform = Platform()
    soc = DUT(platform)
    #output = verilog.convert(soc.get_fragment())

    platform.build(soc, build=True, run=False)



if __name__ == "__main__":

    import os
    import subprocess
    
    path = os.getcwd()

    generate()

    
    root = os.path.join("build")
    verilog_file = os.path.join(root, "sim.v")
    cxxrtl_file = os.path.join(root, "top.cc")
    filename = os.path.join(root, "top.cpp")
    elfname = os.path.join(root, "top.elf")

    os.chdir(path)
    print(subprocess.check_call(["yosys", verilog_file, "-o", cxxrtl_file]))

    with open(filename, "w") as f:
        f.write(r"""
#include <iostream>
#include <fstream>
#include "SDL2/SDL.h"

#include "top.cc"

#include <backends/cxxrtl/cxxrtl_vcd.h>

int main()
{
const int width = 800;
const int height = 600;
const int bpp = 3;

static uint8_t pixels[width * height * bpp];

int frames = 0;
unsigned int lastTime = 0;
unsigned int currentTime;

// Set this to 0 to disable vsync
unsigned int flags = 0;

if(SDL_Init(SDL_INIT_VIDEO) != 0) {
    fprintf(stderr, "Could not init SDL: %s\n", SDL_GetError());
    return 1;
}
SDL_Window *screen = SDL_CreateWindow("cxxrtl",
        SDL_WINDOWPOS_UNDEFINED,
        SDL_WINDOWPOS_UNDEFINED,
        width, height,
        0);
if(!screen) {
    fprintf(stderr, "Could not create window\n");
    return 1;
}
SDL_Renderer *renderer = SDL_CreateRenderer(screen, -1, flags);
if(!renderer) {
    fprintf(stderr, "Could not create renderer\n");
    return 1;
}

SDL_Texture* framebuffer = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_RGB24, SDL_TEXTUREACCESS_STREAMING, width, height);

cxxrtl_design::p_sim top;

cxxrtl::debug_items debug;
top.debug_info(debug);

cxxrtl::vcd_writer vcd;
vcd.timescale(1,"us");
vcd.add_without_memories(debug);

std::ofstream waves("waves.vcd");

int steps = 0;
bool logging = true;


for (int i = 0; i < 500; i++) {
    size_t ctr = 0;
    value<1> old_vs{0u};
    // Render one frame
        unsigned int pixels_in = 0;
    for(int j = 0; j < (650); j++) {
        unsigned int pixels_out = 0;

        for(int k = 0; k < (850); k++) {
        
            top.p_rst = value<1>{0u};
            if(j == 649 & k > 840)
                top.p_rst = value<1>{1u};


        if(logging){
            top.p_clk = value<1>{1u};
            top.step();
            vcd.sample(steps++);
            
            // Inofficial cxxrtl hack that improves performance
            top.p_clk = value<1>{0u};
            top.step();

            vcd.sample(steps++);

            waves << vcd.buffer;
            vcd.buffer.clear();
        }else{
            //top.prev_p_clk = value<1>{0u};
            //top.p_clk = value<1>{1u};
            //top.step();


            top.p_clk = value<1>{1u};
            top.step();

            top.p_clk = value<1>{0u};
            top.step();
        }
        
        


        
        if(top.p_sink__ready.curr){
            pixels_in++;

        }

        top.p_sink__valid = value<1>{0u};
        if(pixels_in < (640*512)){
            top.p_sink__valid = value<1>{1u};
            top.p_sink__data.set((unsigned int)(pixels_in % 640 + (pixels_in / 640)*2));

        }


        top.p_source__ready = value<1>{0u};
        //}

        if(k >= 10 && k < 810 && j < 602 && j >= 2){ 
            top.p_source__ready = value<1>{1u}; 
        if (top.p_source__valid.curr) {
            if(ctr > (600*800*3)){
                std::cout << ctr << std::endl;
            }else {
                uint32_t d = (uint32_t) top.p_source__data.curr.get<uint32_t>();

                pixels_out++;

                //std::cout << d;

                pixels[ctr++] = d & 0xFF;
                pixels[ctr++] = (d >> 8) & 0xFF;
                pixels[ctr++] = (d >> 16) & 0xFF;
            }
        }
        }

        // Break when vsync goes low again
        // if (old_vs && !top.p_vga__output____vs)
        //     break;
        // old_vs = top.p_vga__output____vs;
        }

        //std::cout << pixels_out << pixels_in << std::endl;
    }


    logging = false;

    SDL_UpdateTexture(framebuffer, NULL, pixels, width * bpp);
    SDL_RenderCopy(renderer, framebuffer, NULL, NULL);
    SDL_RenderPresent(renderer);

    SDL_Event event;
    if (SDL_PollEvent(&event)) {
        if (event.type == SDL_KEYDOWN)
            break;
    }

    // SDL_Delay(10);

    frames++;

    currentTime = SDL_GetTicks();
    float delta = currentTime - lastTime;
    if (delta >= 1000) {
        std::cout << "FPS: " << (frames / (delta / 1000.0f)) << std::endl;
        lastTime = currentTime;
        frames = 0;
    }
}


SDL_DestroyWindow(screen);
SDL_Quit();
return 0;
}

        """)
        f.close()

    print(subprocess.check_call([
        "clang++", "-I", "/usr/local/share/yosys/include", "-I", "/usr/include/SDL2",
        "-O3", "-fno-exceptions", "-std=c++11", "-lSDL2", "-o", elfname, filename]))

    print(subprocess.check_call([elfname]))

