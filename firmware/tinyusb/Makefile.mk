LIBTINYUSBDIR=../deps/tinyusb

CFLAGS += \
  -ggdb \
  -fdata-sections \
  -ffunction-sections \
  -fsingle-precision-constant \
  -fno-strict-aliasing \
  -Wdouble-promotion \
  -Wstrict-prototypes \
  -Wstrict-overflow \
  -Wall \
  -Wextra \
  -Werror \
  -Wfatal-errors \
  -Werror-implicit-function-declaration \
  -Wfloat-equal \
  -Wundef \
  -Wshadow \
  -Wwrite-strings \
  -Wsign-compare \
  -Wmissing-format-attribute \
  -Wunreachable-code \
  -Wcast-align \
  -Wcast-function-type

CFLAGS += \
	-I$(TINYUSB_DIRECTORY)/$(LIBTINYUSBDIR)/src \
	-I$(TINYUSB_DIRECTORY) \
	-I$(BUILDINC_DIRECTORY)/generated \
	-Wno-char-subscripts \
	-fno-strict-aliasing -fpack-struct \
	-DCFG_TUSB_MCU=OPT_MCU_VALENTYUSB_EPTRI  \
  -nostdlib
