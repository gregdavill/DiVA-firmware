#!/usr/bin/env python3
import sys
import os

from migen import *
from migen.genlib.cdc import MultiReg

from pycrc.algorithms import Crc

from litex.soc.interconnect import stream
from litex.soc.interconnect.stream import EndpointDescription


from litex.soc.cores.uart import RS232PHYTX



from struct import unpack, pack_into

FRAME_BUF_SIZ = 4000
START_FRAME_BYTE = bytes([0x8E])
ESCAPE_BYTE = bytes([0x9E])
END_FRAME_BYTE = bytes([0xAE])
ESCAPED_START_FRAME_BYTE = bytes([0x81])
ESCAPED_ESCAPE_BYTE = bytes([0x91])
ESCAPED_END_FRAME_BYTE = bytes([0xA1])
ccitt_16Table = [
    0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50A5, 0x60C6, 0x70E7,
    0x8108, 0x9129, 0xA14A, 0xB16B, 0xC18C, 0xD1AD, 0xE1CE, 0xF1EF,
    0x1231, 0x0210, 0x3273, 0x2252, 0x52B5, 0x4294, 0x72F7, 0x62D6,
    0x9339, 0x8318, 0xB37B, 0xA35A, 0xD3BD, 0xC39C, 0xF3FF, 0xE3DE,
    0x2462, 0x3443, 0x0420, 0x1401, 0x64E6, 0x74C7, 0x44A4, 0x5485,
    0xA56A, 0xB54B, 0x8528, 0x9509, 0xE5EE, 0xF5CF, 0xC5AC, 0xD58D,
    0x3653, 0x2672, 0x1611, 0x0630, 0x76D7, 0x66F6, 0x5695, 0x46B4,
    0xB75B, 0xA77A, 0x9719, 0x8738, 0xF7DF, 0xE7FE, 0xD79D, 0xC7BC,
    0x48C4, 0x58E5, 0x6886, 0x78A7, 0x0840, 0x1861, 0x2802, 0x3823,
    0xC9CC, 0xD9ED, 0xE98E, 0xF9AF, 0x8948, 0x9969, 0xA90A, 0xB92B,
    0x5AF5, 0x4AD4, 0x7AB7, 0x6A96, 0x1A71, 0x0A50, 0x3A33, 0x2A12,
    0xDBFD, 0xCBDC, 0xFBBF, 0xEB9E, 0x9B79, 0x8B58, 0xBB3B, 0xAB1A,
    0x6CA6, 0x7C87, 0x4CE4, 0x5CC5, 0x2C22, 0x3C03, 0x0C60, 0x1C41,
    0xEDAE, 0xFD8F, 0xCDEC, 0xDDCD, 0xAD2A, 0xBD0B, 0x8D68, 0x9D49,
    0x7E97, 0x6EB6, 0x5ED5, 0x4EF4, 0x3E13, 0x2E32, 0x1E51, 0x0E70,
    0xFF9F, 0xEFBE, 0xDFDD, 0xCFFC, 0xBF1B, 0xAF3A, 0x9F59, 0x8F78,
    0x9188, 0x81A9, 0xB1CA, 0xA1EB, 0xD10C, 0xC12D, 0xF14E, 0xE16F,
    0x1080, 0x00A1, 0x30C2, 0x20E3, 0x5004, 0x4025, 0x7046, 0x6067,
    0x83B9, 0x9398, 0xA3FB, 0xB3DA, 0xC33D, 0xD31C, 0xE37F, 0xF35E,
    0x02B1, 0x1290, 0x22F3, 0x32D2, 0x4235, 0x5214, 0x6277, 0x7256,
    0xB5EA, 0xA5CB, 0x95A8, 0x8589, 0xF56E, 0xE54F, 0xD52C, 0xC50D,
    0x34E2, 0x24C3, 0x14A0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
    0xA7DB, 0xB7FA, 0x8799, 0x97B8, 0xE75F, 0xF77E, 0xC71D, 0xD73C,
    0x26D3, 0x36F2, 0x0691, 0x16B0, 0x6657, 0x7676, 0x4615, 0x5634,
    0xD94C, 0xC96D, 0xF90E, 0xE92F, 0x99C8, 0x89E9, 0xB98A, 0xA9AB,
    0x5844, 0x4865, 0x7806, 0x6827, 0x18C0, 0x08E1, 0x3882, 0x28A3,
    0xCB7D, 0xDB5C, 0xEB3F, 0xFB1E, 0x8BF9, 0x9BD8, 0xABBB, 0xBB9A,
    0x4A75, 0x5A54, 0x6A37, 0x7A16, 0x0AF1, 0x1AD0, 0x2AB3, 0x3A92,
    0xFD2E, 0xED0F, 0xDD6C, 0xCD4D, 0xBDAA, 0xAD8B, 0x9DE8, 0x8DC9,
    0x7C26, 0x6C07, 0x5C64, 0x4C45, 0x3CA2, 0x2C83, 0x1CE0, 0x0CC1,
    0xEF1F, 0xFF3E, 0xCF5D, 0xDF7C, 0xAF9B, 0xBFBA, 0x8FD9, 0x9FF8,
    0x6E17, 0x7E36, 0x4E55, 0x5E74, 0x2E93, 0x3EB2, 0x0ED1, 0x1EF0
]

