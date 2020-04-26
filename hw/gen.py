
from migen import *

from litex.soc.interconnect import wishbone
from litex.soc.interconnect import stream



class Generator(Module):
    def __init__(self, scroll = False):
        # Wishbone interface
        self.bus = bus = wishbone.Interface(data_width=8)

        self.sink = sink = stream.Endpoint([('data',8)])

        self.submodules.fsm = fsm = FSM()
        

        counter = Signal(32)
        idx = Signal(16)

        counter_done = Signal()
        counter_ce = Signal()
        counter_val = Signal(32)

        self.sync += [
            If(counter_ce,
                counter.eq(counter_val)
            ).Elif(counter > 0,
                counter.eq(counter - 1)
            )
        ]

        self.comb += [
            counter_done.eq(counter == 0)
        ]

        char = Signal(8, reset=0x40)
        colour = Signal(8, reset = 0)
        address = Signal(32, reset= 0)

        ControlChar = Signal(3)
        nValue = Signal(8)
        ansiCode = Signal(8)
        textColour = Signal(8, reset=0x0F)

        fsm.act('INIT',
            NextValue(sink.ready, 1),
            If(sink.valid & sink.ready,
                NextValue(char, sink.data),

                If(ControlChar > 0,
                    If(ControlChar == 1,
                        NextValue(ControlChar,2),
                    ).Elif(ControlChar == 2,
                        NextValue(ansiCode, char),
                        NextValue(nValue, sink.data),
                        NextValue(ControlChar,3),
                    ).Elif(ControlChar == 3,
                        # Reset 
                        If(ansiCode == 0x5b, # [
                            If(nValue == 0x30,  #0
                                If(sink.data == 0x6d, # m
                                    NextValue(textColour, 0x0C), # White
                                )
                            ).Elif(nValue == 0x31,  #1
                                If(sink.data == 0x6d, # m
                                    NextValue(textColour, 0x0E), # cyan
                                )
                            )
                        ),
                        NextValue(ControlChar,0),
                    )
                ).Else(
                    If(sink.data == 0x0A,
                        If(char != 0x0D,
                            NextValue(address, 0),
                            NextState('SCROLL-INIT')
                        )
                    ).Elif(sink.data == 0x0D,
                        If(char != 0x0A,
                            NextValue(address, 0),
                            NextState('SCROLL-INIT'),
                        )
                    ).Elif(sink.data == 0x1B, # Control char
                        NextValue(ControlChar, 1),
                    ).Else(
                        NextState('ADD_CHAR'),
                    ),
                ),
                NextValue(sink.ready, 0),
            )
        )

        

        line_end = 238
        line_wrap = Signal()


        fsm.act('ADD_CHAR',
            If(address == line_end*2,
                NextValue(line_wrap,1),
                bus.dat_w.eq(170),
                bus.adr.eq(address + 240*2*66),
                bus.cyc.eq(1),
                bus.stb.eq(1),
                bus.we.eq(1),
                bus.sel.eq(1),

                If(bus.ack,
                    NextState('ADD_COLOUR'),
                    NextValue(address, address + 1),
                )
            ).Else(
                bus.dat_w.eq(char),
                bus.adr.eq(address + 240*2*66),
                bus.cyc.eq(1),
                bus.stb.eq(1),
                bus.we.eq(1),
                bus.sel.eq(1),

                If(bus.ack,
                    NextState('ADD_COLOUR'),
                    NextValue(address, address + 1),
                )
            )
            
        )

        fsm.act('ADD_COLOUR',
            bus.dat_w.eq(textColour),
            bus.adr.eq(address + 240*2*66),
            bus.cyc.eq(1),
            bus.stb.eq(1),
            bus.we.eq(1),
            bus.sel.eq(1),

            If(bus.ack,
                NextState('INIT'),
                #NextValue(char, char+1),
                NextValue(address, address + 1),


                If(address >= ((line_end*2)+1),
                    NextValue(address, 0),
                    NextState('SCROLL-INIT')
                ),
                
            )
            
        )

        src_address = Signal(32)
        dst_address = Signal(32)

        dat = Signal(8)

        self.comb += src_address.eq(dst_address + 240*2)
        
        fsm.act('SCROLL-INIT',
            NextValue(dst_address, 0x00),
            NextState('SCROLL-READ'),
        )

        fsm.act('SCROLL-READ',
                bus.adr.eq(src_address),
                bus.cyc.eq(1),
                bus.stb.eq(1),
                bus.sel.eq(1),

                If(bus.ack,
                    NextState('SCROLL-WRITE'),
                    NextValue(dat, bus.dat_r),
                )
            
        )

        fsm.act('SCROLL-WRITE',
            bus.dat_w.eq(dat),
            bus.adr.eq(dst_address),
            bus.cyc.eq(1),
            bus.stb.eq(1),
            bus.we.eq(1),
            bus.sel.eq(1),

            If(bus.ack,
                NextState('SCROLL-READ'),
                NextValue(dst_address, dst_address + 1),


                If(dst_address >= ((240*2*66)-2),
                    NextState('CLEAR-LINE'),
                    NextValue(address, 0)
                ),
            )
        )

        fsm.act('CLEAR-LINE',
            bus.dat_w.eq(0),
            bus.adr.eq(address  + 240*2*66 ),
            bus.cyc.eq(1),
            bus.stb.eq(1),
            bus.we.eq(1),
            bus.sel.eq(1),

            If(bus.ack,
                NextValue(address, address + 1),
                If(address >= ((240*2)-2),
                    If(line_wrap,
                        NextState('ADD_CHAR'),
                        NextValue(line_wrap, 0),
                    ),
                    NextState('INIT'),
                    NextValue(address, 0)
                ),
            )   
        )


       