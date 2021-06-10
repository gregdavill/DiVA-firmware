from migen import *
from litex.soc.interconnect.csr import AutoCSR, CSRStorage

class Reboot(Module, AutoCSR):
    def __init__(self, rst, ext_rst=None):

        self.ctrl = CSRStorage(8)
        
        do_reset = Signal()
        self.comb += [
            # "Reset Key" is 0xac (0b10101100)
            do_reset.eq(self.ctrl.storage[2] & self.ctrl.storage[3] & ~self.ctrl.storage[4]
                      & self.ctrl.storage[5] & ~self.ctrl.storage[6] & self.ctrl.storage[7])
        ]

        reset_latch = Signal(reset=0)
        if ext_rst is None:
            self.sync += [
                reset_latch.eq(do_reset | reset_latch)
            ]
        else:
            self.sync += [
                reset_latch.eq(do_reset | reset_latch | ext_rst)
            ]

        self.comb += [
            rst.eq(~reset_latch)
        ]
    
