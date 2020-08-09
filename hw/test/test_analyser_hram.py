#!/usr/bin/env python3

import random
import time
from litex import RemoteClient

from litescope.software.driver.analyzer import LiteScopeAnalyzerDriver

wb = RemoteClient(csr_csv='../build/csr.csv')
wb.open()

# # #



# get identifier
fpga_id = ""
for i in range(256):
    c = chr(wb.read(wb.bases.identifier_mem + 4*i) & 0xff)
    fpga_id += c
    if c == "\0":
        break
print("fpga_id: " + fpga_id)



#while(1):
#    wb.regs.crg_phase_sel.write(0)
#    wb.regs.crg_phase_dir.write(0)
#    wb.regs.crg_phase_step.write(1)
#    wb.regs.crg_phase_step.write(0)
#
#    wb.write(0x10000000,0xA5a5a5a5)
#    wb.read(0x10000000)

wb.regs.writer_enable.write(0)
wb.regs.writer_burst_size.write(16)
wb.regs.writer_transfer_size.write(800*2)

for i in range(8):
    wb.write(0x10000000 + i*4, i)



wb.regs.writer_enable.write(1)

analyzer = LiteScopeAnalyzerDriver(wb.regs, "analyzer", debug=True)
analyzer.configure_trigger(cond={"hyperram_hyperramx2_bus_cyc": 1,"hyperram_hyperramx2_bus_we": 0},)
analyzer.run(offset=2 , length=32)
analyzer.run()

analyzer.wait_done()
analyzer.upload()
analyzer.save("dump.vcd")

# # #

wb.close()