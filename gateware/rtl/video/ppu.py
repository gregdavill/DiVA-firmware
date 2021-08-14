from litex.soc.interconnect.csr_eventmanager import EventManager
from migen import *

from litex.soc.interconnect.stream import *


from litex.soc.interconnect import csr_eventmanager as ev

from litevideo.output.core import Initiator, TimingGenerator
from litex.soc.interconnect import stream
from litex.soc.interconnect.stream import *

from litevideo.output.common import *

from litex.soc.interconnect import wishbone

class op():
    codes = {
        'SYNC': 0x0,
        'CLIP': 0x1,
        'FILL': 0x2,
        'BLIT': 0x3,
        'PUSH': 0xe,
        'POPJ': 0xf,
    }

    YLT = 1
    YGE = 2


class LineBuffer(Module):
    def __init__(self):
        lb0, lb1 = Memory(24, 2048, name=f'lb0'),Memory(24, 2048, name=f'lb1')
        re0 = lb0.get_port(write_capable=True, mode=READ_FIRST)
        re1 = lb1.get_port(write_capable=True, mode=READ_FIRST)        
        self.specials += lb0, lb1, re0, re1

        mp_layout = [
            ('adr',len(re0.adr), DIR_M_TO_S),
            ('dat_r',24, DIR_S_TO_M),
            ('we', 1, DIR_M_TO_S),
            ('dat_w', 24, DIR_M_TO_S)
        ]
        self.front = Record(mp_layout)
        self.back = Record(mp_layout)

        self.buffer_sel = Signal()

        self.comb += [
            If(self.buffer_sel,
                self.front.connect(re0),
                self.back.connect(re1),
            ).Else(
                self.front.connect(re1),
                self.back.connect(re0),
            )
        ]

class WishboneController(Module):
    def __init__(self):
        self.we = Signal()
        self.adr_w = Signal(32)

        self.adr_r = Signal(32)


        self.bus = bus = wishbone.Interface(data_width=32)

        self.submodules.fifo = fifo = ResetInserter()(SyncFIFO([('data', 32)], 16, buffered=True))

        self.instr = fifo.source.data
        self.valid = fifo.source.valid
        self.ready = fifo.source.ready
        self.flush = fifo.reset

        self.submodules.fsm = fsm = FSM(reset_state='FILL')

        self.sync += [
            If(bus.ack,
                bus.adr.eq(bus.adr + 1),
            ),
            If(fifo.source.valid & fifo.source.ready,
                self.adr_r.eq(self.adr_r + 1)
            ),
            If(self.we,
                bus.adr.eq(self.adr_w),
                self.adr_r.eq(self.adr_w),
            ),
        ]
        self.comb += [
            If(self.we,
                fifo.reset.eq(1)
            )
        ]

        fsm.act('FILL',
            If(~fifo.reset,
                bus.cyc.eq(1),
                bus.stb.eq(1),
                If(fifo.level < 12,
                    bus.cti.eq(2)
                ),
            
                fifo.sink.data.eq(bus.dat_r),
                fifo.sink.valid.eq(bus.ack),
                
                If(~fifo.sink.ready,
                    NextState('WAIT'),
                ),
            ),
        )

        fsm.act('WAIT',
            If((fifo.level < 8) | fifo.reset,
                NextState('FILL'),
            )
        ),


class PalletteMemory(Module, AutoCSR):
    def __init__(self):
        palletteMem = Memory(16, 256, name=f'palletteMem')
        wp = palletteMem.get_port(write_capable=True, mode=READ_FIRST)
        rp = palletteMem.get_port(write_capable=False, mode=READ_FIRST)
        self.specials += palletteMem, wp, rp

        self._pmem_adr = CSR(8)
        self._pmem_dat = CSR(16)

        self.adr = rp.adr
        self.dat_r = rp.dat_r
        

        self.comb += [
            wp.dat_w.eq(self._pmem_dat.w),
            wp.we.eq(self._pmem_dat.re),
        ]

        self.sync += [
            If(self._pmem_dat.re,
                wp.adr.eq(rp.adr + 1),
            ),
            If(self._pmem_adr.re,
                wp.adr.eq(self._pmem_adr.w)
            )
        ]


