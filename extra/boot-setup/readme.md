# DiVA Initial Setup Guide

DiVA or the Digital Video Adapter is an addon board for the Boson LWIR core from FLIR.
It features an FPGA that performs the video conversion from the camera to a Digital Video Interface. In order for this to function you will need to load the initial firmware onto the device.

The board is designed to be user updateable in the field over the USB connection. In order to accomplish this we need to load a bootloader onto tho device. 

In order to simplify everything, tools from [Open Tool Forge](https://github.com/open-tool-forge/fpga-toolchain/releases) have been included under `/bin` for Linux and Windows 

## Initial device programming

1. Connect the programming jig to the computer.


2. Place a PCB into the programer, do not connect USB to the PCB, the programmer will supply power.


3. Run this command: 
```console 
$ ./bin/ecpprog DiVA-foboot.bit
```

4. Remove the board from the programmer, and then connect it via USB, while holding down the top button.


5. Run dfu-util to load the application firmware and gateware.
```console 
$ dfu-util -D DiVA-fw.bit
```

The board will now have a bootloader and it's application firmware loaded.

## Further testing

1. Connect a cable from the board to a monitor, you sholud see an image on the screen
2. Unplug from USB and connect a camera to the board, and fasten the board with 3 M1.6 screws.
3. When you power the board back up you should see an image from the thermal camera, pressing the bottom button will cycle through the on-board palletes on the camera, and holding the bottom button will toggle full-screen scaling.


## Troubleshooting

If you have errors using `dfu-util`, on linux you may need to load some udev rules, using this command, then reconnect the board: 
```console 
$ cp extra/udev-rules/20-diva-bootloader.rules /etc/udev/rules.d/
```