def ByteCRC16( value, crcin):
    bottom_byte = (crcin << 8) & 0xFFFF
    top_byte = (crcin >> 8) & 0xFFFF
    value = value & 0xFF
    tbl_index = top_byte ^ value & 0xFF
    crcout = bottom_byte ^ ccitt_16Table[tbl_index]
    return crcout

def CalcCRC16Bytes(count, buffer):
    crc = 0x1d0f
    if (not isinstance(buffer, bytes) and not isinstance(buffer, bytearray)):
        raise Exception("Type error in CalcCRC16Bytes")
    for cur_byte in buffer[:count]:
        crc = ByteCRC16(cur_byte, crc)
    return crc


def UINT_32ToByte(inVal, outBuff, outPtr):
	pack_into('>I',outBuff,outPtr,int(inVal))



def flirFrame(seq, fnID, payload=[]):
    sendPayload = bytearray(len(payload)+12)
    pyldPtr = 0
    
    # Write sequence number to first 4 bytes
    UINT_32ToByte(seq, sendPayload, pyldPtr)
    pyldPtr += 4
    
    # Write function ID to second 4 bytes
    UINT_32ToByte(fnID, sendPayload, pyldPtr)
    pyldPtr += 4
    
    # Write 0xFFFFFFFF to third 4 bytes
    UINT_32ToByte(0xFFFFFFFF, sendPayload, pyldPtr)
    pyldPtr += 4
    
    # Copy sendData to payload buffer
    for byte in payload:
        sendPayload[pyldPtr] = byte
        pyldPtr += 1


    temppayload = bytearray([0x00])
    temppayload.extend(sendPayload)
    payload_crc = CalcCRC16Bytes(len(temppayload), temppayload)
    # print("CRC = 0x{:04x}".format(payload_crc))
    temppayload.extend([(payload_crc >> 8) & 0xff])
    temppayload.extend([payload_crc & 0xff])

    packet = bytearray([0x00])
    packet.extend(START_FRAME_BYTE)
    for i in range(0, len(temppayload)):
        if (temppayload[i] == START_FRAME_BYTE[0]):
            packet.extend(ESCAPE_BYTE)
            packet.extend(ESCAPED_START_FRAME_BYTE)
        elif (temppayload[i] == END_FRAME_BYTE[0]):
            packet.extend(ESCAPE_BYTE)
            packet.extend(ESCAPED_END_FRAME_BYTE)
        elif (temppayload[i] == ESCAPE_BYTE[0]):
            packet.extend(ESCAPE_BYTE)
            packet.extend(ESCAPED_ESCAPE_BYTE)
        else:
            packet.extend([temppayload[i]])

    packet.extend(END_FRAME_BYTE)
    #debugprint("sending " + str(len(packet)) + " bytes:" + " ".join(map(lambda b: format(b, "02x"), packet)))
    packet[0] = len(packet)

    return Array(packet)


