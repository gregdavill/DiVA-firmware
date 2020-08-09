#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <crc.h>
#include <stdint.h>
#include <stdbool.h>

#include <time.h>

#include <generated/csr.h>
#include <generated/mem.h>
#include <generated/git.h>

void isr(void){

}

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







int main(int i, char **c)
{	


	console_set_write_hook(terminal_write);
	
	terminal_enable_write(1);

	//rgb_div_m_write(400000);
    //rgb_config_write(2);
/*
	printf("     ______    ___   __   __   _______ \n");
	printf("    |      |  |___| |  | |  | |   _   |\n");
	printf("    |  _    |  ___  |  |_|  | |  |_|  |\n");
	printf("    | | |   | |   | |       | |       |\n");
	printf("    | |_|   | |   | |       | |       |\n");
	printf("    |       | |   |  |     |  |   _   |\n");
	printf("    |______|  |___|   |___|   |__| |__|\n");

	printf("   - Digital Video Interface for Boson -\n");
	
 	printf("\n (c) Copyright 2019-2020 GetLabs \n");
 	printf(" fw built: "__DATE__ " " __TIME__ " \n\n");

 	printf("   Firmware git sha1: "DIVA_GIT_SHA1"\n");
 	printf("      Migen git sha1: "MIGEN_GIT_SHA1"\n");
 	printf("      LiteX git sha1: "LITEX_GIT_SHA1"\n");
*/


printf("\n");
	printf("\e[1m        __   _ __      _  __\e[0m\n");
	printf("\e[1m       / /  (_) /____ | |/_/\e[0m\n");
	printf("\e[1m      / /__/ / __/ -_)>  <\e[0m\n");
	printf("\e[1m     /____/_/\\__/\\__/_/|_|\e[0m\n");
	printf("\e[1m   Build your hardware, easily!\e[0m\n");
	printf("\n");
	printf(" (c) Copyright 2012-2020 Enjoy-Digital\n");
	printf(" (c) Copyright 2007-2015 M-Labs\n");
	printf("\n");
	printf(" BIOS built on "__DATE__" "__TIME__"\n");
	printf("\n");
	printf(" Migen git sha1: "MIGEN_GIT_SHA1"\n");
	printf(" LiteX git sha1: "LITEX_GIT_SHA1"\n");
	printf("\n");
	printf("--=============== \e[1mSoC\e[0m ==================--\n");
	printf("\e[1mCPU\e[0m:       %s @ %dMHz\n",
		CONFIG_CPU_HUMAN_NAME,
		CONFIG_CLOCK_FREQUENCY/1000000);
	printf("\e[1mBUS\e[0m:       %s %d-bit @ %dGiB\n",
		CONFIG_BUS_STANDARD,
		CONFIG_BUS_DATA_WIDTH,
		(1 << (CONFIG_BUS_ADDRESS_WIDTH - 30)));
	printf("\e[1mCSR\e[0m:       %d-bit data\n",
		CONFIG_CSR_DATA_WIDTH);
	printf("\e[1mROM\e[0m:       %dKiB\n", ROM_SIZE/1024);
	printf("\e[1mSRAM\e[0m:      %dKiB\n", SRAM_SIZE/1024);
#ifdef CONFIG_L2_SIZE
	printf("\e[1mL2\e[0m:        %dKiB\n", CONFIG_L2_SIZE/1024);
#endif
#ifdef MAIN_RAM_SIZE
	printf("\e[1mMAIN-RAM\e[0m:  %dKiB\n", MAIN_RAM_SIZE/1024);
#endif
	printf("\n");


    printf("--========== \e[1mInitialization\e[0m ============--\n");


//    printf(" HyperRAM Init..");

	hyperram_init();
//	printf(" DONE \n");





	uint32_t line = 0;
	uint8_t _y = y;


	reader_reset_write(1);
	reader_start_address_write(0);
	reader_transfer_size_write(800*600);
	reader_burst_size_write(128);
	reader_enable_write(1);

	writer_reset_write(1);
	writer_start_address_write(0);
	writer_transfer_size_write(800*600);
	writer_burst_size_write(128);
	writer_enable_write(1);

	
    while(1) {
		y = _y;
		printf("Counter %u \n", line++);
		/*
		printf("Button_A %u \n", btn_in_read() & 0x1);
		printf("Button_B %u \n", btn_in_read() & 0x2);

		if(btn_in_read() & 0x2)
			reader_enable_write(1);
			*/
	}
	
	return 0;
}
