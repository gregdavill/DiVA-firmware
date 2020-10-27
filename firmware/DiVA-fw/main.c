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


const char* palette[] = {
			"White Hot", "Block Hot",
			"Rainbow", "Rainbow High Contrast",
			"Ironbow", "Lava",
			"Arctic", "Glowbow",
			"Graded Fire", "Hottest"};
const char* padding = "                                                                   ";


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
	terminal_set_fg(TERMINAL_CYAN);

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
	
	//init_settings();

	terminal_clear();
	terminal_set_bg(TERMINAL_BLACK);
	

	/* Boson Init */
	boson_init();


	/* Run through some checks if a Boson is attached? */
	uint32_t boson_freq = video_debug_freq_value_read();

	if(boson_freq == 0){
		//printf("Waiting for Clock from Boson\n");

		while(1){
		//	printf("Detected Frequency: %u Hz           \r", video_debug_freq_value_read());

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


	draw_settings_window();

	uint8_t option = 0;

	uint8_t x = 10;
    while(1) {
		
		//terminal_set_cursor(0,20);

		//printf("Counter %u \n", line++);
		//printf("freq %u \n", video_debug_freq_value_read());
		//
		//video_debug_latch_write(1);
		//printf("vsync LOW %u  HIGH %u   \n", video_debug_vsync_low_read(), video_debug_vsync_high_read());
		//printf("hsync LOW %u  HIGH %u   \n", video_debug_hsync_low_read(), video_debug_hsync_high_read());
		//printf("lines %u   \n", video_debug_lines_read());


		msleep(1);

		
		
		if((btn_in_read() & 2) == 0){
			btn_2_cnt++;
		}else{
			if(btn_2_cnt > 0){
				
				const uint32_t width = 70;
				const uint32_t height = 10;
				const uint32_t window_x = (100 - width) / 2;
				const uint32_t window_y = 20;

				terminal_set_cursor(window_x + 2, window_y+1);
				terminal_set_fg(TERMINAL_BLUE);
				terminal_set_bg(TERMINAL_WHITE);
				printf("LUT [%s]%.*s", palette[option], width - 10 - strlen(palette[option]), padding);
				//terminal_fill_line(width);

				boson_set_lut(option);


				option++;
				if(option >= 10)
					option = 0;
				
				

			}
			btn_2_cnt = 0;
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

void draw_settings_window(){

	const uint32_t width = 70;
	const uint32_t height = 10;
	const uint32_t window_x = (100 - width) / 2;
	const uint32_t window_y = 20;
	
				
	terminal_set_bg(TERMINAL_BLUE);
	terminal_set_fg(TERMINAL_WHITE);

	treminal_draw_box(window_x, window_y, width, height);
	terminal_set_cursor(window_x + 1, window_y);
	printf("Settings");
	
	
	terminal_set_cursor(window_x + 2, window_y+1);
	terminal_set_fg(TERMINAL_BLUE);
	terminal_set_bg(TERMINAL_WHITE);
	printf("LUT [%s]%.*s", palette[0], width - 10 - strlen(palette[0]), padding);
}
