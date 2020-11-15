#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <crc.h>
#include <stdint.h>
#include <stdbool.h>

#include <console.h>
#include "include/hyperram.h"
#include "include/settings.h"
#include "include/time.h"
#include "include/terminal.h"
#include "include/boson.h"

#include <generated/csr.h>
#include <generated/mem.h>
#include <generated/git.h>

#include "include/terminal_menu.h"

/* prototypes */
void isr(void);
void switch_mode(int);


void isr(void){

}



void width_coeff_write(int t, int p, int v, int skip){
	scaler_width_coeff_tap_write(t);
	scaler_width_coeff_phase_write(p);
	scaler_width_coeff_data_write(v);
	scaler_width_coeff_stall_write(skip);
	scaler_width_coeff_en_write(1);
	scaler_width_coeff_en_write(0);
	
	
}

void height_coeff_write(int t, int p, int v, int skip){
	scaler_height_coeff_tap_write(t);
	scaler_height_coeff_phase_write(p);
	scaler_height_coeff_data_write(v);
	scaler_height_coeff_stall_write(skip);
	scaler_height_coeff_en_write(1);
	scaler_height_coeff_en_write(0);
}

void switch_mode(int mode){
	if(mode == 0){
		framer_width_write(640);
		framer_height_write(512);

		framer_x_start_write(213 + (800-640)/2);
		framer_y_start_write(27 +  (600-512)/2);

		scaler_enable_write(0);
	}else{
		framer_x_start_write(213);
		framer_y_start_write(27);

		framer_width_write(800);
		framer_height_write(600 - 2);

		width_coeff_write(0,0,0,0);
		width_coeff_write(0,1,-16,0);
		width_coeff_write(0,2,-18,0);
		width_coeff_write(0,3,-12,0);
		width_coeff_write(0,4,-4,0);
		width_coeff_write(1,0,256,0);
		width_coeff_write(1,1,233,0);
		width_coeff_write(1,2,178,0);
		width_coeff_write(1,3,108,0);
		width_coeff_write(1,4,43,0);
		width_coeff_write(2,0,0,0);
		width_coeff_write(2,1,43,0);
		width_coeff_write(2,2,108,0);
		width_coeff_write(2,3,178,0);
		width_coeff_write(2,4,233,0);
		width_coeff_write(3,0,0,0);
		width_coeff_write(3,1,-4,0);
		width_coeff_write(3,2,-12,0);
		width_coeff_write(3,3,-18,1);
		width_coeff_write(3,4,-16,0);

		scaler_width_phases_write(5);
		


		height_coeff_write(0,0,0,0);
height_coeff_write(1,0,256,0);
height_coeff_write(2,0,0,0);
height_coeff_write(3,0,0,0);
height_coeff_write(0,1,-13,0);
height_coeff_write(1,1,243,0);
height_coeff_write(2,1,28,0);
height_coeff_write(3,1,-2,0);
height_coeff_write(0,2,-18,0);
height_coeff_write(1,2,210,0);
height_coeff_write(2,2,71,0);
height_coeff_write(3,2,-7,0);
height_coeff_write(0,3,-17,0);
height_coeff_write(1,3,164,0);
height_coeff_write(2,3,122,0);
height_coeff_write(3,3,-13,0);
height_coeff_write(0,4,-12,0);
height_coeff_write(1,4,113,0);
height_coeff_write(2,4,173,0);
height_coeff_write(3,4,-18,0);
height_coeff_write(0,5,-6,1);
height_coeff_write(1,5,63,1);
height_coeff_write(2,5,217,1);
height_coeff_write(3,5,-18,1);
height_coeff_write(0,6,-1,0);
height_coeff_write(1,6,22,0);
height_coeff_write(2,6,247,0);
height_coeff_write(3,6,-11,0);
height_coeff_write(0,7,-3,0);
height_coeff_write(1,7,255,0);
height_coeff_write(2,7,3,0);
height_coeff_write(3,7,0,0);
height_coeff_write(0,8,-15,0);
height_coeff_write(1,8,238,0);
height_coeff_write(2,8,35,0);
height_coeff_write(3,8,-3,0);
height_coeff_write(0,9,-18,0);
height_coeff_write(1,9,203,0);
height_coeff_write(2,9,80,0);
height_coeff_write(3,9,-8,0);
height_coeff_write(0,10,-16,0);
height_coeff_write(1,10,155,0);
height_coeff_write(2,10,132,0);
height_coeff_write(3,10,-14,0);
height_coeff_write(0,11,-11,0);
height_coeff_write(1,11,103,0);
height_coeff_write(2,11,182,0);
height_coeff_write(3,11,-18,0);
height_coeff_write(0,12,-5,1);
height_coeff_write(1,12,54,1);
height_coeff_write(2,12,224,1);
height_coeff_write(3,12,-17,1);
height_coeff_write(0,13,-1,0);
height_coeff_write(1,13,16,0);
height_coeff_write(2,13,250,0);
height_coeff_write(3,13,-9,0);
height_coeff_write(0,14,-6,0);
height_coeff_write(1,14,254,0);
height_coeff_write(2,14,8,0);
height_coeff_write(3,14,0,0);
height_coeff_write(0,15,-16,0);
height_coeff_write(1,15,233,0);
height_coeff_write(2,15,43,0);
height_coeff_write(3,15,-4,0);
height_coeff_write(0,16,-18,0);
height_coeff_write(1,16,195,0);
height_coeff_write(2,16,89,0);
height_coeff_write(3,16,-10,0);
height_coeff_write(0,17,-16,0);
height_coeff_write(1,17,146,0);
height_coeff_write(2,17,141,0);
height_coeff_write(3,17,-15,0);
height_coeff_write(0,18,-10,0);
height_coeff_write(1,18,94,0);
height_coeff_write(2,18,190,0);
height_coeff_write(3,18,-18,0);
height_coeff_write(0,19,-4,1);
height_coeff_write(1,19,46,1);
height_coeff_write(2,19,230,1);
height_coeff_write(3,19,-16,1);
height_coeff_write(0,20,0,0);
height_coeff_write(1,20,10,0);
height_coeff_write(2,20,253,0);
height_coeff_write(3,20,-7,0);
height_coeff_write(0,21,-8,0);
height_coeff_write(1,21,252,0);
height_coeff_write(2,21,13,0);
height_coeff_write(3,21,0,0);
height_coeff_write(0,22,-17,0);
height_coeff_write(1,22,227,0);
height_coeff_write(2,22,50,0);
height_coeff_write(3,22,-5,0);
height_coeff_write(0,23,-18,0);
height_coeff_write(1,23,186,0);
height_coeff_write(2,23,99,0);
height_coeff_write(3,23,-11,0);
height_coeff_write(0,24,-15,0);
height_coeff_write(1,24,136,0);
height_coeff_write(2,24,151,0);
height_coeff_write(3,24,-16,0);
height_coeff_write(0,25,-9,0);
height_coeff_write(1,25,85,0);
height_coeff_write(2,25,199,0);
height_coeff_write(3,25,-18,0);
height_coeff_write(0,26,-3,1);
height_coeff_write(1,26,39,1);
height_coeff_write(2,26,236,1);
height_coeff_write(3,26,-15,1);
height_coeff_write(0,27,0,0);
height_coeff_write(1,27,5,0);
height_coeff_write(2,27,255,0);
height_coeff_write(3,27,-4,0);
height_coeff_write(0,28,-10,0);
height_coeff_write(1,28,249,0);
height_coeff_write(2,28,19,0);
height_coeff_write(3,28,-1,0);
height_coeff_write(0,29,-18,0);
height_coeff_write(1,29,221,0);
height_coeff_write(2,29,59,0);
height_coeff_write(3,29,-6,0);
height_coeff_write(0,30,-18,0);
height_coeff_write(1,30,178,0);
height_coeff_write(2,30,108,0);
height_coeff_write(3,30,-12,0);
height_coeff_write(0,31,-14,0);
height_coeff_write(1,31,127,0);
height_coeff_write(2,31,160,0);
height_coeff_write(3,31,-17,0);
height_coeff_write(0,32,-8,0);
height_coeff_write(1,32,76,0);
height_coeff_write(2,32,206,0);
height_coeff_write(3,32,-18,0);
height_coeff_write(0,33,-2,1);
height_coeff_write(1,33,32,1);
height_coeff_write(2,33,241,1);
height_coeff_write(3,33,-14,1);
height_coeff_write(0,34,0,0);
height_coeff_write(1,34,1,0);
height_coeff_write(2,34,255,0);
height_coeff_write(3,34,-1,0);
height_coeff_write(0,35,-12,0);
height_coeff_write(1,35,245,0);
height_coeff_write(2,35,25,0);
height_coeff_write(3,35,-1,0);
height_coeff_write(0,36,-18,0);
height_coeff_write(1,36,214,0);
height_coeff_write(2,36,67,0);
height_coeff_write(3,36,-7,0);
height_coeff_write(0,37,-17,0);
height_coeff_write(1,37,169,0);
height_coeff_write(2,37,117,0);
height_coeff_write(3,37,-13,0);
height_coeff_write(0,38,-13,0);
height_coeff_write(1,38,117,0);
height_coeff_write(2,38,169,0);
height_coeff_write(3,38,-17,0);
height_coeff_write(0,39,-7,1);
height_coeff_write(1,39,67,1);
height_coeff_write(2,39,214,1);
height_coeff_write(3,39,-18,1);
height_coeff_write(0,40,-1,0);
height_coeff_write(1,40,25,0);
height_coeff_write(2,40,245,0);
height_coeff_write(3,40,-12,0);
height_coeff_write(0,41,-1,0);
height_coeff_write(1,41,255,0);
height_coeff_write(2,41,1,0);
height_coeff_write(3,41,0,0);
height_coeff_write(0,42,-14,0);
height_coeff_write(1,42,241,0);
height_coeff_write(2,42,32,0);
height_coeff_write(3,42,-2,0);
height_coeff_write(0,43,-18,0);
height_coeff_write(1,43,206,0);
height_coeff_write(2,43,76,0);
height_coeff_write(3,43,-8,0);
height_coeff_write(0,44,-17,0);
height_coeff_write(1,44,160,0);
height_coeff_write(2,44,127,0);
height_coeff_write(3,44,-14,0);
height_coeff_write(0,45,-12,0);
height_coeff_write(1,45,108,0);
height_coeff_write(2,45,178,0);
height_coeff_write(3,45,-18,0);
height_coeff_write(0,46,-6,1);
height_coeff_write(1,46,59,1);
height_coeff_write(2,46,221,1);
height_coeff_write(3,46,-18,1);
height_coeff_write(0,47,-1,0);
height_coeff_write(1,47,19,0);
height_coeff_write(2,47,249,0);
height_coeff_write(3,47,-10,0);
height_coeff_write(0,48,-4,0);
height_coeff_write(1,48,255,0);
height_coeff_write(2,48,5,0);
height_coeff_write(3,48,0,0);
height_coeff_write(0,49,-15,0);
height_coeff_write(1,49,236,0);
height_coeff_write(2,49,39,0);
height_coeff_write(3,49,-3,0);
height_coeff_write(0,50,-18,0);
height_coeff_write(1,50,199,0);
height_coeff_write(2,50,85,0);
height_coeff_write(3,50,-9,0);
height_coeff_write(0,51,-16,0);
height_coeff_write(1,51,151,0);
height_coeff_write(2,51,136,0);
height_coeff_write(3,51,-15,0);
height_coeff_write(0,52,-11,0);
height_coeff_write(1,52,99,0);
height_coeff_write(2,52,186,0);
height_coeff_write(3,52,-18,0);
height_coeff_write(0,53,-5,1);
height_coeff_write(1,53,50,1);
height_coeff_write(2,53,227,1);
height_coeff_write(3,53,-17,1);
height_coeff_write(0,54,0,0);
height_coeff_write(1,54,13,0);
height_coeff_write(2,54,252,0);
height_coeff_write(3,54,-8,0);
height_coeff_write(0,55,-7,0);
height_coeff_write(1,55,253,0);
height_coeff_write(2,55,10,0);
height_coeff_write(3,55,0,0);
height_coeff_write(0,56,-16,0);
height_coeff_write(1,56,230,0);
height_coeff_write(2,56,46,0);
height_coeff_write(3,56,-4,0);
height_coeff_write(0,57,-18,0);
height_coeff_write(1,57,190,0);
height_coeff_write(2,57,94,0);
height_coeff_write(3,57,-10,0);
height_coeff_write(0,58,-15,0);
height_coeff_write(1,58,141,0);
height_coeff_write(2,58,146,0);
height_coeff_write(3,58,-16,0);
height_coeff_write(0,59,-10,0);
height_coeff_write(1,59,89,0);
height_coeff_write(2,59,195,0);
height_coeff_write(3,59,-18,0);
height_coeff_write(0,60,-4,1);
height_coeff_write(1,60,43,1);
height_coeff_write(2,60,233,1);
height_coeff_write(3,60,-16,1);
height_coeff_write(0,61,0,0);
height_coeff_write(1,61,8,0);
height_coeff_write(2,61,254,0);
height_coeff_write(3,61,-6,0);
height_coeff_write(0,62,-9,0);
height_coeff_write(1,62,250,0);
height_coeff_write(2,62,16,0);
height_coeff_write(3,62,-1,0);
height_coeff_write(0,63,-17,0);
height_coeff_write(1,63,224,0);
height_coeff_write(2,63,54,0);
height_coeff_write(3,63,-5,0);
height_coeff_write(0,64,-18,0);
height_coeff_write(1,64,182,0);
height_coeff_write(2,64,103,0);
height_coeff_write(3,64,-11,0);
height_coeff_write(0,65,-14,0);
height_coeff_write(1,65,132,0);
height_coeff_write(2,65,155,0);
height_coeff_write(3,65,-16,0);
height_coeff_write(0,66,-8,0);
height_coeff_write(1,66,80,0);
height_coeff_write(2,66,203,0);
height_coeff_write(3,66,-18,0);
height_coeff_write(0,67,-3,1);
height_coeff_write(1,67,35,1);
height_coeff_write(2,67,238,1);
height_coeff_write(3,67,-15,1);
height_coeff_write(0,68,0,0);
height_coeff_write(1,68,3,0);
height_coeff_write(2,68,255,0);
height_coeff_write(3,68,-3,0);
height_coeff_write(0,69,-11,0);
height_coeff_write(1,69,247,0);
height_coeff_write(2,69,22,0);
height_coeff_write(3,69,-1,0);
height_coeff_write(0,70,-18,0);
height_coeff_write(1,70,217,0);
height_coeff_write(2,70,63,0);
height_coeff_write(3,70,-6,0);
height_coeff_write(0,71,-18,0);
height_coeff_write(1,71,173,0);
height_coeff_write(2,71,113,0);
height_coeff_write(3,71,-12,0);
height_coeff_write(0,72,-13,0);
height_coeff_write(1,72,122,0);
height_coeff_write(2,72,164,0);
height_coeff_write(3,72,-17,0);
height_coeff_write(0,73,-7,1);
height_coeff_write(1,73,71,1);
height_coeff_write(2,73,210,1);
height_coeff_write(3,73,-18,1);
height_coeff_write(0,74,-2,0);
height_coeff_write(1,74,28,0);
height_coeff_write(2,74,243,0);
height_coeff_write(3,74,-13,0);
		
		scaler_height_phases_write(75);


		scaler_enable_write(1);
	}
}


