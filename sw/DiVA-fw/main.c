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


uint32_t test_write(uint32_t a){
	uint32_t b = 0;

	test_clear_write(1);

	test_reader_addr_write(0);
	test_reader_len_write(1);
	
	test_writer_addr_write(0);
	test_writer_len_write(1);

	test_reader_enable_write(1);
	test_source_data_write(a);

	test_writer_enable_write(1);

	return test_sink_data_read();	
}



void write_pixels(int line, int colour){
	test_clear_write(1);

	test_reader_addr_write(line);
	test_reader_len_write(1920);
	



	test_reader_enable_write(1);

	for(int i = 0; i < 1920; i++)
	test_source_data_write(rand());


}

void inline swap(int a, int b){
	int c = a;
	a = b;
	b = c;
}

void write_line(int x0, int y0, int x1, int y1,
                             uint32_t color) {

  int steep = abs(y1 - y0) > abs(x1 - x0);
  if (steep) {
    swap(x0, y0);
    swap(x1, y1);
  }

  if (x0 > x1) {
    swap(x0, x1);
    swap(y0, y1);
  }

  int dx, dy;
  dx = x1 - x0;
  dy = abs(y1 - y0);

  int err = dx / 2;
  int ystep;

  if (y0 < y1) {
    ystep = 1;
  } else {
    ystep = -1;
  }

  for (; x0 <= x1; x0++) {
    if (steep) {
      write_pixel(y0, x0, color);
    } else {
      write_pixel(x0, y0, color);
    }
    err -= dy;
    if (err < 0) {
      y0 += ystep;
      err += dx;
    }
  }
}

void write_pixel(int x, int y, int colour){
	//test_clear_write(1);
	test_reader_addr_write(x + y*1919);
	test_reader_len_write(1);
	test_reader_enable_write(1);

	test_source_data_write(colour);
}

void start_pixels(){
	test_writer_pix_addr_write(0);
	test_writer_pix_len_write(1920*1080);
	test_writer_pix_enable_write(1);

}



void io_shift(){
	test_loadn_write(1);
	test_direction_write(1);

	/* 25ps of delay per tap.
	   Each rising edge adds to the io delay */
	for(int i = 0; i < 10; i++){ 
		test_move_write(1);
		test_move_write(0);
	}
}

void screen_blank(){
	test_reader_addr_write(0);
	test_reader_len_write(1080*1920);
	test_reader_blank_write(1);

	test_reader_enable_write(1);

	msleep(100);
	
	test_reader_blank_write(0);
}

int main(int i, char **c)
{	


	console_set_write_hook(terminal_write);

	rgb_div_m_write(60000*5);
    rgb_config_write(2);


	printf("\n\n");
	printf("  ______    ___   __   __   _______ \n");
	printf(" |      |  |___| |  | |  | |   _   |\n");
	printf(" |  _    |  ___  |  |_|  | |  |_|  |\n");
	printf(" | | |   | |   | |       | |       |\n");
	printf(" | |_|   | |   | |       | |       |\n");
	printf(" |       | |   |  |     |  |   _   |\n");
	printf(" |______|  |___|   |___|   |__| |__|\n");

	printf("- Digital Video Interface for Boson -\n");
	
// 	printf("\n (c) Copyright 2019-2020 GetLabs \n");
// 	printf(" fw built: "__DATE__ " " __TIME__ " \n\n");

// 	printf("   Firmware git sha1: "DIVA_GIT_SHA1"\n");
// 	printf("      Migen git sha1: "MIGEN_GIT_SHA1"\n");
// 	printf("      LiteX git sha1: "LITEX_GIT_SHA1"\n");
// 	printf("\n");
	

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


    printf("--========== Initialization ============--\n");
	for(int i = 0; i < 20; i++){
		hyperram_init();
		io_shift();
	}


	screen_blank();
	start_pixels();
//	memtest((unsigned int*)HYPERRAM_BASE);
	printf("\n");

    printf("--============= \e[1mConsole\e[0m ================--\n");

	uint32_t line = 0;

	uint32_t colour = 0xFF22410;
    while(1) {
		printf("Overrun: %08x\r", terminal_overrun_read());

		for(int i = 0; i < 1920; i += 20){
			write_line(0,0,i, 1079, colour);
		}

		colour = rand();
		
		//putsnonl("DiVA> ");
		//readstr(buffer, 64);
		//do_command(buffer);
	}
	return 0;
}
