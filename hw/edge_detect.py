# This file is Copyright (c) 2020 Gregory Davill <greg.davill@gmail.com>
# License: BSD
from migen import *

from migen.genlib.cdc import PulseSynchronizer

class EdgeDetect(Module):
    def __init__(self, mode="rise", input_cd="sys", output_cd="sys"):
        self.i = i = Signal()
        self.o = o = Signal()

        pulse = Signal()
    
        reg = Signal()    
        v = getattr(self.sync, input_cd)
        v += reg.eq(i)
        if mode == "rise":
            v += pulse.eq(~reg & i)
        elif mode == "fall":
            v += pulse.eq(reg & ~i)
        elif mode == "change":
            v += pulse.eq(reg != i)
        else:
            AttributeError(f"Invalid mode={mode}")
    

        if input_cd is not output_cd:
            ps = PulseSynchronizer(input_cd, output_cd)
            self.submodules += ps
            self.comb += [
                ps.i.eq(pulse),
                o.eq(ps.o)
            ]
        else:
            self.comb += o.eq(pulse)
