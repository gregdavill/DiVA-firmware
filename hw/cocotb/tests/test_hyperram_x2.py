# Simple tests for hyperRAM
import cocotb
import logging
from cocotb import SimLog
from cocotb.triggers import RisingEdge, Edge, Timer, ClockCycles, FallingEdge
from cocotb.result import TestError
from cocotb.triggers import Timer
from cocotb.result import TestFailure
from cocotb.clock import Clock
import random
from cocotb.binary import BinaryValue

from wishbone_driver import WishboneMaster, WBOp
from hyperbus_monitor import HyperBusSubordinate, HyperBus

class WbGpio(object):
    """ test class for Spi2KszTest
    """
    LOGLEVEL = logging.DEBUG

    # clock frequency is 100Mhz
    PERIOD = (10, "ns")

    STATUSADDR = 0
    DIRADDR    = 1
    READADDR   = 2
    WRITEADDR  = 3

    def __init__(self, dut):
        self.dut = dut
        self.log = SimLog("wbGpio.{}".format(self.__class__.__name__))
        self.dut._log.setLevel(self.LOGLEVEL)
        self.log.setLevel(self.LOGLEVEL)

        self._clock_thread = cocotb.fork(self.custom_clock(self.dut.clock_2x_in, 10, 0))
        self._clock_90_thread = cocotb.fork(self.custom_clock(self.dut.clock_2x_in_90, 10, 5))

        self.wbs = WishboneMaster(dut, "wishbone", dut.clock,
                          width=32,   # size of data bus
                          timeout=10, # in clock cycle number
                          signals_dict={"cyc":  "cyc",
                                        "stb":  "stb",
                                        "sel":  "sel",
                                        "we":   "we",
                                        "adr":  "adr",
                                        "datwr":"dat_w",
                                        "datrd":"dat_r",
                                        "ack":  "ack" })

        self.hyperbus = HyperBusSubordinate(dut, "hyperRAM", dut.hyperRAM_clk_p,  reset=self.dut.reset,
                                                signals_dict ={"dq" : "dq",
                                                               "rwds" : "rwds",
                                                               "cs" : "cs_n" })
    def get_dut_version_str(self):
        return "{}".format(self.dut.test_name)

    @cocotb.coroutine
    def custom_clock(self, signal, period, initial):
        # pre-construct triggers for performance
        high_time = Timer(period, units="ns")
        low_time = Timer(period, units="ns")
        yield Timer(initial, units="ns")
        while True:
            signal <= 1
            yield high_time
            signal <= 0
            yield low_time

    @cocotb.coroutine
    def reset(self):
        self.dut.reset <= 1
        short_per = Timer(50, units="ns")
        yield short_per
        self.dut.reset <= 1
        yield short_per
        self.dut.reset <= 0
        yield short_per

    @cocotb.coroutine
    def hr_recieve(self, data):
        
        bits = ""

        for bit in range(6):
            value = yield self.hyperbus.wait_for_recv(timeout=250e3)
            if value == None:
                raise TimeoutError("Timeout waiting for CA bits")
            #self.log.info("%s" % value)
            bits += str(value['dq'])
            
        ca_register = BinaryValue(n_bits=48, value=bits, bigEndian=False)
        self.log.info("Command-Address: %s" % "{0:#0{1}x}".format(ca_register.integer, 14))
        
        # Decode Command/Address
        read_writen = ca_register[47]
        address_space = ca_register[46]
        burst_type = ca_register[45]
        address = ca_register[44:16] << 3
        address += ca_register[2:0]

        self.log.info(" - Type:            %s" % ("Read" if read_writen == 1 else "Write"))
        self.log.info(" - Address Space:   %s" % ("Register" if address_space == 1 else "DRAM"))
        self.log.info(" - Burst Type:      %s" % ("Linear" if burst_type == 1 else "Wrapped"))
        self.log.info(" - Address:         %s" % "{0:#0{1}x}".format(address, 10))

        if read_writen == 1:
            latency = 22
            for i in range(latency):
                yield Edge(self.hyperbus.clock)
                if latency-i < 8:
                    self.dut.hyperRAM_rwds = 0

            # RAM drives DQ at a fixed delay around 6ns from edge
            dq_delay = 6

            for d in data:
                word = BinaryValue(d, 32, bigEndian=False)

                yield Edge(self.hyperbus.clock)
                yield Timer(dq_delay, "ns")
                self.dut.hyperRAM_dq = word[31:24]
                self.dut.hyperRAM_rwds = 1
                
                yield Edge(self.hyperbus.clock)
                yield Timer(dq_delay, "ns")
                self.dut.hyperRAM_dq = word[23:16]
                self.dut.hyperRAM_rwds = 0

                yield Edge(self.hyperbus.clock)
                yield Timer(dq_delay, "ns")
                self.dut.hyperRAM_dq = word[15:8]
                self.dut.hyperRAM_rwds = 1
                
                yield Edge(self.hyperbus.clock)
                yield Timer(dq_delay, "ns")
                self.dut.hyperRAM_dq = word[7:0]
                self.dut.hyperRAM_rwds = 0
            
            self.dut.hyperRAM_rwds = 0
            yield Timer(50, "ns")


            self.dut.hyperRAM_rwds = BinaryValue('z')
            self.dut.hyperRAM_dq = BinaryValue('zzzzzzzz')
        
        else:    
            latency = 22
            for i in range(latency):
                yield Edge(self.hyperbus.clock)

            bits = ""

            for bit in range(4):
                value = yield self.hyperbus._monitor_recv()
                self.log.info("%s" % value)
                bits += str(value['dq'])
                
            #dq_reg = BinaryValue(n_bits=32, value=bits, bigEndian=False)
            #self.log.info("data: %s" % "{0:#0{1}x}".format(dq_reg.integer, 10))
            

            yield Timer(500, 'ns')
            
            #raise TestFailure("Bad data")

            #for d in data:
            word = BinaryValue(data[0], 16, bigEndian=False)

            d = BinaryValue(bits[0:16], 16, bigEndian=False).integer
            if d != word:
                raise TestFailure("data %s != %s" % ("{0:#0{1}x}".format(word.integer,6), "{0:#0{1}x}".format(d,6)))
    
            word = BinaryValue(data[1], 16, bigEndian=False)

            d = BinaryValue(bits[16:32], 16, bigEndian=False).integer
            if d != word:
                raise TestFailure("data %s != %s" % ("{0:#0{1}x}".format(word.integer,6), "{0:#0{1}x}".format(d,6)))
    

                # check

            

        


