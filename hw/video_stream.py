# This file is Copyright (c) 2020 Gregory Davill <greg.davill@gmail.com>
# License: BSD

from migen import *
from litex.soc.interconnect.stream import Endpoint

class VideoStream(Module):
    def __init__(self):
        # VGA output
        self.red   = red   = Signal(8)
        self.green = green = Signal(8)
        self.blue  = blue  = Signal(8)
        self.data_valid = data_valid = Signal()

        self.source = source = Endpoint([("data", 32)])

        self.sync.pixel += [
            source.valid.eq(data_valid),
            source.data.eq(Cat(red, green, blue)),
        ]
