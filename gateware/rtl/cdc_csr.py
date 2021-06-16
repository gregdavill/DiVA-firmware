
from migen import *
from migen.fhdl.specials import TSTriple
from migen.fhdl.decorators import ClockDomainsRenamer


#from litex.soc.interconnect.wishbone2csr import WB2CSR
from litex.soc.interconnect.csr_bus import CSRBank
from litex.soc.interconnect.csr import AutoCSR

from litex.soc.interconnect.stream import AsyncFIFO, SyncFIFO
from migen.genlib.cdc import BusSynchronizer, PulseSynchronizer, MultiReg



from litex.soc.interconnect import csr_bus, wishbone
from migen.genlib.fsm import FSM, NextState

from valentyusb.usbcore.cpu import eptri

import os

from litex.soc.interconnect.csr import _make_gatherer, _CSRBase, csrprefix

class CSRClockDomainWrapper(Module):
    def get_csr(self):
        return self.usb.get_csrs()

    def __init__(self, usb_iobuf, platform):
        self.bus = wishbone.Interface()
        
        usb12_bus = wishbone.Interface()
        # create a new custom CSR bus
        self.submodules.csr = ClockDomainsRenamer({'sys':'usb_12'})(wishbone.Wishbone2CSR(usb12_bus))
        csr_cpu = self.csr.csr

        self.submodules.usb = usb = ClockDomainsRenamer({'sys':'usb_12'})(eptri.TriEndpointInterface(usb_iobuf, debug=False))
        csrs = self.usb.get_csrs()
        # create a CSRBank for the eptri CSRs
        self.submodules.csr_bank = ClockDomainsRenamer({'sys':'usb_12'})(CSRBank(csrs, 0,  self.csr.csr))
        
        
        self.specials += Instance("wb_cdc",
            i_wbm_clk=ClockSignal(),
            i_wbm_rst=ResetSignal(),
            i_wbm_adr_i=self.bus.adr,
            i_wbm_dat_i=self.bus.dat_w,
            o_wbm_dat_o=self.bus.dat_r,
            i_wbm_we_i=self.bus.we,
            i_wbm_sel_i=self.bus.sel,
            i_wbm_stb_i=self.bus.stb,
            o_wbm_ack_o=self.bus.ack,
            #o_wbm_err_o=self.bus.err,
            #o_wbm_rty_o=,
            i_wbm_cyc_i=self.bus.cyc,

            i_wbs_clk=ClockSignal("usb_12"),
            i_wbs_rst=ResetSignal("usb_12"),
            o_wbs_adr_o=usb12_bus.adr,
            i_wbs_dat_i=usb12_bus.dat_r,
            o_wbs_dat_o=usb12_bus.dat_w,
            o_wbs_we_o=usb12_bus.we,
            o_wbs_sel_o=usb12_bus.sel,
            o_wbs_stb_o=usb12_bus.stb,
            i_wbs_ack_i=usb12_bus.ack,
            #i_wbs_err_i=usb12_bus.err,
            #i_wbs_rty_i=0,
            o_wbs_cyc_o=usb12_bus.cyc)

        # add verilog sources
        platform.add_source_dir("{}/rtl/verilog".format(os.getcwd()))

        # Patch interrupt through
        self.irq = Signal()
        self.specials += MultiReg(usb.ev.irq, self.irq)
        