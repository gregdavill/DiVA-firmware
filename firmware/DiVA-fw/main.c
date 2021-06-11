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


#include <irq.h>

#include <ppu.h>


/* prototypes */
void isr(void);


void isr(void){
	__attribute__((unused)) unsigned int irqs;

	irqs = irq_pending() & irq_getmask();

	if(irqs & (1 << PPU_INTERRUPT))
		next_frame();
}


static volatile uint32_t array[1024];

const int sin[] = {200, 219, 238, 258, 276, 294, 311, 326, 341, 354, 366, 376, 384, 391, 396, 399, 399, 399, 396, 391, 384, 376, 366, 354, 341, 327, 311, 294, 276, 258, 239, 219, 200, 180, 161, 142, 123, 106, 89, 73, 58, 45, 33, 23, 15, 8, 3, 1, 0, 0, 3, 8, 15, 23, 33, 45, 58, 72, 88, 105, 122, 141, 160, 179};


const int font[] = {
	0x00000000, 0x00000000, 0x003A7000, 0x004FB000, 0x004FA000, 0x003FA000, 0x003E9000, 0x003E9000, 0x002E8000, 0x002B6000, 0x00021000, 0x003C9000, 0x004FB000, 0x00143000, 0x00000000, 
0x00000000, 0x00000000, 0x03735600, 0x07F6CD10, 0x06F5BC10, 0x05E3AB00, 0x03C28900, 0x00201100, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 
0x00000000, 0x00000000, 0x00000000, 0x00793A50, 0x00BC5F60, 0x06EDAF81, 0x2CFFFFC2, 0x05F8BE40, 0x05F6BC10, 0x07F6CB10, 0x6EFDFE60, 0x5DEBFC40, 0x0CC5F600, 0x1CA6E400, 0x03224100, 0x00000000, 
0x00000000, 0x00002000, 0x0005C200, 0x017CF810, 0x09FEFE60, 0x1DB7E520, 0x1DB6E200, 0x0AFCE300, 0x02BFF910, 0x007ECF60, 0x007D5E90, 0x058D6E90, 0x1CEFEE50, 0x04BFA500, 0x006D2000, 0x00240000, 
0x00000000, 0x00000000, 0x01210000, 0x4CDB2000, 0xAE9F8000, 0xCC4E9000, 0x9FDF7481, 0x18AABEA1, 0x03AED710, 0x4EDAA940, 0x583CEED3, 0x003E97F5, 0x002ECAF4, 0x0007EE91, 0x00002200, 0x00000000, 
0x00000000, 0x00000000, 0x00121000, 0x06DDC500, 0x2DC7DD10, 0x3F809E20, 0x2DC4DC10, 0x07FEE610, 0x05FF77A1, 0x2DEF99D1, 0x8F69EDD1, 0xAE32DFC1, 0x8FA6CFA0, 0x2BEECBC2, 0x01221110, 0x00000000, 
0x00000000, 0x00000000, 0x00275000, 0x004FB000, 0x003E9000, 0x002E8000, 0x001C6000, 0x00021000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 
0x00000000, 0x00000000, 0x00005500, 0x0006D400, 0x002D7000, 0x008D2000, 0x01C90000, 0x03E50000, 0x04E40000, 0x05E30000, 0x04E40000, 0x03E60000, 0x01CA0000, 0x007D2000, 0x001C9000, 0x0004C600, 
0x00004400, 0x00000000, 0x02720000, 0x01AB1000, 0x002D8000, 0x0007D200, 0x0003E600, 0x0001C900, 0x0000BB00, 0x0000AB00, 0x0000BB00, 0x0001D900, 0x0003E500, 0x0009C100, 0x003D6000, 0x01B90000, 
0x02510000, 0x00000000, 0x00010000, 0x001B6000, 0x132D7230, 0x5DDFDDB1, 0x14BFE720, 0x02CCD700, 0x06B27B10, 0x00100100, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 
0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00011000, 0x002C7000, 0x002E8000, 0x013E9110, 0x3CDFED80, 0x168FB740, 0x002E8000, 0x002E8000, 0x00174000, 0x00000000, 0x00000000, 
0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00177100, 0x005FC100, 0x007F7000, 0x00AD2000, 0x01A80000, 
0x00110000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00111000, 0x06CCCA10, 0x04888710, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 
0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00254000, 0x007FD100, 0x007FD100, 0x00243000, 0x00000000, 
0x00000000, 0x00000000, 0x00000000, 0x00000770, 0x00002D60, 0x00007D20, 0x0001C800, 0x0005D300, 0x000BA000, 0x003E5000, 0x008C1000, 0x02D70000, 0x06D20000, 0x1B900000, 0x3B300000, 0x01000000, 
0x00000000, 0x00000000, 0x00121000, 0x03BDD700, 0x0AE6AE30, 0x1D905F70, 0x3E61BF90, 0x4E56CDB0, 0x4F7B6CB0, 0x4FDA1CB0, 0x3EE31DA0, 0x2DA03E70, 0x0AD69E40, 0x03CED800, 0x00132000, 0x00000000, 
0x00000000, 0x00000000, 0x00000000, 0x0028A400, 0x06DFF600, 0x1B97F600, 0x0204F600, 0x0004F600, 0x0004F600, 0x0004F600, 0x0004F600, 0x0004F600, 0x0004F600, 0x0004E600, 0x00014100, 0x00000000, 
0x00000000, 0x00000000, 0x00000000, 0x039CB500, 0x1CCAED20, 0x15107F50, 0x00005F50, 0x00008E30, 0x0001CC10, 0x0007E600, 0x003DA100, 0x01BD2000, 0x09F84310, 0x1CFEEE60, 0x03444420, 0x00000000, 
0x00000000, 0x00000000, 0x00000000, 0x19AAAA50, 0x19BBDF70, 0x0003DB20, 0x001BC300, 0x009F7100, 0x01CFEA10, 0x00349F60, 0x00003E80, 0x00003E80, 0x05439F60, 0x0AEEEA10, 0x02564100, 0x00000000, 
0x00000000, 0x00000000, 0x00000000, 0x0002A800, 0x0009FC00, 0x003EFC00, 0x009CDC00, 0x03D6CC00, 0x09B2CC00, 0x3D51CC10, 0x8FAAEE91, 0x6CCCFFB1, 0x0001CC10, 0x0000BB00, 0x00003300, 0x00000000, 
0x00000000, 0x00000000, 0x00000000, 0x06AAAA30, 0x0AFBBA30, 0x0AD10000, 0x0AC10000, 0x0BEAA500, 0x0BEBEE30, 0x03305F70, 0x00003E80, 0x00004F70, 0x0533AF50, 0x0BEEE910, 0x02564100, 0x00000000, 
0x00000000, 0x00000000, 0x00012100, 0x019DDC20, 0x06E95610, 0x0BC10000, 0x1DA44200, 0x2EEDED30, 0x3ED45E90, 0x3E901DB0, 0x2E801CB0, 0x1DA02DA0, 0x0AE68F70, 0x03CEE910, 0x00132000, 0x00000000, 
0x00000000, 0x00000000, 0x00000000, 0x19AAAA50, 0x1ABBCF70, 0x00006E40, 0x0000BB10, 0x0003E700, 0x0008E300, 0x001CB000, 0x004E7000, 0x008E3000, 0x01CC1000, 0x02D90000, 0x01420000, 0x00000000, 
0x00000000, 0x00000000, 0x00121000, 0x05CDD910, 0x1DC68F70, 0x3E701D90, 0x2D903D70, 0x08E9CB20, 0x04EEFA10, 0x2CA37E70, 0x5E401CC0, 0x6E400BC1, 0x3EB57E90, 0x06DEEA20, 0x00132000, 0x00000000, 
0x00000000, 0x00000000, 0x00121000, 0x05CDD800, 0x1DD6AE40, 0x4F703E70, 0x5F602E90, 0x4F603E90, 0x2EA28F90, 0x08EDDF80, 0x00455E70, 0x00006F40, 0x0566DC10, 0x08EEC500, 0x01231000, 0x00000000, 
0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00132000, 0x005EB100, 0x006FC100, 0x00265000, 0x00000000, 0x00000000, 0x00254000, 0x006FC100, 0x006FC100, 0x00143000, 0x00000000, 
0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00033000, 0x003ED200, 0x004FD200, 0x00165000, 0x00000000, 0x00000000, 0x00154000, 0x006FB000, 0x009F6000, 0x00BD2000, 0x01C80000, 
0x00410000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000230, 0x00005C80, 0x003AD820, 0x18DA3000, 0x4E600000, 0x3CB40000, 0x029D9200, 0x0004BD50, 0x00001770, 0x00000000, 0x00000000, 
0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x28999950, 0x2ABBBB70, 0x00000000, 0x14555530, 0x3DEEEE90, 0x02222210, 0x00000000, 0x00000000, 0x00000000, 
0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x13000000, 0x2C920000, 0x04BD7100, 0x0016CB40, 0x00002BB0, 0x00017D80, 0x015CC500, 0x1AD82000, 0x29300000, 0x00000000, 0x00000000, 
0x00000000, 0x00000000, 0x00000000, 0x06ACB710, 0x2CB9BF70, 0x02002DB0, 0x00003E90, 0x0001BE30, 0x0008E600, 0x002DA000, 0x003C5000, 0x00021000, 0x006C6000, 0x007F8000, 0x00242000, 0x00000000, 
0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00377400, 0x06EDCE60, 0x2DA34AC1, 0x6E6ADED1, 0x8E7E6BD1, 0x9D8D28D1, 0x9D9D28D1, 0x8D8E59D1, 0x6E6CEE90, 0x3EA35510, 0x08ECAB30, 0x016AA810, 
0x00000000, 0x00000000, 0x00000000, 0x003A8000, 0x008FD200, 0x00BBE400, 0x02D7D700, 0x04E4BA00, 0x07D18D10, 0x0AC27E30, 0x1DFDEF60, 0x3E967EA0, 0x6E300BC1, 0x9D2008E3, 0x33000241, 0x00000000, 
0x00000000, 0x00000000, 0x01221000, 0x2CDDD910, 0x2EB5AF60, 0x2E902E90, 0x2E903E70, 0x2ED9CB20, 0x2EECEB20, 0x2E914D90, 0x2E900BC1, 0x2E901CC1, 0x2EB48F90, 0x2CEEDA20, 0x01332000, 0x00000000, 
0x00000000, 0x00000000, 0x00012100, 0x019DDD40, 0x08F95740, 0x2DB10000, 0x4F600000, 0x5F500000, 0x6F400000, 0x5F500000, 0x4F600000, 0x2DB10000, 0x09F95640, 0x019DED60, 0x00023200, 0x00000000, 
0x00000000, 0x00000000, 0x01221000, 0x3DDDC700, 0x4FA6BF50, 0x4F702DB0, 0x4F700AD1, 0x4F7009E2, 0x4F7008E2, 0x4F7009E2, 0x4F700AD1, 0x4F702DB0, 0x4FA5BF60, 0x3DEED700, 0x02331000, 0x00000000, 
0x00000000, 0x00000000, 0x00000000, 0x08AAAA40, 0x1CEBBB50, 0x1CC10000, 0x1CB00000, 0x1CD55510, 0x1CFEED40, 0x1CC32200, 0x1CB00000, 0x1CB00000, 0x1CC43310, 0x1CFEEE60, 0x03444420, 0x00000000, 
0x00000000, 0x00000000, 0x00000000, 0x07AAAA40, 0x0BFBBB50, 0x0BD20000, 0x0BD10000, 0x0BE65510, 0x0BFEED40, 0x0BD42200, 0x0BD10000, 0x0BD10000, 0x0BD10000, 0x0AC10000, 0x03300000, 0x00000000, };

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

