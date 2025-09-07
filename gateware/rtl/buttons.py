from migen import *
from migen.genlib.cdc import MultiReg
from litex.soc.interconnect.csr import AutoCSR, CSR, CSRField

class Button(Module, AutoCSR):
    def __init__(self, pads):

        self.events = CSR(32)
        self.raw = CSR(32)

        events = Signal(32)
        raw = Signal(32)

        PRESS_TIME = int(82.5e6 * 5e-3)
        HOLD_TIME = int(82.5e6 * 750e-3)

        button_a_counter = Signal(max=max(PRESS_TIME, HOLD_TIME))
        button_b_counter = Signal(max=max(PRESS_TIME, HOLD_TIME))
        
        button_a_sig = Signal()
        button_b_sig = Signal()
        
        # de glitch
        self.specials += MultiReg(~pads.a, button_a_sig, n=4)
        self.specials += MultiReg(~pads.b, button_b_sig, n=4)

        self.sync += [
            If(self.events.re | self.events.we,
                events.eq(events & ~self.events.r)
            ),

            If(button_a_sig,
                If(button_a_counter < HOLD_TIME,
                    button_a_counter.eq(button_a_counter + 1)
                ),
                If(button_a_counter == (HOLD_TIME - 1),
                    events[2].eq(1)
                )
            ).Else(
                If((button_a_counter > PRESS_TIME) & (button_a_counter < HOLD_TIME),
                    events[0].eq(1)
                ),
                button_a_counter.eq(0),
            ),

            If(button_b_sig,
                If(button_b_counter < HOLD_TIME,
                    button_b_counter.eq(button_b_counter + 1)
                ),
                If(button_b_counter == (HOLD_TIME - 1),
                    events[3].eq(1)
                )
            ).Else(
                If((button_b_counter > PRESS_TIME) & (button_b_counter < HOLD_TIME),
                    events[1].eq(1)
                ),
                button_b_counter.eq(0),
            )
        ]

        self.sync += [
            raw.eq(0),
            If(button_a_counter > PRESS_TIME,
                raw[0].eq(1)
            ),
            If(button_b_counter > PRESS_TIME,
                raw[1].eq(1)
            ),
        ]

        self.comb += [
            self.events.w.eq(events),
            self.raw.w.eq(raw)
        ]
    
