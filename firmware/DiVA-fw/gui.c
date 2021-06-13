

#include <ppu.h>
#include <generated/csr.h>

#include <gui/font.h>



static volatile uint32_t array[1024];

const int sin[] = {200, 219, 238, 258, 276, 294, 311, 326, 341, 354, 366, 376, 384, 391, 396, 399, 399, 399, 396, 391, 384, 376, 366, 354, 341, 327, 311, 294, 276, 258, 239, 219, 200, 180, 161, 142, 123, 106, 89, 73, 58, 45, 33, 23, 15, 8, 3, 1, 0, 0, 3, 8, 15, 23, 33, 45, 58, 72, 88, 105, 122, 141, 160, 179};


int counter = 0;

int val = 0;

int hold = 0;

int cnt0 = 0;

int frames = 0;
int sec = 0;
int min = 0;

int cycle_cnt = 0;


int x = 800/2;
int y = 600/2;

size_t square(ppu_instr_t *prog, int x0, int y0, int x1, int y1, int r, int g, int b){
	prog += cproc_branch(prog, 15 + (((uint32_t)prog) >> 2), PPU_CPROC_BRANCH_YLT, y0);			// 3
	prog += cproc_branch(prog, 12 + (((uint32_t)prog) >> 2), PPU_CPROC_BRANCH_YGE, y1 + 2);		// 3
	prog += cproc_clip(prog, x0, x1);															// 1
	prog += cproc_branch(prog,  7 + (((uint32_t)prog) >> 2), PPU_CPROC_BRANCH_YLT, y1);			// 3
	prog += cproc_fill(prog, 0,0,0);															// 1
	prog += cproc_branch(prog,  4 + (((uint32_t)prog) >> 2), PPU_CPROC_BRANCH_ALWAYS, 0);		// 3
	prog += cproc_fill(prog, r,g,b);															// 1
	return 15;
}

size_t blit(ppu_instr_t *prog, int x, int y, int c){
	prog += cproc_blit(prog, PPU_SIZE_16, x, y, ((uint32_t)array >> 2) + (512 + (c*16)));
	return 2;
}



void gui_init(){

    ppu_ppu_pc_write((uint32_t)array >> 2);
	uint32_t* ptr = (ppu_instr_t*)array;

	//ptr += cproc_clip(ptr, 0, 40);
	//ptr += cproc_fill(ptr, 0,255,0);
	//ptr += cproc_sync(ptr);

	for(int i = 0; i < sizeof(font)/sizeof(uint32_t); i++){
		ptr[i + 512] = ~font[i];
	}
}


