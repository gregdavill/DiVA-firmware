#!/usr/bin/env python3
import sys
import os

from migen import *
from migen.genlib.cdc import MultiReg

from litex.soc.interconnect import stream
from litex.soc.interconnect.stream import EndpointDescription

from litex.soc.cores import uart
from rtl.ecp5_dynamic_pll import period_ns

from litex.soc.interconnect.csr import AutoCSR



class boson_rx(Module):
    def __init__(self, pads):
        self.source = source = stream.Endpoint(EndpointDescription([("data", 24)]))
        

        vsync_ = Signal()
        vsync_falling = Signal()

        data = Signal(24)
        
        luminance_delay = Signal(8)
        
        valid = Signal(2)


        pixel_counter = Signal(20)
        
        self.sync += [
            source.data.eq(data),
            source.valid.eq(valid[1]),
        ]

        self.comb += [
            vsync_falling.eq(~pads.vsync & vsync_),
        ]


        self.sync += [
        #    source.data.eq(pads.data),
        #    source.valid.eq(pads.valid)

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
            ).Else(
                pixel_counter.eq(pixel_counter + 1)
            ),
           
        ]



# Convert the Boson clock pin Signal into a clock domain
class boson_clk(Module):
    def __init__(self, clk_pad, platform):
        self.clock_domains.cd_boson_rx = ClockDomain()        
        self.comb += self.cd_boson_rx.clk.eq(clk_pad)
        
        platform.add_period_constraint(self.cd_boson_rx.clk, period_ns(27e6))


class Boson(Module, AutoCSR):
    def __init__(self, platform, pads, clk_freq):
        self.submodules.clk = boson_clk(pads.clk, platform)
        self.submodules.rx = ClockDomainsRenamer("boson_rx")(boson_rx(pads))
        self.source = self.rx.source
        
        self.hsync = pads.hsync
        self.vsync = pads.vsync
        self.data_valid = pads.valid

        self.submodules.uart_phy = uart_phy = uart.UARTPHY(pads, clk_freq, baudrate=921600)
        self.submodules.uart = uart.UART(uart_phy, tx_fifo_depth=4, rx_fifo_depth=128)
    
