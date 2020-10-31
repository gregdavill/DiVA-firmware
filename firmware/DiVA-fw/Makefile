include ../include/generated/variables.mak
include $(SOC_DIRECTORY)/software/common.mak

CFLAGS += -fpack-struct -O3 -I$(DIVA-FW_DIRECTORY)/include -fdata-sections -ffunction-sections

OBJECTS=main.o time.o hyperram.o hdmi_edid.o terminal.o i2c.o boson.o settings.o flirCRC.o Serializer_BuiltIn.o terminal_menu.o

vpath % $(DIVA-FW_DIRECTORY) $(DIVA-FW_DIRECTORY)/boson

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
		-lbase-nofloat -lcompiler_rt
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


.PHONY: all clean
