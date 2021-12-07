#include <stdio.h>
#include <stdint.h>

#include "include/time.h"
#include "include/hyperram.h"

#include <generated/csr.h>
#include <generated/mem.h>
#include <generated/git.h>



#ifdef CSR_HYPERRAM_BASE

/* Prototypes */

void set_io_delay(int);
void set_clk_delay(int);
static int basic_memtest(void);


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


void hyperram_init(void){
	int window = 0;
	int clk_del = 0;
	int io_del = 0;

	while(clk_del < 128){
		set_clk_delay(clk_del >> 2);
		set_io_delay(io_del);
		int i = 0;
		printf("%u,%u, %u |", clk_del >> 2, clk_del & 1 ? 1 : 0, clk_del & 2 ? 1 : 0);
		for(i = 0; i < 64; i++){

			int pass = basic_memtest();

			// Shift our PLL
			crg_phase_sel_write(0);
			crg_phase_dir_write(0);
			crg_phase_step_write(0);
			crg_phase_step_write(1);

			if(i & 1)
				printf("%c", pass > 0 ? '0' : '-');

			if(pass == 1){
				window++;
			}
			else if(pass != 1){
				if(window >= 6){
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
				crg_phase_dir_write(1);
				crg_phase_step_write(0);
				crg_phase_step_write(1);
			}
			return;
		}
		window = 0;
		clk_del = (clk_del + 1);

		crg_slip_hr2x90_write(clk_del & 1 ? 1 : 0);
		crg_slip_hr2x_write(clk_del & 2 ? 1 : 0);

		crg_slip_hr2x90_write(0);
		crg_slip_hr2x_write(0);
	}

	printf("\n\n Error: RAM Init failed :(\n Restarting in... ");
	for(int i = 0; i < 5; i++){
		msleep(1000);
		printf("\b%u",5-i);
	}

	while(1){
		reboot_ctrl_write(0xac);
	}
	
}



void prbs_memtest(uint32_t base, uint32_t len){
		uint32_t start;
		uint32_t end;

		/* init timer */
	timer0_en_write(0);
	timer0_reload_write(0);
	timer0_load_write(0xffffffff);
	timer0_en_write(1);

	uint32_t burst = 320;

	reader_source_mux_write(1);
	writer_sink_mux_write(1);

	prbs_source_reset_write(1);

	reader_reset_write(1);
	reader_burst_size_write(burst);
	reader_transfer_size_write(len/4);
	// Currently adr is handled by the buffers module
	//reader_start_address_write(base>>2);


	/* write speed */
	timer0_update_value_write(1);
	start = timer0_value_read();

	reader_enable_write(1);
	while(reader_done_read() == 0);

	timer0_update_value_write(1);
	end = timer0_value_read();

	uint32_t rate = (CONFIG_CLOCK_FREQUENCY*10)/((start-end)/8);
	printf("Write Speed: %u.%u MBytes/s ( %u cycles )\n", rate / 10, rate % 10, start-end);

	writer_reset_write(1);
	writer_burst_size_write(burst);
	writer_transfer_size_write(len/4);
	// Currently adr is handled by the buffers module
	//writer_start_address_write(base>>2);

	prbs_sink_reset_write(1);


	/* write speed */
	timer0_update_value_write(1);
	start = timer0_value_read();

	writer_enable_write(1);
	while(writer_done_read() == 0);

	timer0_update_value_write(1);
	end = timer0_value_read();
	
	rate = (CONFIG_CLOCK_FREQUENCY*10)/((start-end)/8);
	printf("Read Speed:  %u.%u MBytes/s ( %u cycles )\n", rate / 10, rate % 10, start-end);
	
	printf("Memtest: ");
	if(prbs_sink_good_read() == writer_transfer_size_read()){
		printf("%uKB ( 0x%x )...OK\n", 4*prbs_sink_good_read()/1024, 4*prbs_sink_good_read());
	}else {
		printf("Not OK. :(\n Good: 0x%x (%uKB) [%x], Bad: 0x%x\n", prbs_sink_good_read(),4*prbs_sink_good_read()/1024, writer_transfer_size_read(),prbs_sink_bad_read());
	}


	reader_external_sync_write(1);
	writer_external_sync_write(1);

	writer_enable_write(0);
	reader_enable_write(0);
	
	reader_source_mux_write(0);
	writer_sink_mux_write(0);

}



#else


void hyperram_init(){
	return;
}

#endif
