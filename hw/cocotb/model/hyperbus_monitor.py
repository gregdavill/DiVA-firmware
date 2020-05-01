
import cocotb
from itertools import repeat
from cocotb.decorators  import coroutine
from cocotb.monitors    import BusMonitor
from cocotb.triggers    import Edge
from cocotb.result      import TestFailure
from cocotb.decorators  import public  
from cocotb.binary import BinaryValue


class HyperBus(BusMonitor):
    """HyperBus
    """
    
    _signals = ["dq", "rwds", "clk", "cs"]

    def __init__(self, entity, name, clock, signals_dict=None, **kwargs):
        if signals_dict is not None:
            self._signals=signals_dict
        BusMonitor.__init__(self, entity, name, clock, **kwargs)
        # Drive some sensible defaults (setimmediatevalue to avoid x asserts)
        #self.bus.dq.setimmediatevalue(BinaryValue('zzzzzzzz')) 
    

            

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
    def _monitor_recv(self):
        dq = BinaryValue(n_bits=8)
        rwds = BinaryValue(n_bits=1)

        while True:
            yield Edge(self.clock)
            dq = self.bus.dq.value
            rwds = self.bus.rwds.value

            if self.bus.cs == 0:
                return {"dq":dq, "rwds":rwds}
            
            