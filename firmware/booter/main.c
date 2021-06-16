#include <stdlib.h>
#include <stdint.h>

#include "spi.h"
#include <generated/mem.h>
#include <generated/csr.h>

#define FLASH_OFFSET 0x000D0000

__attribute__((naked)) int main(int i, char **c)
{	
	leds_out_write(3);

  spiInit();
  spiSetQE();
  spiFree();
  
	leds_out_write(1);
  
  asm volatile(
    "jr %0;" 
    :: "r"(SPIFLASH_BASE + FLASH_OFFSET) : );

  __builtin_unreachable();

	return 0;
}
