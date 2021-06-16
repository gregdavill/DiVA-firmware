INCLUDE output_format.ld
ENTRY(_start)

__DYNAMIC = 0;

MEMORY {
	sram : ORIGIN = 0x10000000, LENGTH = 0x00004000
	spiflash : ORIGIN = 0x300D0000, LENGTH = 0x01000000
	usb : ORIGIN = 0x90000000, LENGTH = 0x00001000
	csr : ORIGIN = 0xf0000000, LENGTH = 0x00010000
}

SECTIONS
{
	.text :
	{
		_ftext = .;
		*(.text.start)
		*(.text .stub .text.* .gnu.linkonce.t.*)
		_etext = .;
	} > spiflash

	.rodata :
	{
		. = ALIGN(4);
		_frodata = .;
		*(.rodata .rodata.* .gnu.linkonce.r.*)
		*(.rodata1)
		*(.srodata)
		*(.srodata.*)
		_erodata = .;
	} > spiflash

	.data : AT (ADDR(.rodata) + SIZEOF (.rodata))
	{
		. = ALIGN(4);
		_fdata = .;
		*(.data .data.* .gnu.linkonce.d.*)
		*(.data1)
		_gp = ALIGN(16);
		*(.sdata .sdata.* .gnu.linkonce.s.* .sdata2 .sdata2.*)
		_edata = ALIGN(16); /* Make sure _edata is >= _gp. */
	} > sram

	.bss :
	{
		. = ALIGN(4);
		_fbss = .;
		*(.dynsbss)
		*(.sbss .sbss.* .gnu.linkonce.sb.*)
		*(.scommon)
		*(.dynbss)
		*(.bss .bss.* .gnu.linkonce.b.*)
		*(COMMON)
		. = ALIGN(4);
		_ebss = .;
		_end = .;
	} > sram
}

PROVIDE(_fstack = ORIGIN(sram) + LENGTH(sram) - 4);

PROVIDE(_fdata_rom = LOADADDR(.data));
PROVIDE(_edata_rom = LOADADDR(.data) + SIZEOF(.data));