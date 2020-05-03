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
		if(x >= 80){
			x = 0;
			y += 1;
		}

		vga[x + y*80] = c; 
		//vga[x*2 + y*80*2 + 1] = 14; 
		x += 1;
	}
}



uint8_t buffer[64];




void set_io_delay(int cnt){
	test_loadn_write(1);
	test_loadn_write(0);
	test_loadn_write(1);
	test_direction_write(1);

	/* 25ps of delay per tap.
	   Each rising edge adds to the io delay */
	for(int i = 0; i < cnt; i++){ 
		test_move_write(1);
		test_move_write(0);
	}
}


int main(int i, char **c)
{	


	console_set_write_hook(terminal_write);

	rgb_div_m_write(60000*5);
    rgb_config_write(2);

	printf("     ______    ___   __   __   _______ \n");
	printf("    |      |  |___| |  | |  | |   _   |\n");
	printf("    |  _    |  ___  |  |_|  | |  |_|  |\n");
	printf("    | | |   | |   | |       | |       |\n");
	printf("    | |_|   | |   | |       | |       |\n");
	printf("    |       | |   |  |     |  |   _   |\n");
	printf("    |______|  |___|   |___|   |__| |__|\n");

	printf("   - Digital Video Interface for Boson -\n");
	
// 	printf("\n (c) Copyright 2019-2020 GetLabs \n");
// 	printf(" fw built: "__DATE__ " " __TIME__ " \n\n");

// 	printf("   Firmware git sha1: "DIVA_GIT_SHA1"\n");
// 	printf("      Migen git sha1: "MIGEN_GIT_SHA1"\n");
// 	printf("      LiteX git sha1: "LITEX_GIT_SHA1"\n");
// 	printf("\n");
	

// 	printf("--=============== SoC ==================--\n");
// 	printf("CPU:        ");
// #ifdef __vexriscv__
// 	printf("SERV");
// #else
// 	printf("Unknown");
// #endif
// 	printf(" @ %dMHz\n", CONFIG_CLOCK_FREQUENCY/1000000);
// 	printf("ROM:        %dKB\n", ROM_SIZE/1024);
// 	printf("SRAM:       %dKB\n", SRAM_SIZE/1024);
// #ifdef CONFIG_L2_SIZE
// 	printf("L2:        %dKB\n", CONFIG_L2_SIZE/1024);
// #endif
// #ifdef MAIN_RAM_SIZE
// 	printf("MAIN-RAM:   %dKB\n", MAIN_RAM_SIZE/1024);
// #endif

// 	printf("HYPERRAM:   %dKB\n", (0x800000)/1024);
// 	printf("\n");


    printf("--========== HyperRAM Initialization ============--\n  ");
	set_io_delay(127);
	for(int i = 0; i < 1; i++){
		hyperram_init();
	}


	
	memtest((unsigned int*)HYPERRAM_BASE);
	printf("\n");

    printf("--============= Stats: ================--\n");

	uint32_t line = 0;

	volatile uint32_t* ptr = HYPERRAM_BASE;
	*ptr = 0xAA55AA55;

	printf("Test read: %08x %08x %08x", *ptr++,*ptr++,*ptr++);
	

	uint32_t colour = 0xFF22410;
    while(1) {
		

		
		putsnonl("DiVA> ");
		readstr(buffer, 64);
		do_command(buffer);
	}
	return 0;
}
