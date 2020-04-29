#!/usr/bin/env python3
import sys
import os

from migen import *
from migen.genlib.cdc import MultiReg

from pycrc.algorithms import Crc

from litex.soc.interconnect import stream
from litex.soc.interconnect.stream import EndpointDescription



from struct import unpack, pack_into

class boson_rx(Module):
    def __init__(self, pads):
        self.source = source = stream.Endpoint(EndpointDescription([("data", 24)]))
        self.sync_out = Signal()
        

        vsync_ = Signal()
        vsync_falling = Signal()
        bypass = Signal(reset=1)

        data = Signal(24)
        
        luminance_delay = Signal(8)
        
        valid = Signal(2)
        pixel_en = Signal(2)


        pixel_counter = Signal(max=(450000*4))
        alignment = 750*120 + 100
        
        self.comb += [
            source.data.eq(data),
            source.valid.eq((~bypass) & (valid[1])),
        ]

        self.comb += [
            vsync_falling.eq(~pads.vsync & vsync_)
        ]


        self.sync += [

            luminance_delay.eq(pads.data[0:8]),
            data[0:8].eq(luminance_delay),
            If(~pixel_counter[0],        
                 data[8:16].eq(pads.data[8:16]),
            #    data[0:12].eq(pads.data[0:12]),
            ).Else (
                 data[16:24].eq(pads.data[8:16]),
            #    data[12:24].eq(pads.data[0:12]),
            ),
            #pixel_en.eq(Cat(pads.valid, valid)
            #data.eq(pads.data[0:15]),
            
            valid.eq(Cat(pads.valid, valid[0]))
        ]

        self.sync += [
            vsync_.eq(pads.vsync),

            If(vsync_falling,
                pixel_counter.eq(0),
                bypass.eq(0)
            ).Else(
                pixel_counter.eq(pixel_counter + 1)
            ),
            self.sync_out.eq(0),
            If((pixel_counter >= alignment) & (pixel_counter < (alignment+9)),
                self.sync_out.eq(1)
            )
        ]



# Convert the Boson clock pin Signal into a clock domain
class boson_clk(Module):
    def __init__(self, clk_pad):
        self.clock_domains.cd_boson_rx = ClockDomain()        
        self.comb += self.cd_boson_rx.clk.eq(clk_pad)


class Boson(Module):
    def __init__(self, platform, pads):
        

        
        self.submodules.clk = boson_clk(pads.clk)
        self.submodules.rx = ClockDomainsRenamer("boson_rx")(boson_rx(pads))
        self.source = self.rx.source

        
        #self.sync_out = Signal()
        #reg_sync = MultiReg(self.rx.sync_out, self.sync_out)
        #self.specials += reg_sync


        #self.submodules.conf = ClockDomainsRenamer("clk25")(BosonConfig(pads))

    
