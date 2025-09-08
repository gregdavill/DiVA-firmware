# This file is Copyright (c) 2021 Greg Davill <greg.davill@gmail.com>
# License: BSD

import os

import litex
from migen import *
from litex.soc.interconnect.stream import ClockDomainCrossing, Endpoint

# Create a migen module to interface into a compiled nmigen module
class LunaUSBSerialDevice(Module):
    def __init__(self, platform, usb_io):
        # Follow LiteX sink/source
        self.sink = Endpoint([("data", 8)])
        self.source = Endpoint([("data", 8)])

        self.connect = Signal()

        d_p = TSTriple(1).get_tristate(usb_io.d_p)
        d_n = TSTriple(1).get_tristate(usb_io.d_n)
        self.specials += d_p, d_n
        
        # Add generated verilog module
        vdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verilog")
        platform.add_source(os.path.join(vdir, f"LunaUSBSerialDevice.v"))

        tx_cdc = ClockDomainCrossing([("data", 8)], cd_from="sys", cd_to="usb_12", depth=32)
        rx_cdc = ClockDomainCrossing([("data", 8)], cd_from="usb_12", cd_to="sys")
        self.submodules += tx_cdc, rx_cdc

        self.comb += [
            # sink -> tx_cdc.sink
            self.sink.connect(tx_cdc.sink),
            # rx_cdc.source -> self.source
            rx_cdc.source.connect(self.source)
        ]

        self.params = dict(
            # Clock / Reset
            i_usb_clk   = ClockSignal("usb_12"),
            i_usb_rst   = ResetSignal("usb_12"),
            i_usb_io_clk   = ClockSignal("usb_48"),

            # Physical I/O connections
            i_io__d_p__i = d_p.i,
            o_io__d_p__o = d_p.o,
            o_io__d_p__oe = d_p.oe,
            
            i_io__d_n__i = d_n.i,
            o_io__d_n__o = d_n.o,
            o_io__d_n__oe = d_n.oe,
            
            o_io__pullup__o = usb_io.pullup,

            # Streams
            # Tx stream (Data out to computer)
            o_tx__ready   = tx_cdc.source.ready,
            i_tx__valid   = tx_cdc.source.valid,
            i_tx__first   = tx_cdc.source.first,
            i_tx__last    = tx_cdc.source.last,
            i_tx__payload = tx_cdc.source.data,
            
            # Rx Stream (Data in from a Computer)
            i_rx__ready   = rx_cdc.sink.ready,
            o_rx__valid   = rx_cdc.sink.valid,
            o_rx__first   = rx_cdc.sink.first,
            o_rx__last    = rx_cdc.sink.last,
            o_rx__payload = rx_cdc.sink.data,

            # Connect
            i_connect = self.connect
        )

        self.specials += Instance("LunaUSBSerialDevice",
            **self.params
        )