void next_frame(){
	ppu_ev_pending_write(ppu_ev_pending_read());

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


int main(int i, char **c)
{	

	ppu_ev_pending_write(ppu_ev_pending_read());
	ppu_ev_enable_write(1);

	irq_setmask( (1 << PPU_INTERRUPT));

	irq_setie(1);

	ppu_ppu_pc_write((uint32_t)array >> 2);

	uint32_t* ptr = (ppu_instr_t*)array;

	//ptr += cproc_clip(ptr, 0, 40);
	//ptr += cproc_fill(ptr, 0,255,0);
	//ptr += cproc_sync(ptr);

	for(int i = 0; i < sizeof(font)/sizeof(uint32_t); i++){
		ptr[i + 512] = ~font[i];
	}

	ppu_initiator_enable_write(0);
	ppu_initiator_hres_write(1280);
	ppu_initiator_hsync_start_write(1280 + 48);
	ppu_initiator_hsync_end_write(1280 + 48 + 32);
	ppu_initiator_hscan_write(1440);
	ppu_initiator_vres_write(720);
	ppu_initiator_vsync_start_write(720 + 3);
	ppu_initiator_vsync_end_write(720 + 3 + 5);
	ppu_initiator_vscan_write(741);
	ppu_initiator_enable_write(1);

	int j = 600;
	while(1){

	}


	
	return 0;
}

