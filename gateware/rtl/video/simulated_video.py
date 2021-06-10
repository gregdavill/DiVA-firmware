# This file is Copyright (c) 2019 Frank Buss <fb@frank-buss.de>
# This file is Copyright (c) 2020 Gregory Davill <greg.davill@gmail.com>
# License: BSD

import os

from migen import *

class SimulatedVideo(Module):
    def __init__(self):
        
        # Display resolution
        WIDTH  = 640
        HEIGHT = 512

        # VGA output
        self.red   = red   = Signal(8)
        self.green = green = Signal(8)
        self.blue  = blue  = Signal(8)
        self.hsync = hsync = Signal()
        self.vsync = vsync = Signal()
        self.data_valid = data_valid = Signal()


        # VGA timings
        H_SYNC_PULSE  = 8
        H_BACK_PORCH  = 50 + H_SYNC_PULSE
        H_DATA        = WIDTH + H_BACK_PORCH
        H_FRONT_PORCH = 52 + H_DATA
        # Total 750 clocks per row

        V_SYNC_PULSE  = 88
        V_BACK_PORCH  = 0 + V_SYNC_PULSE
        V_DATA        = HEIGHT + V_BACK_PORCH
        V_FRONT_PORCH = 0 + V_DATA
        # 600 rows per frame. vsync LOW for 88 extra rows

        pixel_counter = Signal(14)
        line_counter  = Signal(14)

        self.sync.pixel += [
            # Default values
            red.eq(0),
            green.eq(0),
            blue.eq(0),
            data_valid.eq(0),

            # Show pixels
            If((line_counter >= V_BACK_PORCH) & (line_counter < V_DATA),
                If((pixel_counter >= H_BACK_PORCH) & (pixel_counter < (H_DATA)),
                    data_valid.eq(1),
                    red.eq(0x33),
                    green.eq(0x33),
                    blue.eq(0x33)
                )
            ),

            

            # Horizontal timing for one line
            pixel_counter.eq(pixel_counter + 1),
            If(pixel_counter < H_SYNC_PULSE,
                hsync.eq(0)
            ).Elif (pixel_counter < H_BACK_PORCH,
                hsync.eq(1)
            ),
            If(pixel_counter >= (H_FRONT_PORCH-1),
                # Initilize next line
                pixel_counter.eq(0),
                line_counter.eq(line_counter + 1),
            ),

            # Vertical timing for one screen
            If(line_counter < V_SYNC_PULSE,
                vsync.eq(0)
            ).Else(
                vsync.eq(1)
            ),
            If(line_counter >= (V_FRONT_PORCH-1),
                # End of image
                line_counter.eq(0)
            ),
        ]