void start_dma(){
	reader_reset_write(1);
	//reader_start_address_write(0);
	reader_transfer_size_write(640*512);
	reader_burst_size_write(128);
	reader_enable_write(1);


	//writer_reset_write(1);
	//writer_start_address_write(0);
	//writer_transfer_size_write(640*512);
	//writer_burst_size_write(128);
	//writer_enable_write(1);
}

void stop_dma(){
	reader_enable_write(0);
	reader_reset_write(1);


	//writer_enable_write(0);	
	//writer_reset_write(1);
}

int main(int i, char **c)
{	


	console_set_write_hook((console_write_hook)terminal_write);
	
	terminal_enable_write(1);

	//rgb_div_m_write(400000);
    //rgb_config_write(2);


	terminal_set_bg(TERMINAL_TRANSPARENT);
	terminal_set_fg(TERMINAL_TRANSPARENT);
	terminal_clear();


	//terminal_set_fg(TERMINAL_CYAN);
	printf("     ______    ___   __   __   _______ \n");
	printf("    |      |  |___| |  | |  | |   _   |\n");
	printf("    |  _    |  ___  |  |_|  | |  |_|  |\n");
	printf("    | | |   | |   | |       | |       |\n");
	printf("    | |_|   | |   | |       | |       |\n");
	printf("    |       | |   |  |     |  |   _   |\n");
	printf("    |______|  |___|   |___|   |__| |__|\n");


	//terminal_set_fg(TERMINAL_YELLOW);
	printf("   - Digital Video Interface for Boson -\n");
	//terminal_set_fg(TERMINAL_CYAN);

 	printf("\n (c) Copyright 2019-2020 GetLabs \n");
 	printf(" fw built: "__DATE__ " " __TIME__ " \n\n");

 	printf("   Firmware git sha1: "DIVA_GIT_SHA1"\n");
 	printf("      Migen git sha1: "MIGEN_GIT_SHA1"\n");
 	printf("      LiteX git sha1: "LITEX_GIT_SHA1"\n");

	printf("--==========-- \e[1mHyperRAM Init\e[0m ===========--\n");
	

	/* On power up we need these to be set to 0 so that 
	 * PRBS memtest still works */
	buffers_adr0_write(0x0);
	buffers_adr1_write(0x0);
	buffers_adr2_write(0x0);

	hyperram_init();
	printf("\n");	
	prbs_memtest(HYPERRAM_BASE, HYPERRAM_SIZE);

	
	terminal_set_bg(TERMINAL_TRANSPARENT);
	
	bool load_defaults = false;
	if(button_raw_read() & 0x00000002){
		load_defaults = true;
	}
	init_settings(load_defaults);
	
	//terminal_clear();
	terminal_set_bg(TERMINAL_BLACK);
	

	/* Boson Init */
	boson_init();

	terminal_set_cursor(0,20);

	/* Configure frame buffers, 
	* each frame currently takes up 0x140000 bytes in RAM */
	buffers_adr0_write(0x000000);
	buffers_adr1_write(0x180000);
	buffers_adr2_write(0x300000);

	reader_reset_write(1);
	reader_transfer_size_write(640*512);
	reader_burst_size_write(128);
	reader_enable_write(1);


	writer_reset_write(1);
	writer_transfer_size_write(640*512);
	writer_burst_size_write(128);
	writer_enable_write(1);
	

	framer_width_write(800);
	framer_height_write(600);

	framer_x_start_write(213 + (800-640)/2);
	framer_y_start_write(27 +  (600-512)/2);

	switch_mode(_settings.scaler_enable);

	bool debug_window_open = false;

    while(1) {
		
		/* Print debug window */
		if(_settings.debug_info_overlay || debug_window_open){
			/* Draw the main settings window */
			const uint32_t width = 48;
			const uint32_t height = 5;
			uint32_t window_x = 50;
			uint32_t window_y = 1;

			if(debug_window_open & !_settings.debug_info_overlay)
			{
				/* Close window */
				terminal_set_fg(TERMINAL_TRANSPARENT);
				terminal_set_bg(TERMINAL_TRANSPARENT);
				terminal_fill(window_x, window_y, width+1, height+1);

			}else if(!debug_window_open & _settings.debug_info_overlay){
				/* Open window */
				treminal_draw_box(window_x, window_y, width, height);
			}else{
					
				terminal_set_fg(TERMINAL_WHITE);
				terminal_set_bg(TERMINAL_BLUE);
		
				terminal_set_cursor(++window_x, window_y++);
				printf("Boson Interface debug info:");
		
				terminal_set_cursor(++window_x, window_y++);
				printf("Clk Freq: %u Hz", video_debug_freq_value_read());

				video_debug_latch_write(1);
				terminal_set_cursor(window_x, window_y++);
				printf("VSync: %8u | LOW %8u HIGH %8u", video_debug_vsync_low_read() + video_debug_vsync_high_read(), video_debug_vsync_low_read(), video_debug_vsync_high_read());
				terminal_set_cursor(window_x, window_y++);
				printf("HSync: %8u | LOW %8u HIGH %8u", video_debug_hsync_low_read() + video_debug_hsync_high_read(), video_debug_hsync_low_read(), video_debug_hsync_high_read());
				terminal_set_cursor(window_x, window_y++);
				printf("Lines: %8u ", video_debug_lines_read());
			}

			debug_window_open = _settings.debug_info_overlay;
		}


		msleep(2);
		
		/* Collect button events and pass them to the menu state machine */
		event_t e = 0;
		uint32_t b = button_events_read();

		if(b & 0x00000002){
			e |= BUTTON_B_PRESS;
		}
		if(b & 0x00000001){
			e |= BUTTON_A_PRESS;
		}
		if(b & 0x00000008){
			e |= BUTTON_B_HOLD;
		}
		if(b & 0x00000004){
			e |= BUTTON_A_HOLD;
		}
		
		if(e){
			menu_act(e);
		}

	}
	
	return 0;
}

