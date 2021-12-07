from migen import Module
from litex.soc.interconnect.csr import AutoCSR, CSRStatus, CSRStorage
from litex.soc.integration.doc import ModuleDoc

class Button(Module, AutoCSR):
    def __init__(self, pad):
        self.intro = ModuleDoc("""Button

        This block simply provides CPU readable input.  It has
        one register which returns status of the Input button state connected to this pins.
        """)
        self.i  = CSRStatus(1, description="Input value from user button")

        self.comb += [
            self.i.status.eq(pad)
        ]
