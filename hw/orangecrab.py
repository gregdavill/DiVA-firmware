# This file is Copyright (c) 2017 Serge 'q3k' Bazanski <serge@bazanski.pl>
# License: BSD

from litex.build.generic_platform import *
from litex.build.lattice import LatticePlatform

# IOs ----------------------------------------------------------------------------------------------

_io = [
    ("clk48", 0, Pins("M1"),  IOStandard("LVCMOS18")),
    ("rst_n", 0, Pins("V17"), IOStandard("LVCMOS33")),


    ("rgb_led", 0,
        Subsignal("r", Pins("L16"), IOStandard("LVCMOS33")),
        Subsignal("g", Pins("J16"), IOStandard("LVCMOS33")),
        Subsignal("b", Pins("J17"), IOStandard("LVCMOS33")),
    ),

    ("hdmi", 0,
        Subsignal("p", Pins("J18 H17 K17 F17"), IOStandard("LVCMOS33"), Misc("SLEWRATE=SLOW")),
        Subsignal("n", Pins("K18 G18 L18 F16"), IOStandard("LVCMOS33"), Misc("SLEWRATE=SLOW")),
    ),

    ("hyperRAM", 0,
        Subsignal("rst_n",     Pins("F4"),       IOStandard("LVCMOS18"),Misc("SLEWRATE=FAST")),    
        Subsignal("clk_p",     Pins("G4"),     IOStandard("LVCMOS18"),Misc("SLEWRATE=FAST")),
        Subsignal("clk_n",     Pins("H4"),     IOStandard("LVCMOS18"),Misc("SLEWRATE=FAST")),
        Subsignal("cs_n",      Pins("F3"),       IOStandard("LVCMOS18"),Misc("SLEWRATE=FAST")),
        Subsignal("dq",        Pins("K4 L4 J3 K3 L1 M3 N4 N3"),     IOStandard("LVCMOS18"),Misc("SLEWRATE=FAST")),
        Subsignal("rwds",       Pins("H3"),     IOStandard("LVCMOS18"),Misc("SLEWRATE=FAST")),
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

