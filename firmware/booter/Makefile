include ../include/generated/variables.mak
include $(SOC_DIRECTORY)/software/common.mak

CFLAGS += -Os \
  -I.

OBJECTS=crt0.o main.o spi.o

vpath % $(BOOTER_DIRECTORY)

all: booter.bin lst

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

booter.elf: $(BOOTER_DIRECTORY)/linker.ld $(OBJECTS)

%.elf: 
	$(LD) $(LDFLAGS) -L$(BUILDINC_DIRECTORY)/generated -T $(BOOTER_DIRECTORY)/linker.ld -N -o $@ \
		$(OBJECTS) \
		-Map=output.map
		
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
	$(RM) $(OBJECTS) booter.elf booter.bin .*~ *~

lst:
	riscv64-unknown-elf-objdump -DS booter.elf > booter.lst


.PHONY: all clean