class PalletteMux(Module):
    def __init__(self):
        # Input can be colour or pallette index
        self.i = Signal(24)
        self.o = Signal(24)

        self.we = Signal()
        self.we_o = Signal()

        self.submodules.pm = pm = PalletteMemory()
        i_r = Signal(24)

        self.mode = Signal()

        self.sync += [
            i_r.eq(self.i),
            self.we_o.eq(self.we)
        ]

        self.comb += [
            pm.adr.eq(self.i),
        
            self.o.eq(Mux(self.mode, pm.dat_r, (i_r << 4+16) | (i_r << 4+8) | (i_r << 4)))
        ]


class PPU(Module, AutoCSR):
    def __init__(self):

        # Frame timing input
        self.sink = sink = stream.Endpoint(frame_timing_layout + frame_parameter_layout)

        # Video signal output
        self.source = source = stream.Endpoint(video_out_layout(24))

        # Stack for PPU
        stack_mem = Memory(width=32, depth=8)
        stack_port = stack_mem.get_port(write_capable=True)
        self.specials += stack_mem, stack_port

        # Wishbone Controller Interface
        self.submodules.wb_ctrl = wb_ctrl = WishboneController()
        self.bus = wb_ctrl.bus

        # Pallette memory
        self.submodules.pm = pal_mux = PalletteMux()

        # CSR Interface
        self._pc = csr_pc = CSRStorage(size=32, name='pc')

        last_hsync = Signal()
        last_vsync = Signal()
        last_de = Signal()
        buffer_swap = Signal()
        self.next_frame = Signal()

        frame_end = Signal()

        # Generate strobes form timing signals
        # Note they're in a different clock domain, so we use `PulseSynchronizer` to make sure the signals pass through
        self.sync.video += [
            last_hsync.eq(sink.hsync),
            last_vsync.eq(sink.vsync),
            last_de.eq(sink.de)
        ]
        hsync_ps = PulseSynchronizer('video', 'sys')
        vsync_ps = PulseSynchronizer('video', 'sys')
        de_ps = PulseSynchronizer('video', 'sys')
        self.submodules += hsync_ps, vsync_ps, de_ps
        

        starter = Signal(2)
        self.comb += [
            de_ps.i.eq(last_de & ~sink.de),
            hsync_ps.i.eq(~last_hsync & sink.hsync),
            vsync_ps.i.eq(last_vsync & ~sink.vsync),
            
            frame_end.eq(vsync_ps.o),
            buffer_swap.eq(((starter[0] | starter[1]) & hsync_ps.o) | de_ps.o),
            self.next_frame.eq(vsync_ps.o)
        ]


        self.sync += [
            If(vsync_ps.o,
                starter.eq(0b10)
            ),
            If(hsync_ps.o,
                starter.eq(Cat(starter[-1:]))
            )
        ]
        
        total_lines = Signal(vbits)
        active_line_idx = Signal(hbits)
        inactive_line_idx = Signal(hbits)
        inactive_line_we = Signal()
        inactive_line_dat_w = Signal(24)
        self.submodules.lb = lb = LineBuffer()

        self.sync += [
            If(buffer_swap,
                lb.buffer_sel.eq(~lb.buffer_sel),
                total_lines.eq(total_lines + 1),
                If(total_lines <= (1080-1),
                    active_line_idx.eq(0),
                )
            ),
            If(frame_end,
                total_lines.eq(0),
            )
        ]


        y_counter = Signal(vbits)

        cdc = ClockDomainCrossing([('data',24)], cd_from='sys', cd_to='video', depth=8)
        self.submodules += cdc

        self.sync += [
            If(cdc.sink.ready & cdc.sink.valid,
                active_line_idx.eq(active_line_idx + 1),
            ),
        ]

        self.comb += [
            cdc.sink.valid.eq(active_line_idx <= (1920-1)),
            cdc.sink.data.eq(lb.front.dat_r),

            source.data.eq(cdc.source.data),
            cdc.source.ready.eq(sink.de),
        ]

        self.comb += [
            lb.front.adr.eq(active_line_idx + (cdc.sink.ready & cdc.sink.valid)),
            lb.front.we.eq(0),
            lb.front.dat_w.eq(0),

            lb.back.adr.eq(inactive_line_idx),
            lb.back.we.eq(inactive_line_we),
            lb.back.dat_w.eq(inactive_line_dat_w),
        ]

        clip_x_start = Signal(hbits)
        clip_x_end = Signal(hbits)

        x_idx = Signal(hbits)

        tmp = Signal(32)
        tmp0 = Signal(32)
        tmp1 = Signal(32)
        tmp2 = Signal(32)
        
        self.submodules.fsm = fsm = FSM(reset_state='RESET')

        self.comb += [
            inactive_line_idx.eq(x_idx),

            inactive_line_dat_w.eq(pal_mux.o),
            inactive_line_we.eq(pal_mux.we_o),
            pal_mux.mode.eq(0)
        ]
        
        base_addr = Signal(32)


        fsm.act('RESET',
             If(frame_end,
                wb_ctrl.adr_w.eq(csr_pc.storage),
                wb_ctrl.we.eq(1),
                NextValue(base_addr,csr_pc.storage),
                NextValue(y_counter,0),
                NextState('DECODE0'),
            ),
        )

        fsm.act('IDLE',
            If(frame_end,
                wb_ctrl.adr_w.eq(csr_pc.storage),
                wb_ctrl.we.eq(1),
                NextValue(base_addr,csr_pc.storage),
                NextValue(y_counter,0),
                NextState('DECODE0'),
            ),
            If(buffer_swap,
                wb_ctrl.adr_w.eq(base_addr),
                wb_ctrl.we.eq(1),
                NextState('DECODE0'),
            )
        )

        fsm.delayed_enter('DECODE0', 'DECODE', 1)

        fsm.act('DECODE',
            #NextValue(op_idx,op_idx + 1),
            wb_ctrl.ready.eq(1),

            If(wb_ctrl.valid,
                If(wb_ctrl.instr[28:32] == op.codes['SYNC'],
                    NextValue(y_counter,y_counter + 1),
                    NextState('IDLE'),
                ),
                If(wb_ctrl.instr[28:32] == op.codes['CLIP'],
                    NextValue(clip_x_start, wb_ctrl.instr[0:12]),
                    NextValue(clip_x_end, wb_ctrl.instr[12:24]),
                ),
                If(wb_ctrl.instr[28:32] == op.codes['FILL'],
                    NextValue(tmp, wb_ctrl.instr[0:15]),
                    NextValue(x_idx, clip_x_start),
                    NextState('FILL'),
                ),
                If(wb_ctrl.instr[28:32] == op.codes['BLIT'],
                    If(y_counter >= wb_ctrl.instr[12:24],
                        NextValue(x_idx, wb_ctrl.instr[0:12]), # Load x
                        NextValue(tmp1, wb_ctrl.instr[12:24]),
                        NextValue(tmp0, 8 << wb_ctrl.instr[24:27]),
                        NextValue(tmp, 4 << wb_ctrl.instr[24:27]),
                        NextValue(tmp2, ((4 << wb_ctrl.instr[24:27]) * (y_counter - wb_ctrl.instr[12:24]))),
                        NextState('BLIT_0'), # LOAD Addr
                    ).Else(
                        NextState('SKIP')
                    )
                ),
                If(wb_ctrl.instr[28:32] == op.codes['PUSH'],
                    NextState('PUSH')
                ),
                If(wb_ctrl.instr[28:32] == op.codes['POPJ'],
                    # Handle conditionals
                    If((wb_ctrl.instr[26:28] == 0) |
                    ((wb_ctrl.instr[26:28] == 1) & (y_counter < wb_ctrl.instr[0:12])) |
                    ((wb_ctrl.instr[26:28] == 2) & (y_counter >= wb_ctrl.instr[0:12])),
                        NextValue(stack_port.adr, stack_port.adr - 1),
                        NextState('POPJ_DELAY'),
                    )
                ),
            )
        )

        fsm.act('PUSH',
            wb_ctrl.ready.eq(1),
            If(wb_ctrl.valid,
                NextValue(stack_port.adr, stack_port.adr + 1),
                stack_port.dat_w.eq(wb_ctrl.instr),
                stack_port.we.eq(1),
                NextState('DECODE'),
            )
        )

        fsm.act('SKIP',
            wb_ctrl.ready.eq(1),
            If(wb_ctrl.valid,
                NextState('DECODE')
            )
        )

        fsm.act('BLIT_0',
            wb_ctrl.ready.eq(1),
            If(wb_ctrl.valid,
                NextState('DECODE'),
                If(y_counter < (tmp1 + tmp0),
                    # Address now available for us. Store current op_idx and load in address
                    NextValue(tmp0, wb_ctrl.adr_r),
                    #NextValue(tmp2, (wb_ctrl.instr << 3) * (y_counter - tmp1)),
                    #NextValue(tmp1, ),

                    #NextState('BLIT_CALC'),
                    NextState('BLIT_ACTION'),
                    wb_ctrl.adr_w.eq((wb_ctrl.instr << 3)  + tmp2 >> 3),
                    wb_ctrl.we.eq(1),
                )
            )
        )

        fsm.act('BLIT_CALC',
            If(tmp1 == 0,
            ),
            NextValue(tmp2, tmp2 + tmp),
            NextValue(tmp1, tmp1 - 1),
        )

        cases = {}
        for i in range(8):
            cases[i] = [
                pal_mux.i.eq(wb_ctrl.instr[28-i*4:32-i*4]),
                #inactive_line_dat_w[0:8].eq(wb_ctrl.instr[28-i*4:32-i*4] << 4),
                #inactive_line_dat_w[8:16].eq(wb_ctrl.instr[28-i*4:32-i*4] << 4),
                #inactive_line_dat_w[16:24].eq(wb_ctrl.instr[28-i*4:32-i*4] << 4)
                ]
            
        fsm.act('BLIT_ACTION',
            wb_ctrl.ready.eq(tmp2[0:3] == 7),
            If(wb_ctrl.valid,
                NextValue(tmp2, tmp2 + 1),
                NextValue(x_idx, x_idx+1),
                NextValue(tmp, tmp - 1),
                #inactive_line_we.eq(1),
                pal_mux.we.eq(1),
                If(tmp == 1, 
                    NextState('BLIT_CLEANUP')
                ),
            ),
            Case(tmp2[0:3], cases)
        )

        fsm.act('BLIT_CLEANUP',
            wb_ctrl.adr_w.eq(tmp0),
            wb_ctrl.we.eq(1),
            NextState('DECODE'),
        )

        fsm.act('POPJ_DELAY',
            NextState('POPJ_DELAY0'),
        )
        
        fsm.act('POPJ_DELAY0',
            wb_ctrl.adr_w.eq(stack_port.dat_r),
            wb_ctrl.we.eq(1),
            NextState('DECODE'),
        )

        
        fsm.act('FILL',
            If(x_idx >= (clip_x_end - 1),
                NextState('DECODE')
            ),
            NextValue(x_idx, x_idx+1),
            inactive_line_we.eq(1),
            inactive_line_dat_w[3:8].eq(tmp[0:5]),
            inactive_line_dat_w[11:16].eq(tmp[5:10]),
            inactive_line_dat_w[19:24].eq(tmp[10:15]),
        )

        fsm.delayed_enter('STALL', 'DECODE', 1)

        fsm.act('END',
            If(frame_end,
                NextValue(y_counter,0),
                NextState('IDLE')
            )
        )

