# This file is Copyright (c) 2019 Antti Lukats <antti.lukats@gmail.com>
# This file is Copyright (c) 2019 Florent Kermarrec <florent@enjoy-digital.fr>
# This file is Copyright (c) 2020 Gregory Davill <greg.davill@gmail.com>
# License: BSD

from migen import *

from litex.soc.interconnect import wishbone
#from migen.genlib.io import DDRInput, DDROutput

from litex.soc.cores.clock import *
#from migen.genlib.misc import timeline


from migen.genlib.cdc import MultiReg


def timeline(trigger, events, offset):
    lastevent = max([e[0] for e in events])
    counter = Signal(max=lastevent+1)

    counterlogic = If(counter != 0,
        counter.eq(counter + 1 - offset)
    ).Elif(trigger,
        counter.eq(1)
    )
    # insert counter reset if it doesn't naturally overflow
    # (test if lastevent+1 is a power of 2)
    if (lastevent & (lastevent + 1)) != 0:
        counterlogic = If(counter == lastevent,
            counter.eq(0)
        ).Else(
            counterlogic
        )

    def get_cond(e):
        if e[0] == 0:
            return trigger & (counter == 0)
        else:
            return counter == e[0]
    sync = [If(get_cond(e), *e[1]) for e in events]
    sync.append(counterlogic)
    return sync


# HyperRAM -----------------------------------------------------------------------------------------

class HyperRAM(Module):
    """HyperRAM

    Provides a standard HyperRAM core that works at 1:1 system clock speeds
    - PHY is device dependent for DDR IO primitives
      - ECP5 (done)
    - 90 deg phase shifted clock required from PLL
    - Burst R/W supported if bus is ready
    - Latency indepedent reads (RWDS strobing)

    This core favors performance over portability

    """
    def __init__(self, pads):
        self.pads = pads
        self.bus  = bus = wishbone.Interface(adr_width=22)


        self.loadn = Signal()
        self.move = Signal()
        self.direction = Signal()

        # # #

        clk         = Signal()
        cs         = Signal()
        ca         = Signal(48)
        sr         = Signal(64)
        #sr_in      = Signal(64)
        sr_rwds    = Signal(8)

        latency = Signal(4, reset=11)
        
        phy = HyperBusPHY(pads)
        self.submodules += phy

        self.comb += [
            phy.direction.eq(self.direction),
            phy.loadn.eq(self.loadn),
            phy.move.eq(self.move),
        ]
        

        # Drive rst_n, from internal signals ---------------------------------------------
        if hasattr(pads, "rst_n"):
            self.comb += pads.rst_n.eq(1)
            
        self.comb += [
            phy.cs.eq(~cs),
            phy.clk_enable.eq(clk)
        ]
        
        # Data Out Shift Register (for write) -------------------------------------------------
        self.sync += [
            sr.eq(Cat(phy.dq.i, sr[:32])),
            sr_rwds[-4:].eq(sr_rwds),
            #If(ca_load, 
            #    sr.eq(ca)
            #),
            #If(dq_load,
            #    sr_out[:16].eq(0),
            #    sr_out[16:].eq(self.bus.dat_w),
            #    sr_rwds.eq(~self.bus.sel)
            #)
        ]

        # Data in Shift Register
        dqi = Signal(16)
        #self.sync += dqi.eq(phy.dq_in) # Store last sample, to align edges.
        self.sync += [
        #    If(phy.rwds_in == 0b01, # RAM indicates to us a valid word with RWDS strobes
        #        sr_in.eq(Cat(phy.dq_in[8:], dqi[:8], sr_in[:-16]))
        #    )
        ]

        self.comb += [
            bus.dat_r.eq(Cat(phy.dq.i[16:32], sr[:16])), # To Wishbone
            phy.dq.o.eq(sr[-32:]),  # To HyperRAM
        #    phy.rwds_out.eq(sr_rwds[-2:]) # To HyperRAM
        ]

        # Command generation -----------------------------------------------------------------------
        self.comb += [
            ca[47].eq(~self.bus.we),          # R/W#
            ca[45].eq(1),                     # Burst Type (Linear)
            ca[16:35].eq(self.bus.adr[2:21]), # Row & Upper Column Address
            ca[1:3].eq(self.bus.adr[0:2]),    # Lower Column Address
            ca[0].eq(0),                      # Lower Column Address
        ]

        #self.counter = counter = Signal(8)
        #counter_rst = Signal()

        offset = Signal(5)

        # Sequencer --------------------------------------------------------------------------------
        dt_seq = [
            # DT,  Action
            (1,    [cs.eq(1)]),
            (2,    [clk.eq(1), phy.dq.oe.eq(1), sr.eq(ca)]),    # Command: 6 clk
            (3,    [phy.dq.oe.eq(0)]),                         # Latency(default): 2*6 clk
            (1,    [phy.dq.oe.eq(self.bus.we),                 # Write/Read data byte: 2 clk
                    sr[:32].eq(0),
                    sr[32:].eq(Cat(self.bus.dat_w[16:32],self.bus.dat_w[0:16])),
                    phy.rwds.o.eq(~bus.sel[0:4])]),
            #(2,    [phy.rwds.o.eq(~bus.sel[1])]),              # Write/Read data byte: 2 clk
            (1,    [clk.eq(0)]),              # Write/Read data byte: 2 clk
            (1,    [cs.eq(0),phy.rwds.oe.eq(0),phy.dq.oe.eq(0)]),              # Write/Read data byte: 2 clk
            (2,    []),
            (1,    [bus.ack.eq(1)]),
            (1,    [bus.ack.eq(0)]),
            (0,    []),
        ]
        # Convert delta-time sequencer to time sequencer
        t_seq = []
        t = 0
        for dt, a in dt_seq:
            t_seq.append((t, a))
            t += dt
        self.sync += timeline(bus.cyc & bus.stb, t_seq, offset)


