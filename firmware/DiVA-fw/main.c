#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <crc.h>
#include <stdint.h>
#include <stdbool.h>

#include <time.h>
#include "include/terminal.h"

#include <generated/csr.h>
#include <generated/mem.h>
#include <generated/git.h>

void isr(void){

}



void switch_mode(int mode){
	if(mode == 0){
		framer_x_start_write(213);
		framer_y_start_write(27);

		framer_width_write(800);
		framer_height_write(600);



		scaler_enable_write(1);
	}else{
		framer_width_write(640);
		framer_height_write(512);

		framer_x_start_write(213 + (800-640)/2);
		framer_y_start_write(27 +  (600-512)/2);

		scaler_enable_write(0);
	}
}


int main(int i, char **c)
{	


	console_set_write_hook(terminal_write);
	
	terminal_enable_write(1);

	//rgb_div_m_write(400000);
    //rgb_config_write(2);


	terminal_set_bg(TERMINAL_TRANSPARENT);
	terminal_set_fg(TERMINAL_TRANSPARENT);
	terminal_clear();


	terminal_set_fg(TERMINAL_CYAN);
	printf("     ______    ___   __   __   _______ \n");
	printf("    |      |  |___| |  | |  | |   _   |\n");
	printf("    |  _    |  ___  |  |_|  | |  |_|  |\n");
	printf("    | | |   | |   | |       | |       |\n");
	printf("    | |_|   | |   | |       | |       |\n");
	printf("    |       | |   |  |     |  |   _   |\n");
	printf("    |______|  |___|   |___|   |__| |__|\n");


	terminal_set_fg(TERMINAL_YELLOW);
	printf("   - Digital Video Interface for Boson -\n");
	terminal_set_fg(TERMINAL_BLUE);

 	printf("\n (c) Copyright 2019-2020 GetLabs \n");
 	printf(" fw built: "__DATE__ " " __TIME__ " \n\n");

 	printf("   Firmware git sha1: "DIVA_GIT_SHA1"\n");
 	printf("      Migen git sha1: "MIGEN_GIT_SHA1"\n");
 	printf("      LiteX git sha1: "LITEX_GIT_SHA1"\n");

	printf("--==========-- \e[1mHyperRAM Init\e[0m ===========--\n");
	hyperram_init();
	printf("\n");	
	prbs_memtest(HYPERRAM_BASE, HYPERRAM_SIZE);


	terminal_set_bg(TERMINAL_TRANSPARENT);

	/* Run through some checks if a Boson is attached? */
	uint32_t boson_freq = video_debug_freq_value_read();

	if(boson_freq == 0){
		printf("Waiting for Clock from Boson\n");

		while(1){
			printf("Detected Frequency: %u Hz           \r", video_debug_freq_value_read());

			if(video_debug_freq_value_read() > 26.5e6){
				break;
			}
		}
	}



	uint32_t line = 0;
	terminal_set_cursor(0,20);


	reader_reset_write(1);
	reader_start_address_write(0);
	reader_transfer_size_write(640*512);
	reader_burst_size_write(512);
	reader_enable_write(1);


	writer_reset_write(1);
	writer_start_address_write(0);
	writer_transfer_size_write(640*512);
	writer_burst_size_write(512);
	writer_enable_write(1);
	

	framer_width_write(800);
	framer_height_write(600);

	//framer_x_start_write(213);
	//framer_y_start_write(27);
	framer_x_start_write(213 + (800-640)/2);
	framer_y_start_write(27 +  (600-512)/2);

	switch_mode(1);

	//msleep(100);
	//switch_mode(1);
	
	
	// place preview in bottom right corner


	
	uint8_t scale_mode = 1;
	uint16_t btn_2_cnt = 0;

    while(1) {
		
		terminal_set_cursor(0,20);

		printf("Counter %u \n", line++);
		printf("freq %u \n", video_debug_freq_value_read());
		
		video_debug_latch_write(1);
		printf("vsync LOW %u  HIGH %u   \n", video_debug_vsync_low_read(), video_debug_vsync_high_read());
		printf("hsync LOW %u  HIGH %u   \n", video_debug_hsync_low_read(), video_debug_hsync_high_read());
		printf("lines %u   \n", video_debug_lines_read());



		if((btn_in_read() & 2) == 0){
			btn_2_cnt++;
		}else{
			if((btn_2_cnt > 5) && (btn_2_cnt < 100)){
				boson_mode_write(1);
			}
			btn_2_cnt = 0;
		}


		if((btn_2_cnt > 100) && (btn_2_cnt < 150) ){
			scale_mode ^= 1;
			btn_2_cnt = 999;

			switch_mode(scale_mode);
		}



		/*
		printf("Button_A %u \n", btn_in_read() & 0x1);
		printf("Button_B %u \n", btn_in_read() & 0x2);

		if(btn_in_read() & 0x2)
			reader_enable_write(1);
			*/
		
		
	}
	
	return 0;
}

