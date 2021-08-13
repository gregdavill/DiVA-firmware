from migen import *
from litevideo.output.common import *
from litevideo.output.hdmi.encoder import Encoder
from litex.build.io import DDROutput


class _ECP5OutSerializer(Module):
    def __init__(self, pad, invert=False):
        self.submodules.encoder = ClockDomainsRenamer("video")(Encoder())
        self.d, self.c, self.de = self.encoder.d, self.encoder.c, self.encoder.de
        self.load_sr = Signal()

        # Stage 1: 1:5 gearbox
        _data = Signal(10)
        self.sync.video_shift += [
            _data.eq(_data[2:]),
            If(
                self.load_sr,
                _data.eq(self.encoder.out),
            )
        ]

        # Stage 2: Optional invert
        data_out = Signal(2)
        if invert:
            self.sync.video_shift += data_out.eq(~_data[0:2])
        else:
            self.sync.video_shift += data_out.eq(_data[0:2])

        self.specials += DDROutput(data_out[0], data_out[1], pad,
                                    ClockSignal("video_shift"))


class HDMI(Module):
    def __init__(self, pins):
        self.sink = sink = stream.Endpoint(phy_layout('rgb'))

        # Generate strobe signal every 5 video_shift clks
        load_sr = Signal()
        count = Signal(5, reset=0b00100)
        self.sync.video_shift += count.eq(Cat(count[-1], count[:-1]))
        self.comb += load_sr.eq(count[0])

        self.submodules.es0 = _ECP5OutSerializer(
            pins.data0_p,
            invert=True)  # Due to layout reasons these pins are inverted
        self.submodules.es1 = _ECP5OutSerializer(pins.data1_p)
        self.submodules.es2 = _ECP5OutSerializer(
            pins.data2_p,
            invert=True)  # Due to layout reasons these pins are inverted

        self.comb += [
            sink.ready.eq(1),
            self.es0.load_sr.eq(load_sr),
            self.es1.load_sr.eq(load_sr),
            self.es2.load_sr.eq(load_sr),
            self.es0.d.eq(sink.b),
            self.es1.d.eq(sink.g),
            self.es2.d.eq(sink.r),
            self.es0.c.eq(Cat(sink.hsync, sink.vsync)),
            self.es1.c.eq(0),
            self.es2.c.eq(0),
            self.es0.de.eq(sink.de),
            self.es1.de.eq(sink.de),
            self.es2.de.eq(sink.de)
        ]

        self.specials += DDROutput(1, 0, pins.clk_p, ClockSignal("video"))
