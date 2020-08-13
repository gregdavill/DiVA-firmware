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


for i in range(8):
    wb.write(0x10000000 + i*4, i)
    print(hex(wb.read(0x10000000 + i*4)))


# # #

wb.close()