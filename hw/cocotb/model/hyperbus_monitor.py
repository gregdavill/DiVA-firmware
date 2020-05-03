
import cocotb
from itertools import repeat
from cocotb.decorators  import coroutine
from cocotb.monitors    import BusMonitor
from cocotb.drivers     import BusDriver
from cocotb.triggers    import Edge, FallingEdge, RisingEdge
from cocotb.result      import TestFailure
from cocotb.decorators  import public  
from cocotb.triggers import Timer
from cocotb.binary import BinaryValue


class HyperBus(BusMonitor, BusDriver):
    """HyperBus
    """
    
    _signals = ["dq", "rwds", "clk", "cs"]

    def __init__(self, entity, name, clock, signals_dict=None, **kwargs):
        if signals_dict is not None:
            self._signals=signals_dict

        reset = kwargs.pop('reset', None)
        BusMonitor.__init__(self, entity, name, clock, reset=reset, **kwargs)
        BusDriver.__init__(self, entity, name, clock, **kwargs)
        # Drive some sensible defaults (setimmediatevalue to avoid x asserts)
        self.bus.dq.setimmediatevalue(BinaryValue('zzzzzzzz')) 
        self.bus.rwds.setimmediatevalue(BinaryValue('z')) 
        
    

            

class HyperBusSubordinate(HyperBus):
    """HyperBus subordinate
    """
    
    
    def __init__(self, entity, name, clock, **kwargs):
        #init instance variables
        self._acked_ops      = 0  # ack cntr. wait for equality with
                                  # number of Ops before releasing lock
        self._res_buf        = [] # save readdata/ack/err/rty
        self._clk_cycle_count = 0
        self._cycle          = False
        self._lastTime       = 0
        self._stallCount     = 0   
        HyperBus.__init__(self, entity, name, clock, **kwargs)     


    @coroutine
    def _driver_send(self, transaction, rwds='zz', sync=True):
        """Implementation for BusDriver.

        Args:
            transaction: The transaction to send.
            sync (bool, optional): Synchronize the transfer by waiting for a rising edge.
        """

        timeout = Timer(50, 'ns')
        # RAM drives DQ at a fixed delay around 6ns from edge
        dq_delay = 6


        self.log.debug("%s" % transaction)

        trig = yield [RisingEdge(self.clock), timeout]
        if trig == timeout:
            raise TimeoutError()
        else:
            yield Timer(dq_delay, 'ns')
            self.bus.dq <= transaction[15:8]
            self.bus.rwds <= BinaryValue(rwds[1])

        trig = yield [FallingEdge(self.clock), timeout]
        if trig == timeout:
            raise TimeoutError()
        else:
            yield Timer(dq_delay, 'ns')
            self.bus.dq <= transaction[7:0]
            self.bus.rwds <= BinaryValue(rwds[0])



    @coroutine
    def _monitor_recv(self):
        while True:

            # Handle reset condition
            while str(self._reset) == "z":
                yield Timer(1, "ns")
            while self.in_reset:
                yield FallingEdge(self._reset)

            # Wait for next CS edge
            if int(self.bus.cs) == 1:
                self.log.debug("Wait for CS fall")
                yield FallingEdge(self.bus.cs)
                self.log.debug("CS falling edge")

            # while in a transaction we can watch for data or end of transaction
            while int(self.bus.cs) == 0:
                trig = yield [Edge(self.clock), Edge(self.bus.cs)]
                if trig == Edge(self.clock):
                    dq   = str(self.bus.dq)
                    rwds = str(self.bus.rwds)
                    values_recv = {"dq": dq, "rwds": rwds}
                    self.log.debug("data: %s" % values_recv) 
                    self._recv(values_recv)
                else:
                    self.log.debug("CS rising edge")


           
            
