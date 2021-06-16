include ../include/generated/variables.mak
include $(SOC_DIRECTORY)/software/common.mak

CFLAGS += -O3 -I$(DIVA-FW_DIRECTORY)/include -fdata-sections -ffunction-sections
CFLAGS += -I$(TINYUSB_DIRECTORY)/../deps/tinyusb/src -I$(TINYUSB_DIRECTORY) -DCFG_TUSB_MCU=OPT_MCU_VALENTYUSB_EPTRI -Wno-char-subscripts -fno-strict-aliasing -fpack-struct

OBJECTS=main.o time.o hyperram.o hdmi_edid.o terminal.o i2c.o boson.o settings.o flirCRC.o Serializer_BuiltIn.o terminal_menu.o dma.o scaler.o ppu.o gui.o
OBJECTS+= usb.o usb_descriptors.o msc_disk.o bswapsi2.o


vpath % $(DIVA-FW_DIRECTORY) $(DIVA-FW_DIRECTORY)/boson
vpath % $(DIVA-FW_DIRECTORY) $(DIVA-FW_DIRECTORY)/usb

all: DiVA-fw.bin size

%.bin: %.elf
	$(OBJCOPY) -O binary $< $@
ifneq ($(OS),Windows_NT)
	chmod -x $@
endif
ifeq ($(CPUENDIANNESS),little)
	$(PYTHON) -m litex.soc.software.mkmscimg $@ --little
else
	$(PYTHON) -m litex.soc.software.mkmscimg $@
endif

DiVA-fw.elf: $(DIVA-FW_DIRECTORY)/linker.ld $(OBJECTS)

%.elf: 
	$(LD) $(LDFLAGS) -L$(BUILDINC_DIRECTORY)/generated -T $(DIVA-FW_DIRECTORY)/linker.ld -N -o $@ \
		../libbase/crt0.o \
		$(OBJECTS) \
		-gc-sections \
		-L../libbase \
		-L../libcompiler_rt \
		-L../tinyusb \
		-lbase-nofloat -lcompiler_rt -ltinyusb
ifneq ($(OS),Windows_NT)
	chmod -x $@
endif

# pull in dependency info for *existing* .o files
-include $(OBJECTS:.o=.d)

%.o: %.c
	$(compile)

%.o: %.S
	$(assemble)

clean:
	$(RM) $(OBJECTS) DiVA-fw.elf DiVA-fw.bin .*~ *~

size:
	$(TARGET_PREFIX)size DiVA-fw.elf
	riscv64-unknown-elf-objdump -DS DiVA-fw.elf > DiVA-fw.lst


.PHONY: all clean
