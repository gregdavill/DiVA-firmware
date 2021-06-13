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

#include <irq.h>

#include <ppu.h>


/* prototypes */
void isr(void);


void isr(void){
	__attribute__((unused)) unsigned int irqs;

	irqs = irq_pending() & irq_getmask();

	if(irqs & (1 << PPU_INTERRUPT)){
		gui_isr();
		ppu_ev_pending_write(-1);
	}
}



int main(int i, char **c)
{	
	irq_setie(1);

	gui_init();


	ppu_start();

	int j = 600;
	while(1){

	}


	
	return 0;
}

