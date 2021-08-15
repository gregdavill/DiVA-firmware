# This file is Copyright (c) 2020 Gregory Davill <greg.davill@gmail.com>
# License: BSD

from litex.build.generic_platform import *
from litex.build.lattice import LatticePlatform

# IOs ----------------------------------------------------------------------------------------------

_io = [
    ("clk48", 0, Pins("M1"),  IOStandard("LVCMOS18")),
    ("rst_n", 0, Pins("V17"), IOStandard("LVCMOS33")),

    # Leds
    ("user_led", 0, Pins("L16"), IOStandard("LVCMOS33")), # rgb_led.r
    ("user_led", 1, Pins("J16"), IOStandard("LVCMOS33")), # rgb_led.g
    ("user_led", 2, Pins("J17"), IOStandard("LVCMOS33")), # rgb_led.b
    ("rgb_led", 0,
        Subsignal("r", Pins("L16"), IOStandard("LVCMOS33")),
        Subsignal("g", Pins("J16"), IOStandard("LVCMOS33")),
        Subsignal("b", Pins("J17"), IOStandard("LVCMOS33")),
    ),

    ("usb", 0,
        Subsignal("d_p", Pins("G16")),
        Subsignal("d_n", Pins("K15")),
        Subsignal("pullup", Pins("H16")),
        Subsignal("sw_sel", Pins("F15")),
        Subsignal("sw_oe", Pins("G15")),
        IOStandard("LVCMOS33")
    ),
            
    ("hdmi_i2c", 0,
        Subsignal("sda", Pins("M16")),
        Subsignal("scl", Pins("M17")),
    ),
    ("hdmi_cec", 0,
        Subsignal("cec", Pins("L15")),
    ),
    ("hdmi", 0,
        Subsignal("clk_p",       Pins("K17")),
        Subsignal("data0_p",     Pins("J18")),
        Subsignal("data1_p",     Pins("G18")),
        Subsignal("data2_p",     Pins("F17")),
        IOStandard("LVCMOS33D"),Misc("SLEWRATE=FAST"),Misc("DRIVE=16"),Misc("OPENDRAIN=OFF"),
    ),

    ("i2c", 0,
        Subsignal("sda", Pins("N15")),
        Subsignal("scl", Pins("N16")),
    ),

    ("hyperRAM", 0,
        Subsignal("rst_n",     Pins("F4"),       IOStandard("LVCMOS18"),Misc("SLEWRATE=FAST")),    
        Subsignal("clk_p",     Pins("G4"),       IOStandard("LVCMOS18"),Misc("SLEWRATE=FAST")),
        Subsignal("clk_n",     Pins("H4"),       IOStandard("LVCMOS18"),Misc("SLEWRATE=FAST")),
        Subsignal("cs_n",      Pins("F3"),       IOStandard("LVCMOS18"),Misc("SLEWRATE=FAST")),
        Subsignal("dq",        Pins("K4 L4 J3 K3 L1 M3 N4 N3"),     IOStandard("LVCMOS18"),Misc("SLEWRATE=FAST")),
        Subsignal("rwds",      Pins("H3"),       IOStandard("LVCMOS18"),Misc("SLEWRATE=FAST")),
    ),

    ("boson", 0,
        Subsignal("data", Pins("D15 C17 C13 B17 A2 A10 A11 C2 \
                                D1 A15 B11 C15 C3 A8 C1 B13 \
                                B12 B1 D13 B10 B15 A16 A4 A12"),IOStandard("LVCMOS18"),Misc("SLEWRATE=SLOW")),
        Subsignal("clk", Pins("A17"),IOStandard("LVCMOS18"),Misc("SLEWRATE=SLOW")),
        Subsignal("vsync", Pins("A13"),IOStandard("LVCMOS18"),Misc("SLEWRATE=SLOW")),
        Subsignal("hsync", Pins("D16"),IOStandard("LVCMOS18"),Misc("SLEWRATE=SLOW")),
        Subsignal("valid", Pins("C16"),IOStandard("LVCMOS18"),Misc("SLEWRATE=SLOW")),
        Subsignal("tx", Pins("A3"),IOStandard("LVCMOS18"),Misc("SLEWRATE=SLOW")),
        Subsignal("rx", Pins("B9"),IOStandard("LVCMOS18"),Misc("SLEWRATE=SLOW")),
        Subsignal("reset", Pins("B2"),IOStandard("LVCMOS18"),Misc("SLEWRATE=SLOW")),
        Subsignal("ext_sync", Pins("B18"),IOStandard("LVCMOS18"),Misc("SLEWRATE=SLOW")),
    ),    

    ("button", 0,
        Subsignal("a", Pins("F2"),IOStandard("LVCMOS18"),Misc("PULLMODE=UP")),
        Subsignal("b", Pins("J1"),IOStandard("LVCMOS18"),Misc("PULLMODE=UP")),
    ),

    ("spiflash", 0,
        Subsignal("cs_n", Pins("U17"), IOStandard("LVCMOS33")),
        #Subsignal("clk",  Pins("U16"), IOStandard("LVCMOS33")), # Note: CLK is bound using USRMCLK block
        Subsignal("miso", Pins("T18"), IOStandard("LVCMOS33")),
        Subsignal("mosi", Pins("U18"), IOStandard("LVCMOS33")),
        Subsignal("wp",   Pins("R18"), IOStandard("LVCMOS33")),
        Subsignal("hold", Pins("N18"), IOStandard("LVCMOS33")),
    ),
    ("spiflash4x", 0,
        Subsignal("cs_n", Pins("U17"), IOStandard("LVCMOS33")),
        #Subsignal("clk",  Pins("U16"), IOStandard("LVCMOS33")),
        Subsignal("dq",   Pins("U18 T18 R18 N18"), IOStandard("LVCMOS33")),
    ),
]



# Connectors ---------------------------------------------------------------------------------------

_connectors = [
]

# Platform -----------------------------------------------------------------------------------------

class Platform(LatticePlatform):
    default_clk_name = "clk48"
    default_clk_period = 1e9/48e6

    def __init__(self, **kwargs):
        LatticePlatform.__init__(self, "LFE5U-25F-8MG285C", _io, _connectors, toolchain='trellis', **kwargs)
        self.name = 'diva'