class VideoCore(Module, AutoCSR):
    """Video out core

    Generates a video stream from memory.
    """
    def __init__(self, mode="rgb"):
        try:
            dw = 24
        except:
            raise ValueError("Unsupported {} video mode".format(mode))
        
        self.source = source = stream.Endpoint(video_out_layout(dw))  # "output" is a video layout that's dw wide

        self.underflow_enable = CSRStorage()
        self.underflow_update = CSR()
        self.underflow_counter = CSRStatus(32)


        self.submodules.ev = ev.EventManager()
        self.ev.submodules.frame = new_frame = ev.EventSourcePulse(name="newframe",
                                            description="""A New frame is here!""")
        self.ev.finalize()
        

        # # #

        cd = 'video'

        self.submodules.initiator = initiator = Initiator(cd)
        self.submodules.timing = timing = ClockDomainsRenamer(cd)(TimingGenerator())
        self.submodules.ppu = ppu = PPU()

        self.comb += new_frame.trigger.eq(ppu.next_frame)
        self.bus = ppu.bus

        # ctrl path
        self.comb += timing.sink.valid.eq(initiator.source.valid) # if the CSR FIFO data is valid, timing may proceed

        self.comb += [
            # dispatch initiator parameters to timing & dma
            #dma.sink.valid.eq(initiator.source.valid),   # the DMA's parameter input "pushed" from the initiator, so connect the valids
            initiator.source.ready.eq(timing.sink.ready), # timing's parameters come from initiator, but this is "pulled" by timing so connect readys

            # combine timing and dma
            source.valid.eq(timing.source.valid), # our output is valid only when timing's outputs are valid and (when the dma's output is valid or de is low)
              # the "or de is low" thing seems like a hack to fix some edge case??
            # flush dma/timing when disabled
            If(~initiator.source.valid,  # if the initiator's (e.g. CSR) outputs aren't valid
                timing.source.ready.eq(1), # force the outputs to 1 to keep the DMA running
            #    dma.source.ready.eq(1)
            ).Elif(source.valid & source.ready, # else if our DMA output stream has valid data, and is ready to accept addresses
                timing.source.ready.eq(1),  # output stream of timing is ready to go, which kicks off the timing generator...
            #    dma.source.ready.eq(timing.source.de | (mode == "raw"))  # and the DMA's DMAReader source ready is tied to the timing's DE signal
            )
        ]

        # data path
        self.comb += [
            # dispatch initiator parameters to timing & dma
            initiator.source.connect(timing.sink, keep=list_signals(frame_parameter_layout)), # initiator is a compound source, so use "keep" to demux. initiator sources config data to the timer
            
            ppu.sink.hres.eq(timing.sink.hres),
            timing.source.connect(ppu.sink, keep=list_signals(frame_timing_layout)),

            # combine timing and dma
            source.de.eq(timing.source.de),  # manually assign this block's video de, hsync, vsync outputs,, to the respective timing or DMA outputs
            source.hsync.eq(timing.source.hsync),
            source.vsync.eq(timing.source.vsync),
            source.data.eq(ppu.source.data)
        ]

        # underflow detection
        underflow_enable = Signal()
        underflow_update = Signal()
        underflow_counter = Signal(32)
        self.specials += MultiReg(self.underflow_enable.storage, underflow_enable)
        underflow_update_synchronizer = PulseSynchronizer("sys", cd)
        self.submodules += underflow_update_synchronizer
        self.comb += [
            underflow_update_synchronizer.i.eq(self.underflow_update.re),
            underflow_update.eq(underflow_update_synchronizer.o)
        ]
        sync = getattr(self.sync, cd)
        sync += [
            If(underflow_enable,
                If(~source.valid,  # count whenever the source isn't valid...
                    underflow_counter.eq(underflow_counter + 1)
                )
            ).Else(
                underflow_counter.eq(0)
            ),
            If(underflow_update,
                self.underflow_counter.status.eq(underflow_counter)
            )
        ]


