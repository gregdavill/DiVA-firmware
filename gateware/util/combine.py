#!/usr/bin/env python3

import argparse
import os
import struct
import binascii


def CombineBinaryFiles(flash_regions_final):
    flash_regions = {}

    offset = int("0x00080000", 16)
    for filename, base in flash_regions_final.items():
        base = int(base, 16)
        new_address = base - offset
        print(f'Moving {filename} from 0x{base:08x} to 0x{new_address:08x}')
        flash_regions[filename] = new_address


    output_file = 'combine.dfu'
    total_len = 0
    with open(output_file, "wb") as f:
        for filename, base in flash_regions.items():
            data = open(filename, "rb").read()
            #crc = binascii.crc32(data)
            
            print(f' ')
            print(f'Inserting {filename:60}')
            print(f'  Start address: 0x{base + offset:08x}')
            
            print(f'  Length       : 0x{len(data):08x} bytes')
            print(f'  Gap          : 0x{base - total_len:08x} bytes')
            print(f'           data: ' + f' '.join(f'{i:02x}' for i in data[:16]))
            f.seek(base)
            f.write(data)

            total_len += len(data)

