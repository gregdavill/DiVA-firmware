# This file is Copyright (c) 2020 Gregory Davill <greg.davill@gmail.com>
# License: BSD

from migen import *
from litex.soc.interconnect.stream import Endpoint
from rtl.edge_detect import EdgeDetect

from litex.soc.interconnect.csr import AutoCSR, CSR, CSRStorage
from litex.soc.interconnect.stream import AsyncFIFO

class BufferedCSRBlock(Module, AutoCSR):
    def __init__(self, params):

        # Sync signal, 
        self.csr_sync = csr_sync = Signal()

        # Populate CSR storage
        for name,size in params:
            csr = CSRStorage(name=name, size=size)
            setattr(self, f'{name}_csr', csr)

            # output signal
            sig = Signal(size, name=name)
            setattr(self, f'{name}', sig)

        # CSR control
        self.update_values = CSR(1)

        # fifo
        self.submodules.fifo = fifo = ClockDomainsRenamer({"read":"video","write":"sys"})(AsyncFIFO(params, depth=4))
        
        for name,size in params:
            self.comb += getattr(fifo.sink, name).eq(getattr(self, f'{name}_csr').storage)
            self.sync.video += [
                fifo.source.ready.eq(csr_sync),
                If(csr_sync,
                    If(fifo.source.valid,
                        getattr(self, f'{name}').eq(getattr(fifo.source, name)),
                    )
                )
            ]

        self.comb += [
            fifo.sink.valid.eq(self.update_values.re),
        ]
     