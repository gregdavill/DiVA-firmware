include ../include/generated/variables.mak
include $(SOC_DIRECTORY)/software/common.mak

VPATH=$(TINYUSB_DIRECTORY)

include $(TINYUSB_DIRECTORY)/Makefile.mk

#See here for-fno-strict-aliasing -fpack-struct:
#http://sourceforge.net/p/contiki/mailman/message/28002063/

CCDEP=$(CC)


# TinyUSB Stack source
SRC_C += \
	src/tusb.c \
	src/common/tusb_fifo.c \
	src/device/usbd.c \
	src/device/usbd_control.c \
	src/class/audio/audio_device.c \
	src/class/cdc/cdc_device.c \
	src/class/dfu/dfu_device.c \
	src/class/dfu/dfu_rt_device.c \
	src/class/hid/hid_device.c \
	src/class/midi/midi_device.c \
	src/class/msc/msc_device.c \
	src/class/net/net_device.c \
	src/class/usbtmc/usbtmc_device.c \
	src/class/vendor/vendor_device.c

TINYUSBCOREOBJS=$(addprefix $(LIBTINYUSBDIR)/,$(SRC_C:.c=.o))

TINYUSBARCHOBJS=\
	$(LIBTINYUSBDIR)/src/portable/valentyusb/eptri/dcd_eptri.o \

TINYUSBOBJS=$(TINYUSBCOREOBJS) $(TINYUSBARCHOBJS)
OBJS_LIB+=$(TINYUSBOBJS)

TINYUSBLIB=libtinyusb.a

all: $(TINYUSBLIB)

.PHONY: all compile clean

# pull in dependency info for *existing* .o files
-include $(TINYUSBOBJS:.o=.d)

%.o: %.c
	@mkdir -p $(@D)
	$(compile)

%.o: %.S
	@mkdir -p $(@D)
	$(assemble)

clean:
	rm -f $(TINYUSBOBJS) $(TINYUSBOBJS:.o=.d) libtinyusb.a

libtinyusb.a: $(TINYUSBOBJS)
	$(AR) clr libtinyusb.a $(TINYUSBOBJS)
