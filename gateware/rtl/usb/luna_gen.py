# This file is Copyright (c) 2025 Greg Davill <greg.davill@gmail.com>
# License: BSD

import os

from amaranth import Signal, Module, Elaboratable, ClockDomain, ClockSignal, ResetSignal
from amaranth.lib import data, wiring
from amaranth.back import verilog

from luna.gateware.utils.rec import Record, DIR_FANIN, DIR_FANOUT, DIR_NONE

from luna.full_devices import USBSerialDevice as LunaDeviceACM
from luna.gateware.architecture.car import PHYResetController

# Create an amaranth module that exposes external interfaces as Signal/Record attributes of the class
class LunaUSBSerialDevice(Elaboratable):
    def __init__(self):
        self.io = Record([
            ('d_p', [('i', 1, DIR_FANIN), ('o', 1, DIR_FANOUT), ('oe', 1, DIR_FANOUT)]),
            ('d_n', [('i', 1, DIR_FANIN), ('o', 1, DIR_FANOUT), ('oe', 1, DIR_FANOUT)]),
            ('pullup', [('o', 1, DIR_FANOUT)]),
        ])


        self.usb0 = usb = LunaDeviceACM(bus=self.io, idVendor=0x1209, idProduct=0x5af1, 
                manufacturer_string="GroupGets|GsD", product_string="Boson Digital Video Adapter")
        
        self.rx = Record(usb.rx.layout)
        self.tx = Record(usb.tx.layout)
            
        self.usb_clk = Signal()
        self.usb_rst = Signal()
        self.usb_io_clk = Signal()

        self.connect  = Signal()


    def elaborate(self, platform):
        m = Module()

        # Create our clock domains.
        m.domains.usb = ClockDomain()
        m.domains.usb_io  = ClockDomain()

        m.submodules.usb_reset = controller = PHYResetController(reset_length=40e-3, stop_length=40e-4)
        m.d.comb += [
            ResetSignal("usb")  .eq(controller.phy_reset),
        ]
        
        # Attach Clock domains
        m.d.comb += [
            ClockSignal(domain="usb")     .eq(self.usb_clk),
            ClockSignal(domain="usb_io")  .eq(self.usb_io_clk),
            ResetSignal("usb").eq(self.usb_rst),
        ]
        
        # Attach usb module
        m.submodules.usb0 = self.usb0

        m.d.comb += [
            # Wire up streams
            self.usb0.tx.valid    .eq(self.tx.valid),
            self.usb0.tx.first    .eq(self.tx.first),
            self.usb0.tx.last     .eq(self.tx.last),
            self.usb0.tx.payload  .eq(self.tx.payload),
            # --
            
            self.tx.ready    .eq(self.usb0.tx.ready),


            self.rx.valid    .eq(self.usb0.rx.valid),
            self.rx.first    .eq(self.usb0.rx.first),
            self.rx.last     .eq(self.usb0.rx.last),
            self.rx.payload  .eq(self.usb0.rx.payload),
            # --
            self.usb0.rx.ready    .eq(self.rx.ready),
        
            # ... Pass through connect flag
            self.usb0.connect     .eq(self.connect)
        ]
        return m


elaboratable = LunaUSBSerialDevice()
name = 'LunaUSBSerialDevice'

ports = []

# Patch through all Records/Ports
for port_name, port in vars(elaboratable).items():
    if not port_name.startswith("_") and isinstance(port, (Signal, Record)):
        ports += port._lhs_signals()

verilog_text = verilog.convert(elaboratable, name=name, ports=ports, strip_internal_attrs=True)
verilog_file = f"verilog/{name}.v"

vdir = os.path.join(os.getcwd(), "verilog")
os.makedirs(vdir, exist_ok=True)

with open(verilog_file, "w") as f:
    f.write(verilog_text)