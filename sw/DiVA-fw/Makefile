include ../include/generated/variables.mak
include $(SOC_DIRECTORY)/software/common.mak

# Permit TFTP_SERVER_PORT override from shell environment / command line
ifdef TFTP_SERVER_PORT
CFLAGS += -DTFTP_SERVER_PORT=$(TFTP_SERVER_PORT)
endif

CFLAGS += -fpack-struct -O3

OBJECTS=isr.o main.o

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
		../libbase/crt0-$(CPU)-ctr.o \
		$(OBJECTS) \
		-L../libbase \
		-L../libcompiler_rt \
		-lbase-nofloat -lcompiler_rt
ifneq ($(OS),Windows_NT)
	chmod -x $@
endif

# pull in dependency info for *existing* .o files
-include $(OBJECTS:.o=.d)

%.o: $(DIVA-FW_DIRECTORY)/%.c
	$(compile)

%.o: $(DIVA-FW_DIRECTORY)/%.S
	$(assemble)

clean:
	$(RM) $(OBJECTS) DiVA-fw.elf DiVA-fw.bin .*~ *~

size:
	$(TARGET_PREFIX)size DiVA-fw.elf


.PHONY: all clean
