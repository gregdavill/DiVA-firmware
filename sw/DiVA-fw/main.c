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
