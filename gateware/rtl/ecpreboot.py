from migen import Module, Signal, If, Instance
from litex.soc.integration.doc import ModuleDoc
from litex.soc.interconnect.csr import AutoCSR, CSRStatus, CSRStorage, CSRField

class ECPReboot(Module, AutoCSR):
    def __init__(self, parent):

        self.ctrl = CSRStorage(fields=[
            CSRField("image", size=2, description="""
                        Which image to reboot to.  ``SB_WARMBOOT`` supports four images that
                        are configured at FPGA startup.  The bootloader is image 0, so set
                        these bits to 0 to reboot back into the bootloader.
                        """),
            CSRField("key", size=6, description="""
                        A reboot key used to prevent accidental reboots when writing to random
                        areas of memory.  To initiate a reboot, set this to ``0b101011``.""")
        ], description="""
                Provides support for rebooting the FPGA.  You can select which of the four images
                to reboot to, just be sure to OR the image number with ``0xac``.  For example,
                to reboot to the bootloader (image 0), write ``0xac``` to this register."""
        )
        self.addr = CSRStorage(size=32, description="""
                This sets the reset vector for the VexRiscv.  This address will be used whenever
                the CPU is reset, for example through a debug bridge.  You should update this
                address whenever you load a new program, to enable the debugger to run ``mon reset``
                """
            )
        do_reset = Signal()
        self.comb += [
            # "Reset Key" is 0xac (0b101011xx)
            do_reset.eq(self.ctrl.storage[2] & self.ctrl.storage[3] & ~self.ctrl.storage[4]
                      & self.ctrl.storage[5] & ~self.ctrl.storage[6] & self.ctrl.storage[7])
        ]

        reset_latch = Signal(reset=0)
        self.sync += [
            reset_latch.eq(do_reset | reset_latch)
        ]

        rst = parent.platform.request("rst_n")
        self.comb += [
            rst.eq(~reset_latch)
        ]
        
        parent.config["BITSTREAM_SYNC_HEADER1"] = 0x7e99aa7e
        parent.config["BITSTREAM_SYNC_HEADER2"] = 0x7eaa997e
