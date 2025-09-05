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

#include <scaler.h>

#include <generated/csr.h>
#include <generated/mem.h>
#include <generated/git.h>

#include "include/terminal_menu.h"

/* prototypes */
void isr(void);


void isr(void){

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

	switch_mode(_settings.scaler_enable);
	
	reader_reset_write(1);
	reader_transfer_size_write(640*512);
	reader_burst_size_write(128);
	reader_enable_write(1);

	writer_reset_write(1);
	writer_transfer_size_write(640*512);
	writer_burst_size_write(128);
	writer_enable_write(1);
	
	bool debug_window_open = false;

    while(1) {
		
		/* Print debug window */
		if(_settings.debug_info_overlay || debug_window_open){
			/* Draw the main settings window */
			const uint32_t width = 48;
			const uint32_t height = 5;
			uint32_t window_x = 50;
			uint32_t window_y = 1;

			if(debug_window_open && !_settings.debug_info_overlay)
			{
				/* Close window */
				terminal_set_fg(TERMINAL_TRANSPARENT);
				terminal_set_bg(TERMINAL_TRANSPARENT);
				terminal_fill(window_x, window_y, width+1, height+1);

			}else if(!debug_window_open && _settings.debug_info_overlay){
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

