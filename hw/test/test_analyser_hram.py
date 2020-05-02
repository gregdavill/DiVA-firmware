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


wb.regs.test_loadn.write(1)
wb.regs.test_direction.write(1)


#wb.regs.crg_phase_load.write(0)
#wb.regs.crg_phase_load.write(1)


wb.regs.crg_phase_sel.write(0)
wb.regs.crg_phase_dir.write(0)


analyzer = LiteScopeAnalyzerDriver(wb.regs, "analyzer", debug=True)
analyzer.configure_trigger(cond={"hyperram_bus_cyc": 1},)
analyzer.run(offset=8 , length=32)

for _ in range(128):
    ...
    wb.regs.test_move.write(0)
    wb.regs.test_move.write(1)

for i in range(10000):
    #wb.regs.test_move.write(0)
    #wb.regs.test_move.write(1)
    wb.regs.crg_phase_step.write(1)
    wb.regs.crg_phase_step.write(0)

    #wb.write(0x10000000, 0x00112233)
    print("{0:#0{1}x}".format(wb.read(0x10000000),10))
    #wb.read(0x10000000)
    #    print('.')
#wb.regs.reader0_burst_size.write(64)
#wb.regs.reader0_start_address.write(0x10000000>>2)
#while True:
#wb.regs.reader0_enable.write(1)

#while wb.regs.reader0_busy.read() == 1:
#    ...




#
analyzer.wait_done()
analyzer.upload()
analyzer.save("dump.vcd")

# # #

wb.close()