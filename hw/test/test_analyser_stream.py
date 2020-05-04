#!/usr/bin/env python3

import random
import time
from litex import RemoteClient

from litescope.software.driver.analyzer import LiteScopeAnalyzerDriver

def print_id():
    # get identifier
    fpga_id = ""
    for i in range(256):
        c = chr(wb.read(wb.bases.identifier_mem + 4*i) & 0xff)
        fpga_id += c
        if c == "\0":
            break
    print("fpga_id: " + fpga_id)


wb = RemoteClient(csr_csv='../build/csr.csv')
wb.open()
print_id()
# # #



wb.regs.hyperram_reader_boson_enable.write(0)
time.sleep(0.5)

wb.regs.hyperram_reader_boson_transfer_size.write(640*512)
wb.regs.hyperram_reader_boson_enable.write(0)

#analyzer = LiteScopeAnalyzerDriver(wb.regs, "analyzer", debug=True)
#analyzer.configure_trigger(cond={"hyperram_hyperramx2_bus_adr": 640})
#analyzer.add_trigger(cond={"hyperram_reader_boson_sink_valid": 0})
#analyzer.add_trigger(cond={"hyperram_reader_boson_sink_ready": 1})
#analyzer.run(offset=32 , length=128)


#
#analyzer.wait_done()
#analyzer.upload()
#analyzer.save("dump.vcd")

# # #


wb.close()