class HyperBusPHY(Module):

    def add_tristate(self, pad):
        t = TSTriple(len(pad))
        self.specials += t.get_tristate(pad)
        return t

    def __init__(self, pads):
        
        # # #
        self.interface = Record([
            ("clk_enable1", 1)
        ])

        self.clk_enable = Signal()
        self.cs = Signal()

        self.dq = Record([
            ("oe", 1),
            ("i", 32),
            ("o", 32),
        ])

        self.rwds = Record([
            ("oe", 1),
            ("i", 4),
            ("o", 4),
        ])

        ## IO Delay shifting 
        self.loadn = Signal()
        self.move = Signal()
        self.direction = Signal()

        dq        = self.add_tristate(pads.dq) if not hasattr(pads.dq, "oe") else pads.dq
        rwds      = self.add_tristate(pads.rwds) if not hasattr(pads.rwds, "oe") else pads.rwds


        # Shift non DDR signals to match the FF's inside DDR modules.
        self.specials += MultiReg(self.cs, pads.cs_n, n=3)

        self.specials += MultiReg(self.rwds.oe, rwds.oe, n=3)
        self.specials += MultiReg(self.dq.oe, dq.oe, n=3)
        
        # mask off clock when no CS
        clk_en = Signal()
        self.comb += clk_en.eq(self.clk_enable & ~self.cs)
        #self.sync += [
        #    clk_en.eq(self.clk_en & ~self.cs)
        #]
        
        #clk_out
        for clk in [pads.clk_p, pads.clk_n]:
            self.specials += [
                Instance("ODDRX2F",
                    i_D0=clk_en,
                    i_D1=0,
                    i_D2=clk_en,
                    i_D3=0,
                    i_SCLK=ClockSignal("hr"),
                    i_ECLK=ClockSignal("hr2x_90"),
                    i_RST=ResetSignal("hr"),
                    o_Q=clk
                )
            ]


        # DQ_out
        for i in range(8):
            self.specials += [
                Instance("ODDRX2F",
                    i_D1=self.dq.o[i],
                    i_D0=self.dq.o[8+i],
                    i_D3=self.dq.o[16+i],
                    i_D2=self.dq.o[24+i],
                    i_SCLK=ClockSignal("hr"),
                    i_ECLK=ClockSignal("hr2x"),
                    i_RST=ResetSignal("hr"),
                    o_Q=dq.o[i]
                )
            ]
        

        # DQ_in
        for i in range(8):
            dq_in = Signal()
            self.specials += [
                Instance("IDDRX2F",
                    i_D=dq_in,
                    i_SCLK=ClockSignal("hr"),
                    i_ECLK=ClockSignal("hr2x"),
                    i_RST= ResetSignal("hr"),
                    o_Q3=self.dq.i[i],
                    o_Q2=self.dq.i[i+8],
                    o_Q1=self.dq.i[i+16],
                    o_Q0=self.dq.i[i+24]
                ),
                Instance("DELAYF",
                    p_DEL_MODE="USER_DEFINED",
                    p_DEL_VALUE=120, # 2ns (25ps per tap)
                    i_A=dq.i[i],
                    i_LOADN=self.loadn,
                    i_MOVE=self.move,
                    i_DIRECTION=self.direction,
                    o_Z=dq_in)
            ]
        
        # RWDS_out
        self.specials += [
            Instance("ODDRX2F",
                i_D0=self.rwds.o[0],
                i_D1=self.rwds.o[1],
                i_D2=self.rwds.o[2],
                i_D3=self.rwds.o[3],
                i_SCLK=ClockSignal("hr"),
                i_ECLK=ClockSignal("hr2x"),
                i_RST=ResetSignal("hr"),
                o_Q=rwds.o
            )
        ]

        # RWDS_in
        rwds_in = Signal()
        self.specials += [
            Instance("IDDRX2F",
                i_D=rwds_in,
                i_SCLK=ClockSignal("hr"),
                i_ECLK=ClockSignal("hr2x"),
                i_RST= ResetSignal("hr"),
                o_Q0=self.rwds.i[1],
                o_Q1=self.rwds.i[0],
                o_Q2=self.rwds.i[3],
                o_Q3=self.rwds.i[2]
            ),
            Instance("DELAYF",
                    p_DEL_MODE="USER_DEFINED",
                    p_DEL_VALUE=120, # 2ns (25ps per tap)
                    i_A=rwds.i,
                    i_LOADN=self.loadn,
                    i_MOVE=self.move,
                    i_DIRECTION=self.direction,
                    o_Z=rwds_in)
        ]
