# This file is Copyright (c) 2020 Gregory Davill <greg.davill@gmail.com>
# License: BSD

from migen import *
from litex.soc.interconnect.stream import Endpoint
from rtl.edge_detect import EdgeDetect

from litex.soc.interconnect.csr import AutoCSR, CSR, CSRStatus, CSRStorage
from litex.soc.interconnect.stream import Endpoint, EndpointDescription, AsyncFIFO

def framer_params():
    return [
        ("x_start", 16),
        ("y_start", 16),
        ("x_stop", 16),
        ("y_stop", 16),
    ]

class Framer(Module, AutoCSR):
    def __init__(self):
        self.sink = sink = Endpoint([("data", 32)])

        self.params = params = Endpoint(framer_params())

        self.hsync = hsync = Signal()
        self.vsync = vsync = Signal()


        # VGA output
        self.red   = red   = Signal(8)
        self.green = green = Signal(8)
        self.blue  = blue  = Signal(8)
        self.data_valid = data_valid = Signal()

        # parameters
        pixel_counter = Signal(14)
        line_counter  = Signal(14)

        h_det = EdgeDetect(mode="fall", input_cd="video", output_cd="video")
        v_det = EdgeDetect(mode="fall", input_cd="video", output_cd="video")
        self.submodules += h_det, v_det
        self.comb += [
            h_det.i.eq(hsync),
            v_det.i.eq(vsync),
        ]

        self.comb += [
            If((line_counter >= params.y_start) & (line_counter < params.y_stop),
                If((pixel_counter >= params.x_start) & (pixel_counter < params.x_stop),
                    sink.ready.eq(1)
                )
            )
        ]

        self.sync.video += [
            # Default values
            red.eq(0),
            green.eq(0),
            blue.eq(0),
            data_valid.eq(0),

            # Show pixels
            If((line_counter >= params.y_start) & (line_counter < params.y_stop),
                If((pixel_counter >= params.x_start) & (pixel_counter < params.x_stop),
                    data_valid.eq(1),
                    If(sink.valid,
                        red.eq(sink.data[0:8]),
                        green.eq(sink.data[8:16]),
                        blue.eq(sink.data[16:24])
                    ).Else( 
                        red.eq(0xFF),
                        green.eq(0x77),
                        blue.eq(0xFF)
                    )
                )
            ),

            # Horizontal timing for one line
            pixel_counter.eq(pixel_counter + 1),

            If(h_det.o,
                pixel_counter.eq(0),
                line_counter.eq(line_counter + 1),
            ),
            If(v_det.o,
                line_counter.eq(0),
            )
        ]