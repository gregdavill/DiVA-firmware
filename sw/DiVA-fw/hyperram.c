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



uint32_t test_write(uint32_t a);
/* 
	Test memory location by writing a value and attempting read-back.
	Try twice to avoid situation where memory is read-only and set from a previous test.
*/
static int basic_memtest(volatile uint32_t* addr){

	if(test_write(0xFF55AACD) != 0xFF55AACD)
		return 0;

	if(test_write(0xFF55AAC0) != 0xFF55AAC0)
		return 0;

	if(test_write(0x0123FECD) != 0x0123FECD)
		return 0;



	/* Test stream?*/

	test_clear_write(1);

	test_reader_addr_write(100);
	test_reader_len_write(16);
	
	test_writer_addr_write(100);
	test_writer_len_write(16);

	test_reader_enable_write(1);

	for(int i = 0; i < 16; i++)
		test_source_data_write(1 << i);

	test_writer_enable_write(1);


	for(int i = 0; i < 16; i++)
		if(test_sink_data_read() != (1 << i))
			return 0;

	
	return 1;
}


void hyperram_init(){

	int window = 0;
	int i = 0;
	bool dir = false;
	printf("|");
	for(i = 0; i < 64; i++){

		int pass = basic_memtest(0);

		// Shift our PLL
		crg_phase_sel_write(0);
		crg_phase_dir_write(dir);
		crg_phase_step_write(0);
		crg_phase_step_write(1);

		if((pass == 0) & !dir)
			dir = true;

		if(!dir)
			continue;

	    printf("%c", pass > 0 ? '0' : '-');

		if(pass == 1){
			window++;
		}
		else if(pass != 1){
			if(window > 8){
				break;
			}else {
				window = 0;
			}
		}

	}
	printf("| - ");
	printf("Window: %u \n", window, i);

	for(i = 0; i < window/2; i++){
		// Shift our PLL up
		crg_phase_sel_write(0);
		crg_phase_dir_write(0);
		crg_phase_step_write(0);
		crg_phase_step_write(1);
	}
}