void gui_isr(){
	timer0_en_write(0);
	timer0_reload_write(0);
	timer0_load_write(CONFIG_CLOCK_FREQUENCY/30);
	timer0_en_write(1);
	timer0_update_value_write(1);

//	cycle_cnt = val;
	val = sin[counter]/4;

			cnt0++;
	if(hold > 0){
		hold--;
	}else{
		counter+=1;
		if(counter == 16){
			hold =100;
		}
		if(counter >= 64){
			counter = 0;
		}
	}


	ppu_instr_t* ptr = (ppu_instr_t*)array;

	uint32_t* vector;

	/* Fill buffers with black */
	ptr += cproc_branch(ptr, ((uint32_t)ptr >> 2) + 5, 2, 2);
	ptr += cproc_clip(ptr, 0,1280);
	ptr += cproc_fill(ptr, 0,0,0);

	/* Draw a square */
	ptr += square(ptr, 0,10 + val,10,20 + val, 0, 32 ,255);
	
	ptr += square(ptr, x - (val >> 4), y - (val >> 4), x + 5 + (val >> 4), y + 5 + (val >> 4), 128, 127, 0 );


	ptr += square(ptr, 17 + x,16 + y ,98 + x, 41 + y, 255, 255 ,255);
	//ptr += square(ptr, 18, 27, 87, 48, 0, 0 ,0);
	

	ptr += blit(ptr, 20 + 8*0 + x, 20 + y, 30);
	ptr += blit(ptr, 20 + 8*1 + x, 20 + y, 15 + min /10 % 10);
	ptr += blit(ptr, 20 + 8*2 + x, 20 + y, 15 + min % 10);
	ptr += blit(ptr, 20 + 8*3 + x, 20 + y, 25);
	ptr += blit(ptr, 20 + 8*4 + x, 20 + y, 15 + sec /10 % 10);
	ptr += blit(ptr, 20 + 8*5 + x, 20 + y, 15 + sec % 10);
	ptr += blit(ptr, 20 + 8*6 + x, 20 + y, 25);
	ptr += blit(ptr, 20 + 8*7 + x, 20 + y, 15 + frames/10 % 10);
	ptr += blit(ptr, 20 + 8*8 + x, 20 + y, 15 + frames % 10);

	if(++frames >= 60){
		frames = 0;
		if(++sec >= 60){
			sec = 0;
			if(++min >= 60){
				min = 0;
			}
		}
	}


	for(int i = 0; i < 1; i++){
		ptr += square(ptr, 78 + 72*i, 18 ,147 + 72*i, 38, 255, 255 ,255);
		ptr += blit(ptr, 80 + 72*i + 8*0, 20, 15 + cycle_cnt /10000000 % 10);
		ptr += blit(ptr, 80 + 72*i + 8*1, 20, 15 + cycle_cnt /1000000 % 10);
		ptr += blit(ptr, 80 + 72*i + 8*2, 20, 15 + cycle_cnt /100000 % 10);
		ptr += blit(ptr, 80 + 72*i + 8*3, 20, 15 + cycle_cnt /10000 % 10);
		ptr += blit(ptr, 80 + 72*i + 8*4, 20, 15 + cycle_cnt /1000 % 10);
		ptr += blit(ptr, 80 + 72*i + 8*5, 20, 15 + cycle_cnt /100 % 10);
		ptr += blit(ptr, 80 + 72*i + 8*6, 20, 15 + cycle_cnt /10 % 10);
		ptr += blit(ptr, 80 + 72*i + 8*7, 20, 15 + cycle_cnt % 10);
	}

	ptr += cproc_branch(ptr, 6*(18 + 15) + ((uint32_t)ptr >> 2), 1, 100);
	for(int i = 0; i < 2; i++){
		ptr += square(ptr, 78 + 72*i, 118 ,149 + 72*i, 138, 255, 255 ,255);
		ptr += blit(ptr, 80 + 72*i + 8*0, 120, 15 + cycle_cnt /10000000 % 10);
		ptr += blit(ptr, 80 + 72*i + 8*1, 120, 15 + cycle_cnt /1000000 % 10);
		ptr += blit(ptr, 80 + 72*i + 8*2, 120, 15 + cycle_cnt /100000 % 10);
		ptr += blit(ptr, 80 + 72*i + 8*3, 120, 15 + cycle_cnt /10000 % 10);
		ptr += blit(ptr, 80 + 72*i + 8*4, 120, 15 + cycle_cnt /1000 % 10);
		ptr += blit(ptr, 80 + 72*i + 8*5, 120, 15 + cycle_cnt /100 % 10);
		ptr += blit(ptr, 80 + 72*i + 8*6, 120, 15 + cycle_cnt /10 % 10);
		ptr += blit(ptr, 80 + 72*i + 8*7, 120, 15 + cycle_cnt % 10);
	}



	x = 400 + sin[counter & 63]/2;
	y = 200 + sin[(counter + 16) & 63] / 2;


	ptr += cproc_sync(ptr);
	timer0_update_value_write(1);
    cycle_cnt = ((uint32_t)(ptr) >> 2) & 0xFFFF;//CONFIG_CLOCK_FREQUENCY/30 - timer0_value_read();
}