from migen import *

class HDMI(Module):
    def __init__(self, platform, pins):

        platform.add_source('hdl/fake_differential.v')
        platform.add_source('hdl/vga2dvid.v')
        platform.add_source('hdl/vga.v')
        platform.add_source('hdl/tmds_encoder.v')

        vga_r, vga_g, vga_b = Signal(8), Signal(8), Signal(8)
        vga_hsync, vga_vsync, vga_blank = Signal(), Signal(), Signal()
        
        self.specials += Instance(
            'vga',
            p_C_resolution_x=      1920,
            p_C_hsync_front_porch= 88,
            p_C_hsync_pulse=       44,
            p_C_hsync_back_porch=  133, # our adjustment for 75 MHz pixel clock
            p_C_resolution_y=      1080,
            p_C_vsync_front_porch= 4,
            p_C_vsync_pulse=       5,
            p_C_vsync_back_porch=  46, # our adjustment for 75 MHz pixel clock
            p_C_bits_x=            12,
            p_C_bits_y=            11,
            i_clk_pixel=ClockSignal('sys'),
            i_test_picture=0,
            o_vga_r=vga_r,
            o_vga_g=vga_g,
            o_vga_b=vga_b,
            o_vga_hsync=vga_hsync,
            o_vga_vsync=vga_vsync,
            o_vga_blank=vga_blank
        )

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
            i_clk_pixel=ClockSignal('sys'),
            i_clk_shift=ClockSignal('shift'),
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
            i_clk_shift=ClockSignal('shift'),
            i_in_clock=tmds[3],
            i_in_red=tmds[2],
            i_in_green=tmds[1],
            i_in_blue=tmds[0],
            o_out_p=pins.p,
            o_out_n=pins.n,

            i_move=0,
            i_loadn=0,
            i_dir=1,
        )