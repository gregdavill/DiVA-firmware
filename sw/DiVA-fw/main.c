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
		vga[x*2 + y*240*2 + 1] = 0x02; 
		x += 1;
	}
}



int main(int i, char **c)
{	


	console_set_write_hook(terminal_write);

	rgb_div_m_write(60000*5);
    rgb_config_write(2);

	printf("\n\n");
	printf("\e[1m   _____         _____             ____ ___  ___  ___ \e[0m\n");
	printf("\e[1m  / __(_)______ / ___/__ ___ _    |_  // _ \\/ _ \\/ _ \\\e[0m\n");
	printf("\e[1m / _// / __/ -_) /__/ _ `/  ' \\  _/_ </ // / // / // /\e[0m\n");
	printf("\e[1m/_/ /_/_/  \\__/\\___/\\_,_/_/_/_/ /____/\\___/\\___/\\___/ \e[0m\n");
	printf("\e[96;1m    FireFlight Dual Sensor Thermal Imager! \e[0m\n");
	
	printf("\n (c) Copyright 2019-2020 FireFlight Technologies \n");
	printf(" BIOS built: "__DATE__ " " __TIME__ " \n");

	printf("\n");
	printf(" Migen git sha1: "MIGEN_GIT_SHA1"\n");
	printf(" LiteX git sha1: "LITEX_GIT_SHA1"\n");
	printf("\n");
	

	printf("--=============== \e[1mSoC\e[0m ==================--\n");
	printf("\e[1mCPU\e[0m:        ");
#ifdef __lm32__
	printf("LM32");
#elif __or1k__
	printf("MOR1KX");
#elif __picorv32__
	printf("PicoRV32");
#elif __vexriscv__
	printf("VexRiscv");
#elif __minerva__
	printf("Minerva");
#elif __rocket__
	printf("RocketRV64[imac]");
#elif __blackparrot__
		printf("BlackParrotRV64[ia]");
#else
	printf("Unknown");
#endif
	printf(" @ %dMHz\n", CONFIG_CLOCK_FREQUENCY/1000000);
	printf("\e[1mROM\e[0m:        %dKB\n", ROM_SIZE/1024);
	printf("\e[1mSRAM\e[0m:       %dKB\n", SRAM_SIZE/1024);
#ifdef CONFIG_L2_SIZE
	printf("\e[1mL2\e[0m:        %dKB\n", CONFIG_L2_SIZE/1024);
#endif
#ifdef MAIN_RAM_SIZE
	printf("\e[1mMAIN-RAM\e[0m:   %dKB\n", MAIN_RAM_SIZE/1024);
#endif

//	printf("\e[1mHYPERRAM0\e[0m:  %dKB\n", HYPERRAM0_SIZE/1024);
//	printf("\e[1mHYPERRAM1\e[0m:  %dKB\n", HYPERRAM1_SIZE/1024);
	printf("\n");


    printf("--========== \e[1mInitialization\e[0m ============--\n");
//	hyperram_init();

//	memtest((unsigned int*)HYPERRAM0_BASE);
//	memtest((unsigned int*)HYPERRAM1_BASE);
	printf("\n");



	printf("> ");
	msleep(10);

    while (1) {

    }
	return 0;
}