# Commands to be sent on powerup
flirInitPackets = Array([
    flirFrame(0, 0x0006000D, [0x00, 0x00, 0x00, 0x00]), # Set Display mode Continuous
    #flirFrame(2, 0x00100000,[0x01, 0x00,0x00,0x00,0x01]), # set test pattern?
    #flirFrame(3, 0x00000013, [0x00,0x00,0x00,0x00]), # enable test ramp

    flirFrame(12, 0x0006000F,[0x00,0x00,0x00,0x00]), # colour

    flirFrame(19, 0x00060004,[0x00,0x00,0x00,0x00]), # Analog off
    flirFrame(20, 0x00060006,[0x00,0x00,0x00,0x02]), # Output format = YCbCr
    
    flirFrame(40, 0x0006000A,[0x00,0x00,0x00,0x00, 0x00,0x00,0x00,0x00]), # RGB888
    flirFrame(41, 0x00060008,[0x00,0x00,0x00,0x00, 0x00,0x00,0x00,0x00, 0x00,0x00,0x00,0x00]), # YCBCR Muxed
    
    flirFrame(50, 0x0006000C), # Apply Settings
    
    flirFrame(90, 0x000B0003,[0x00,0x00,0x00,0x04]), # LUT select Rainbow
    flirFrame(91, 0x000B0001,[0x00,0x00,0x00,0x01]), # Enable Colouriser
    
    flirFrame(100, 0x0006000F,[0x00,0x00,0x00,0x02]), # colour
    flirFrame(110, 0x0000000B,[0x00,0x00,0x00,0x00]), # Averager: disable (60Hz)


    flirFrame(120, 0x00050007), # FFC

    


#    [0x00, 0x06, 0x00, 0x0D, 0x00, 0x00, 0x00, 0x00],

])


flirLUTPackets = Array([
    flirFrame(100, 0x000B0003,[0x00,0x00,0x00,0x00]), # LUT select Rainbow
    flirFrame(100, 0x000B0003,[0x00,0x00,0x00,0x01]), # LUT select Rainbow
    flirFrame(100, 0x000B0003,[0x00,0x00,0x00,0x02]), # LUT select Rainbow
    flirFrame(100, 0x000B0003,[0x00,0x00,0x00,0x03]), # LUT select Rainbow
    flirFrame(100, 0x000B0003,[0x00,0x00,0x00,0x04]), # LUT select Rainbow
    flirFrame(100, 0x000B0003,[0x00,0x00,0x00,0x05]), # LUT select Rainbow
    flirFrame(100, 0x000B0003,[0x00,0x00,0x00,0x06]), # LUT select Rainbow
    flirFrame(100, 0x000B0003,[0x00,0x00,0x00,0x07]), # LUT select Rainbow
    flirFrame(100, 0x000B0003,[0x00,0x00,0x00,0x08]), # LUT select Rainbow
    flirFrame(100, 0x000B0003,[0x00,0x00,0x00,0x09]), # LUT select Rainbow
])


