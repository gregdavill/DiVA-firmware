# This file is Copyright (c) 2020 Gregory Davill <greg.davill@gmail.com>
# License: BSD

from migen import *

from litex.soc.interconnect.stream import EndpointDescription, Endpoint

from litex.soc.cores import uart
from rtl.ecp5_dynamic_pll import period_ns

from litex.soc.interconnect.csr import AutoCSR

from migen.genlib.resetsync import AsyncResetSynchronizer



class BosonDataRx(Module):
    def __init__(self, pads):
        self.source = source = Endpoint(EndpointDescription([("data", 24)]))
        
        vsync_ = Signal()
        vsync_falling = Signal()

        self.pixel_counter_last = Signal(max=640*512)        
        pixel_counter = Signal(max=640*512)        

        self.comb += [
            vsync_falling.eq(pads.vsync & ~vsync_),

            If(pads.valid,
                source.data.eq(pads.data),
                source.first.eq(pixel_counter == 0),
                source.last.eq(pixel_counter == (640*512) - 1),
                source.valid.eq(1),
            )
        ]

        self.sync += [
            If(pads.valid,
                pixel_counter.eq(pixel_counter + 1)
            ),

            vsync_.eq(pads.vsync),
            If(vsync_falling,
                pixel_counter.eq(0),
                self.pixel_counter_last.eq(pixel_counter)
            )
        ]



# Convert the Boson clock pin Signal into a clock domain
class BosonClk(Module):
    def __init__(self, clk_pad, platform):
        self.clock_domains.cd_boson_rx = ClockDomain()        
        self.comb += self.cd_boson_rx.clk.eq(clk_pad)
        
        self.specials += AsyncResetSynchronizer(self.cd_boson_rx, 0)
        platform.add_period_constraint(self.cd_boson_rx.clk, period_ns(27e6))


class Boson(Module, AutoCSR):
    def __init__(self, platform, pads, clk_freq):
        self.submodules.clk = BosonClk(pads.clk, platform)
        self.submodules.rx = ClockDomainsRenamer("boson_rx")(BosonDataRx(pads))
        self.source = self.rx.source
        
        self.hsync = pads.hsync
        self.vsync = pads.vsync
        self.data_valid = pads.valid
        self.pixel_count = self.rx.pixel_counter_last

        self.submodules.uart_phy = uart_phy = uart.UARTPHY(pads, clk_freq, baudrate=921600)
        self.submodules.uart = uart.UART(uart_phy, tx_fifo_depth=4, rx_fifo_depth=128)
    
