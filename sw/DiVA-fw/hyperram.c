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




void write_hyperram(uint32_t dat){
	hyperram_reader_start_address_write(0);
	hyperram_reader_transfer_size_write(1);
	hyperram_reader_enable_write(1);

	//hyperram_source_data_write(dat);
	hyperram_source_data_write(dat);
}

uint32_t read_hyperram(void){
	hyperram_writer_start_address_write(0);
	hyperram_writer_transfer_size_write(1);
	hyperram_writer_enable_write(1);

	//hyperram_sink_data_read();
	return hyperram_sink_data_read();
}

/* 
	Test memory location by writing a value and attempting read-back.
	Try twice to avoid situation where memory is read-only and set from a previous test.
*/
static int basic_memtest(volatile uint32_t* addr){

	hyperram_clear_write(1);
	
	write_hyperram(0xFF55AACD);
	if(read_hyperram() != 0xFF55AACD)
		return 0;

	hyperram_clear_write(1);
	
	write_hyperram(0x00112233);
	if(read_hyperram() != 0x00112233)
		return 0;

	//*((volatile uint32_t*)HYPERRAM_BASE) = 0xFF55AACD;
	//if(*((volatile uint32_t*)HYPERRAM_BASE) != 0xFF55AACD)
	//	return 0;
//
	//*((volatile uint32_t*)HYPERRAM_BASE) = 0x00112233;
	//if(*((volatile uint32_t*)HYPERRAM_BASE) != 0x00112233)
	//	return 0;
	
	return 1;
}


void hyperram_init(){
	int window = 0;
	int i = 0;
	printf("|");
	for(i = 0; i < 128; i++){

		int pass = basic_memtest(0);

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
			if(window > 2){
				break;
			}else {
				window = 0;
			}
		}

	}
	printf("| %x \n", window );
	if(window > 2){
		for(i = 0; i < window/2; i++){
			// Shift our PLL up
			crg_phase_sel_write(0);
			crg_phase_dir_write(0);
			crg_phase_step_write(0);
			crg_phase_step_write(1);
		}
	}
}