@cocotb.test()
def test_read(dut):
    wbgpio = WbGpio(dut)
    yield wbgpio.reset()
    
    

    hyperram = cocotb.fork(wbgpio.hr_recieve([0x00112233]))
    wbRes = yield [Timer(5000, units='ns'), wbgpio.wbs.send_cycle([WBOp(0)])]
    
    if wbRes[0].datrd != 0x00112233:
        raise TestFailure("data %s != 0x00112233" % "{0:#0{1}x}".format(wbRes[0].datrd.integer,10))
    
    dut.hyperRAM_dq = BinaryValue('zzzzzzzz')
    yield Timer(100, 'ns')


@cocotb.test()
def test_read_dual(dut):
    wbgpio = WbGpio(dut)
    yield wbgpio.reset()
    
    hyperram = cocotb.fork(wbgpio.hr_recieve([0x00112233,0x44556677]))
    wbRes = yield [Timer(5000, units='ns'), wbgpio.wbs.send_cycle([WBOp(0), WBOp(1)])]
    
    if wbRes[0].datrd != 0x00112233:
        raise TestFailure("data %s != 0x00112233" % "{0:#0{1}x}".format(wbRes[0].datrd.integer,10))
    
    dut.hyperRAM_dq = BinaryValue('zzzzzzzz')
    yield Timer(100, 'ns')

@cocotb.test()
def test_write(dut):
    wbgpio = WbGpio(dut)
    yield wbgpio.reset()
    
    hyperram = cocotb.fork(wbgpio.hr_recieve([0x0011,0x2233]))
    wbRes = yield wbgpio.wbs.send_cycle([WBOp(0, dat=0x00112233, sel=0xF)])

    yield Timer(400, 'ns')
    dut.hyperRAM_dq = BinaryValue('zzzzzzzz')
    
    #if wbRes[0].datrd != 0x00112233:
    #    raise TestFailure("data %s != 0x00112233" % "{0:#0{1}x}".format(wbRes[0].datrd.integer,10))
    