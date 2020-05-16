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



uint8_t buffer[64];




void set_io_delay(int cnt){
	hyperram_io_loadn_write(0);
	hyperram_io_loadn_write(1);
	hyperram_io_direction_write(0);

	/* 25ps of delay per tap.
	   Each rising edge adds to the io delay */
	for(int i = 0; i < cnt; i++){ 
		hyperram_io_move_write(1);
		hyperram_io_move_write(0);
	}
}

void set_clk_delay(int cnt){
	hyperram_clk_loadn_write(0);
	hyperram_clk_loadn_write(1);
	hyperram_clk_direction_write(0);

	/* 25ps of delay per tap.
	   Each rising edge adds to the io delay */
	for(int i = 0; i < cnt; i++){ 
		hyperram_clk_move_write(1);
		hyperram_clk_move_write(0);
	}
}


void screen_blank(){
	hyperram_reader_reset_write(1);
	hyperram_reader_start_address_write(0);
	hyperram_reader_transfer_size_write(1080*1920);
	hyperram_reader_blank_write(1);

	hyperram_reader_enable_write(1);

	msleep(100);
	
	hyperram_reader_blank_write(0);
}



int main(int i, char **c)
{	


	console_set_write_hook(terminal_write);

	rgb_div_m_write(300000);
    rgb_config_write(2);

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


    printf("--========== HyperRAM Initialization ============--\n");
	set_io_delay(0);
	set_clk_delay(120);
	hyperram_init();

	screen_blank();

	hdmi_out0_i2c_init();
	hdmi_out0_print_edid();

    printf("--============= Stats: ================--\n");

	uint32_t line = 0;

	hyperram_writer_pix_start_address_write(0);
	hyperram_writer_pix_transfer_size_write(640*720);
	hyperram_writer_pix_burst_size_write(256);
	hyperram_writer_pix_enable_write(1);

	hyperram_reader_boson_start_address_write(0);
	hyperram_reader_boson_transfer_size_write(640*512-64);
	hyperram_reader_boson_burst_size_write(256);
	hyperram_reader_boson_enable_write(1);
	
    while(1) {
		hyperram_hdmi_stats_reset_write(1);
		hyperram_boson_stats_reset_write(1);
		msleep(1000);		
		hyperram_hdmi_stats_latch_write(1);
		hyperram_boson_stats_latch_write(1);
		x = 0;
		y = 37;
		printf("HDMI: t:%u u:%u        \n", hyperram_hdmi_stats_tokens_read(), hyperram_hdmi_stats_underflows_read());
		x = 0;
		y = 38;
		printf("Boson: t:%u o:%u         ", hyperram_boson_stats_tokens_read(), hyperram_boson_stats_overflows_read());

		
		
	}
	return 0;
}
