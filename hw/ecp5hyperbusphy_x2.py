# This file is Copyright (c) 2020 Gregory Davill <greg.davill@gmail.com>
# License: BSD

from migen import Module, Record, Signal, TSTriple, Instance, ClockSignal, ResetSignal, If, Cat

from migen.genlib.cdc import MultiReg

#from hyperram_x2 import delayf_pins

def delayf_pins():
    return Record([("loadn", 1),("move", 1),("direction", 1)])

# HyperBusPHY -----------------------------------------------------------------------------------------

class HyperBusPHY(Module):
    """HyperBusPHY x2 for ECP5

    Provides I/O support for a 32bit datapath from HyperRAM x2 module
    - Uses ECP5 primitives IDDRX2F / ODDRX2F / DELAYF
      - Not technically supported under diamond outside of DQS modes
      - Only available on Left/Right I/O banks

    - PLL required to produce 2*sys_clk, then use CLKDIVF to create sys_clk 

    - Clocks
     - hr2x    : 2* sys_freq - I/O clock
     - hr      : sys_freq    - core clock
     - hr2x_90 : 2* sys_freq - phase shifted clock output to HyperRAM
     - hr_90   : sys_freq    - phase shifted clock for SCLK
    
    """
    def add_tristate(self, pad):
        t = TSTriple(len(pad))
        self.specials += t.get_tristate(pad)
        return t

    def __init__(self, pads):
        def io_bus(n):
            return Record([("oe", 1),("i", n),("o", n)])
        
        # # #
        self.clk_enable = Signal()
        self.cs = Signal()
        self.dq = io_bus(32)
        self.rwds = io_bus(4)


        ## IO Delay shifting 
        self.dly_io = delayf_pins()
        self.dly_clk = delayf_pins()

        dq        = self.add_tristate(pads.dq) if not hasattr(pads.dq, "oe") else pads.dq
        rwds      = self.add_tristate(pads.rwds) if not hasattr(pads.rwds, "oe") else pads.rwds


        # Shift non DDR signals to match the FF's inside DDR modules.
        self.specials += MultiReg(self.cs, pads.cs_n, n=2)

        self.specials += MultiReg(self.rwds.oe, rwds.oe, n=2)
        self.specials += MultiReg(self.dq.oe, dq.oe, n=2)
        
        # mask off clock when no CS
        clk_en = Signal()
        self.comb += clk_en.eq(self.clk_enable & ~self.cs)

        load_next = Signal(reset=0)
        dq_reg = Signal(32)
        rwds_reg = Signal(4)

        
        self.dq_in_reg = dq_in_reg = Signal(64)
        dq_in_ = Signal(16)
        rwds_in_reg = Signal(8)
        rwds_in_ = Signal(2)


        
        
        clk_en_reg = Signal()
        self.sync.hr2x += [
            load_next.eq(~load_next),
            If(ClockSignal("sys"),
                dq_reg.eq(self.dq.o),
                rwds_reg.eq(self.rwds.o),
                clk_en_reg.eq(clk_en),

                self.rwds.i.eq(rwds_in_reg[4:8]),
                self.dq.i.eq(Cat(dq_in_reg[16:24],dq_in_reg[40:48],dq_in_reg[32:40],dq_in_reg[56:64])),
            ).Else(
                dq_reg[16:32].eq(dq_reg[0:16]),
                rwds_reg[2:4].eq(rwds_reg[0:2]),
            ),

            rwds_in_reg.eq(Cat(rwds_in_, rwds_in_reg[:8])),
            dq_in_reg.eq(Cat(dq_in_, dq_in_reg[:48])),
        ]

        self.comb += [
            ]

        #clk_out
        clkp = Signal()
        clkn = Signal()
        self.specials += [
            Instance("ODDRX1F",
                i_D0=0,
                i_D1=clk_en_reg,
                i_SCLK=ClockSignal("hr2x_90"),
                i_RST=ResetSignal("hr2x_90"),
                o_Q=clkp),
            Instance("DELAYF",
                    p_DEL_MODE="USER_DEFINED",
                    p_DEL_VALUE=0, # (25ps per tap)
                    i_A=clkp,
                    i_LOADN=self.dly_clk.loadn,
                    i_MOVE=self.dly_clk.move,
                    i_DIRECTION=self.dly_clk.direction,
                    o_Z=pads.clk_p)
        ]
        
        self.specials += [
            Instance("ODDRX1F",
                i_D0=1,
                i_D1=~clk_en_reg,
                i_SCLK=ClockSignal("hr2x_90"),
                i_RST=ResetSignal("hr2x_90"),
                o_Q=clkn),
            Instance("DELAYF",
                    p_DEL_MODE="USER_DEFINED",
                    p_DEL_VALUE=0, # (25ps per tap)
                    i_A=clkn,
                    i_LOADN=self.dly_clk.loadn,
                    i_MOVE=self.dly_clk.move,
                    i_DIRECTION=self.dly_clk.direction,
                    o_Z=pads.clk_n)
        ]

        # DQ_out
        for i in range(8):
            dq_out = Signal()
            self.specials += [
                Instance("ODDRX1F",
                    i_D0=dq_reg[24+i],
                    i_D1=dq_reg[16+i],
                    i_SCLK=ClockSignal("hr2x"),
                    i_RST=ResetSignal("hr2x"),
                    o_Q=dq_out
                ),
                Instance("DELAYF",
                    p_DEL_MODE="USER_DEFINED",
                    p_DEL_VALUE=0, # (25ps per tap)
                    i_A=dq_out,
                    i_LOADN=self.dly_io.loadn,
                    i_MOVE=self.dly_io.move,
                    i_DIRECTION=self.dly_io.direction,
                    o_Z=dq.o[i])
            ]
    

        # DQ_in
        for i in range(8):
            self.specials += [
                Instance("IDDRX1F",
                    i_D=dq.i[i],
                    i_SCLK=ClockSignal("hr2x"),
                    i_RST= ResetSignal("hr2x"),
                    o_Q0=dq_in_[0+i],
                    o_Q1=dq_in_[8+i]
                )
            ]
        
        # RWDS_out
        rwds_out = Signal()
        self.specials += [
            Instance("ODDRX1F",
                i_D0=self.rwds.o[3],
                i_D1=self.rwds.o[2],
                i_SCLK=ClockSignal("hr2x"),
                i_RST=ResetSignal("hr2x"),
                o_Q=rwds_out
            ),
            Instance("DELAYF",
                    p_DEL_MODE="USER_DEFINED",
                    p_DEL_VALUE=0, # (25ps per tap)
                    i_A=rwds_out,
                    i_LOADN=self.dly_io.loadn,
                    i_MOVE=self.dly_io.move,
                    i_DIRECTION=self.dly_io.direction,
                    o_Z=rwds.o)
        ]

        # RWDS_in
        self.specials += [
            Instance("IDDRX1F",
                i_D=rwds.i,
                i_SCLK=ClockSignal("hr2x"),
                i_RST= ResetSignal("hr2x"),
                o_Q0=rwds_in_[0],
                o_Q1=rwds_in_[1]
            ),
            
        ]
