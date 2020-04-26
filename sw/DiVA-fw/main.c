#include <stdlib.h>
#include <string.h>
#include <crc.h>
#include <stdint.h>
#include <stdbool.h>

#include <time.h>

#include <generated/csr.h>
#include <generated/mem.h>
#include <generated/git.h>


uint8_t x = 0;
uint8_t y = 0;


void terminal_write(char c){
	volatile uint32_t* vga = (volatile uint32_t*) (TERMINAL_BASE);
	if(c == '\r'){
		x = 0;
	}else if(c == '\n'){
		y += 1;
	}else{
		if(x >= 240){
			x = 0;
			y += 1;
		}

		vga[x*2 + y*240*2] = c; 
		vga[x*2 + y*240*2 + 1] = 14; 
		x += 1;
	}
}



uint8_t buffer[64];


int main(int i, char **c)
{	


	console_set_write_hook(terminal_write);

	rgb_div_m_write(60000*5);
    rgb_config_write(2);


	printf("\n\n");
	printf("  ______    ___   __   __   _______ \n");
	printf(" |      |  |___| |  | |  | |   _   |\n");
	printf(" |  _    |  ___  |  |_|  | |  |_|  |\n");
	printf(" | | |   | |   | |       | |       |\n");
	printf(" | |_|   | |   | |       | |       |\n");
	printf(" |       | |   |  |     |  |   _   |\n");
	printf(" |______|  |___|   |___|   |__| |__|\n");

	printf("- Digital Video Interface for Boson -\n");
	
	printf("\n (c) Copyright 2019-2020 GetLabs \n");
	printf(" fw built: "__DATE__ " " __TIME__ " \n\n");

	printf("   Firmware git sha1: "DIVA_GIT_SHA1"\n");
	printf("      Migen git sha1: "MIGEN_GIT_SHA1"\n");
	printf("      LiteX git sha1: "LITEX_GIT_SHA1"\n");
	printf("\n");
	

	printf("--=============== SoC ==================--\n");
	printf("CPU:        ");
#ifdef __vexriscv__
	printf("VexRiscv");
#else
	printf("Unknown");
#endif
	printf(" @ %dMHz\n", CONFIG_CLOCK_FREQUENCY/1000000);
	printf("ROM:        %dKB\n", ROM_SIZE/1024);
	printf("SRAM:       %dKB\n", SRAM_SIZE/1024);
#ifdef CONFIG_L2_SIZE
	printf("L2:        %dKB\n", CONFIG_L2_SIZE/1024);
#endif
#ifdef MAIN_RAM_SIZE
	printf("MAIN-RAM:   %dKB\n", MAIN_RAM_SIZE/1024);
#endif

#ifdef HYPERRAM_BASE
	printf("HYPERRAM:   %dKB\n", HYPERRAM_SIZE/1024);
#endif
//	printf("\e[1mHYPERRAM1\e[0m:  %dKB\n", HYPERRAM1_SIZE/1024);
	printf("\n");


    printf("--========== Initialization ============--\n");
#ifdef HYPERRAM_BASE
	hyperram_init();
#endif

	memtest((unsigned int*)HYPERRAM_BASE);
	printf("\n");

    printf("--============= \e[1mConsole\e[0m ================--\n");
    while(1) {
		putsnonl("\e[92;1mFireCam\e[0m> ");
		readstr(buffer, 64);
		do_command(buffer);
	}
	return 0;
}
