from migen import *

class HDMI(Module):
    def __init__(self, platform, pins):

        platform.add_source('rtl/verilog/fake_differential.v')
        platform.add_source('rtl/verilog/vga2dvid.v')
        platform.add_source('rtl/verilog/tmds_encoder.v')

        self.r = vga_r = Signal(8)
        self.g = vga_g = Signal(8)
        self.b = vga_b = Signal(8)
        self.hsync = vga_hsync = Signal()
        self.vsync = vga_vsync = Signal()
        self.blank = vga_blank = Signal()

        tmds = [Signal(2) for i in range(4)]
        self.specials += Instance(
            'vga2dvid',
            p_C_ddr=1,
            i_clk_pixel=ClockSignal('video'),
            i_clk_shift=ClockSignal('video_shift'),
            i_in_red=vga_r,
            i_in_green=vga_g,
            i_in_blue=vga_b,
            i_in_hsync=vga_hsync,
            i_in_vsync=vga_vsync,
            i_in_blank=vga_blank,
            o_out_clock=tmds[3],
            o_out_red=tmds[2],
            o_out_green=tmds[1],
            o_out_blue=tmds[0]
        )


        self.specials += Instance(
            'fake_differential',
            p_C_ddr=1,
            i_clk_shift=ClockSignal('video_shift'),
            i_in_clock=tmds[3],
            i_in_red=tmds[2],
            i_in_green=tmds[1],
            i_in_blue=tmds[0],
            o_out_p=pins.p,
            #o_out_n=pins.n,

            i_move=0,
            i_loadn=0,
            i_dir=1,
        )