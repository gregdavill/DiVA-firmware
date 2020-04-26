from migen import *
import orangecrab

from litex.soc.cores.clock import ECP5PLL

import os
import shutil
from hdmi import HDMI
from gen import Generator
from litevideo.terminal.core import Terminal
from stream_gen import StreamGenerator

class PWMFade(Module):
    def __init__(self, platform):


        clk48 = platform.request("clk48")

        pixel_clock = 75e6
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_shift = ClockDomain()
        
        self.submodules.pll = pll = ECP5PLL()
        pll.register_clkin(clk48, 48e6)
        pll.create_clkout(self.cd_sys, pixel_clock, margin=0)
        pll.create_clkout(self.cd_shift, pixel_clock * 5, margin=0)
        
        ## HDMI output 
        hdmi_pins = platform.request('hdmi')
        self.submodules.hdmi = hdmi =  HDMI(platform, hdmi_pins)

        ## Create VGA terminal
        #mem_map["terminal"] = 0x30000000
        self.submodules.terminal = terminal = ClockDomainsRenamer({'vga':'sys'})(Terminal())
        #self.add_wb_slave(mem_decoder(0x30000000), self.terminal.bus)
        #self.add_memory_region("terminal", 0x30000000, 0x10000)

        self.submodules.generator = generator = Generator()

        self.submodules.streamgen = sg = StreamGenerator()

        ## Connect VGA pins
        self.comb += [
            hdmi.vsync.eq(terminal.vsync),
            hdmi.hsync.eq(terminal.hsync),
            hdmi.blank.eq(terminal.blank),
            hdmi.r.eq(terminal.red),
            hdmi.g.eq(terminal.green),
            hdmi.b.eq(terminal.blue),
#
            generator.bus.connect(terminal.bus),
#
            sg.source.connect(generator.sink)
        ]

if __name__ == "__main__":
    import sys

    platform = orangecrab.Platform()

    pwm_fade = PWMFade(platform)
    platform.build(pwm_fade, build_dir='build')
    os.system(f'ecppack build/top.config --compress --bit build/top.bit --svf build/top.svf')
    shutil.copyfile('build/top.bit', 'build/top.dfu')
    os.system('dfu-suffix -v 1209 -p 5bf0 -a build/top.dfu')
    #os.system("dfu-util -d 1d50:614b --alt 2 --download build_lcd/top.bit -R")
    #platform.create_programmer().flash(0, 'build/top.bin')