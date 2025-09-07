include ../include/generated/variables.mak
include $(SOC_DIRECTORY)/software/common.mak

CFLAGS += -fpack-struct -O3 -I$(DIVA_FW_DIRECTORY)/include -fdata-sections -ffunction-sections

OBJECTS=crt0.o main.o time.o hyperram_ctrl.o hdmi_edid.o terminal.o boson.o settings.o flirCRC.o Serializer_BuiltIn.o terminal_menu.o dma.o scaler.o

vpath % $(DIVA_FW_DIRECTORY) $(DIVA_FW_DIRECTORY)/boson

all: DiVA-fw.bin size

%.bin: %.elf
	$(OBJCOPY) -O binary $< $@
ifneq ($(OS),Windows_NT)
	chmod -x $@
endif


DiVA-fw.elf: $(DIVA_FW_DIRECTORY)/linker.ld $(OBJECTS)

vpath %.a $(PACKAGES:%=../%)

%.elf: crt0.o 
	$(CC) $(LDFLAGS) \
		-L$(BUILDINC_DIRECTORY)/generated -T $(DIVA_FW_DIRECTORY)/linker.ld -N -o $@ \
		$(OBJECTS) \
		$(PACKAGES:%=-L../%) \
		-Wl,-gc-sections \
		-Wl,--wrap=uart_write \
		-Wl,-Map,$@.map \
		$(LIBS:lib%=-l%)

ifneq ($(OS),Windows_NT)
	chmod -x $@
endif

# pull in dependency info for *existing* .o files
-include $(OBJECTS:.o=.d)

VPATH = $(DIVA_FW_DIRECTORY):$(CPU_DIRECTORY)

%.o: %.c
	$(compile)

%.o: %.S
	$(assemble)

clean:
	$(RM) $(OBJECTS) DiVA-fw.elf DiVA-fw.bin .*~ *~

size: DiVA-fw.elf
	$(TARGET_PREFIX)size DiVA-fw.elf


.PHONY: all clean
