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

def io_delay(c):
    wb.regs.hyperram_io_loadn.write(0)
    wb.regs.hyperram_io_loadn.write(1)
    wb.regs.hyperram_io_direction.write(0)

    for _ in range(c):
        wb.regs.hyperram_io_move.write(0)
        wb.regs.hyperram_io_move.write(1)

def clk_delay(c):
    wb.regs.hyperram_clk_loadn.write(0)
    wb.regs.hyperram_clk_loadn.write(1)
    wb.regs.hyperram_clk_direction.write(0)

    for _ in range(c):
        wb.regs.hyperram_clk_move.write(0)
        wb.regs.hyperram_clk_move.write(1)    


io_delay(0)
clk_delay(0)

i = 0xFFAABBCC

while(1):
    wb.regs.crg_phase_sel.write(0)
    wb.regs.crg_phase_dir.write(0)
    wb.regs.crg_phase_step.write(1)
    wb.regs.crg_phase_step.write(0)

    wb.write(0x10000000,i)
    value = wb.read(0x10000000)

    print(f"{hex(value)}")

    if value != 0:
        break


# # #

wb.close()