class BosonConfig(Module):
    def __init__(self, pads, clk_freq):
        baudrate=921600
        tuning_word = int((baudrate/clk_freq)*2**32)

        self.button = button = Signal()
        self.submodules.tx = tx = RS232PHYTX(pads, tuning_word)
        #self.sink = self.tx.sink

        self.submodules.fsm = fsm = FSM(reset_state="STARTUP")

        fsmCounter = Signal(max=int((clk_freq)*60), reset=int((clk_freq)*(300e-3)))
        currentPacket = Signal(max=12, reset=0)
        currentByte = Signal(max=64, reset=1)


        fsm.act("STARTUP",
            NextValue(fsmCounter, int((clk_freq)*(4))),
            NextState("WAIT"),
        )

        fsm.act("WAIT",
            NextValue(fsmCounter, fsmCounter - 1),
            If(fsmCounter == 0,
                NextState("XMIT"),
                NextValue(fsmCounter, 0)
            ),
        )


        fsm.act("XMIT",
            If(currentByte >= (flirInitPackets[currentPacket][0]),
                If(currentPacket >= (len(flirInitPackets) - 1),
                    NextValue(currentPacket,0),
                    NextState("DONE"),
                ).Else(
                    NextValue(currentPacket, currentPacket + 1),
                    NextValue(fsmCounter, int((clk_freq)*(200e-3))),
                    NextState("WAIT"),
                ),
                NextValue(currentByte, 1),
            ).Else(
                tx.sink.data.eq(flirInitPackets[currentPacket][currentByte]),
                tx.sink.valid.eq(1),
                If(tx.sink.ready,
                    NextValue(currentByte, currentByte + 1)
                )
            )
        ) 

        fsm.act("DONE",
            # done
            If(button & (fsmCounter == 0), 
                NextState("BUTTON")
            ),

            If(fsmCounter > 0,
                NextValue(fsmCounter, fsmCounter - 1)
            )
        )

        fsm.act("HOLD",
            # done
            If(~button, 
                NextState("DONE"),
                NextValue(fsmCounter, int((clk_freq)*(25e-3))),
            ),            
        )

        fsm.act("BUTTON",
            If(currentByte >= (flirLUTPackets[currentPacket][0]),
                If(currentPacket >= (len(flirLUTPackets) - 1),
                    NextValue(currentPacket,0),
                    NextState("HOLD"),
                ).Else(
                    NextValue(currentPacket, currentPacket + 1),
                    NextState("HOLD"),
                ),
                NextValue(currentByte, 1),
            ).Else(
                tx.sink.data.eq(flirLUTPackets[currentPacket][currentByte]),
                tx.sink.valid.eq(1),
                If(tx.sink.ready,
                    NextValue(currentByte, currentByte + 1)
                )
            )
        ) 






class boson_rx(Module):
    def __init__(self, pads):
        self.source = source = stream.Endpoint(EndpointDescription([("data", 24)]))
        self.sync_out = Signal()
        

        vsync_ = Signal()
        vsync_falling = Signal()

        data = Signal(24)
        
        luminance_delay = Signal(8)
        
        valid = Signal(2)


        pixel_counter = Signal(20)
        
        self.sync += [
            source.data.eq(data),
            source.valid.eq(valid[1]),
        ]

        self.comb += [
            vsync_falling.eq(~pads.vsync & vsync_)
        ]


        self.sync += [

            luminance_delay.eq(pads.data[0:8]),
            data[0:8].eq(luminance_delay),
            If(~pixel_counter[0],        
                 data[8:16].eq(pads.data[8:16]),
            #    data[0:12].eq(pads.data[0:12]),
            ).Else (
                 data[16:24].eq(pads.data[8:16]),
            #    data[12:24].eq(pads.data[0:12]),
            ),
            #pixel_en.eq(Cat(pads.valid, valid)
            #data.eq(pads.data[0:15]),
            
            valid.eq(Cat(pads.valid, valid[0]))
        ]

        self.sync += [
            vsync_.eq(pads.vsync),

            If(vsync_falling,
                pixel_counter.eq(0),
            ).Else(
                pixel_counter.eq(pixel_counter + 1)
            ),
            self.sync_out.eq(pads.vsync),
           
        ]



# Convert the Boson clock pin Signal into a clock domain
class boson_clk(Module):
    def __init__(self, clk_pad):
        self.clock_domains.cd_boson_rx = ClockDomain()        
        self.comb += self.cd_boson_rx.clk.eq(~clk_pad)


class Boson(Module):
    def __init__(self, platform, pads, clk_freq):
        

        
        self.submodules.clk = boson_clk(pads.clk)
        self.submodules.rx = ClockDomainsRenamer("boson_rx")(boson_rx(pads))
        self.source = self.rx.source


        
        self.sync_out = Signal()
        reg_sync = MultiReg(self.rx.sync_out, self.sync_out)
        self.specials += reg_sync


        self.submodules.conf = ClockDomainsRenamer("sys")(BosonConfig(pads, clk_freq))

        button = platform.request("button")

        
        self.comb += [
            self.conf.button.eq(~button.a),
            #self.sync_out.eq(button.b),
        ]

    
