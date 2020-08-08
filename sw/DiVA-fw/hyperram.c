#include <stdio.h>
#include <stdlib.h>
#include <console.h>
#include <string.h>
#include <uart.h>
#include <system.h>
#include <id.h>
#include <irq.h>
#include <crc.h>
#include <stdint.h>
#include <stdbool.h>

#include <generated/csr.h>
#include <generated/mem.h>
#include <generated/git.h>




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



/* 
	Test memory location by writing a value and attempting read-back.
	Try twice to avoid situation where memory is read-only and set from a previous test.
*/
static int basic_memtest(void){

	*((volatile uint32_t*)HYPERRAM_BASE) = 0xFF55AACD;
	if(*((volatile uint32_t*)HYPERRAM_BASE) != 0xFF55AACD)
		return 0;
//
	*((volatile uint32_t*)HYPERRAM_BASE) = 0xA3112233;
	if(*((volatile uint32_t*)HYPERRAM_BASE) != 0xA3112233)
		return 0;
	
	return 1;
}


void hyperram_init(){
	int window = 0;
	int clk_del = 0;
	int io_del = 0;

	while(1){
		set_clk_delay(clk_del);
		set_io_delay(io_del);
		int i = 0;
		printf("%u,%u |", clk_del, io_del);
		for(i = 0; i < 32; i++){

			int pass = basic_memtest();

			// Shift our PLL
			crg_phase_sel_write(0);
			crg_phase_dir_write(1);
			crg_phase_step_write(0);
			crg_phase_step_write(1);

			printf("%c", pass > 0 ? '0' : '-');

			if(pass == 1){
				window++;
			}
			else if(pass != 1){
				if(window >=5){
					break;
				}else {
					window = 0;
				}
			}

		}
		printf("| %d    \r", window );
		if(window >= 5){
			for(i = 0; i < window/2; i++){
				// Shift our PLL up
				crg_phase_sel_write(0);
				crg_phase_dir_write(0);
				crg_phase_step_write(0);
				crg_phase_step_write(1);
			}
			return;
		}
		window = 0;
		clk_del = (clk_del + 1) & 0x7F;
		if(clk_del == 0){
			io_del = (io_del + 1) & 0x7F;
		}
	}
}


