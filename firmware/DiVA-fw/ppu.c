
#include <ppu.h>
#include <generated/csr.h>


#include <irq.h>

void ppu_start(void){

    ppu_initiator_enable_write(0);

	irq_setmask(irq_getmask() | (1 << PPU_INTERRUPT));
    ppu_ev_pending_write(ppu_ev_pending_read());
	ppu_ev_enable_write(1);


    /* Start GDPI output
	
	  1280x720 (0xab) 74.250MHz +HSync +VSync
        h: width  1280 start 1390 end 1430 total 1650 skew    0 clock  45.00KHz
        v: height  720 start  725 end  730 total  750           clock  60.00Hz
	*/
	ppu_initiator_hres_write(1280);
	ppu_initiator_hsync_start_write(1390);
	ppu_initiator_hsync_end_write(1430);
	ppu_initiator_hscan_write(1650);
	ppu_initiator_vres_write(720);
	ppu_initiator_vsync_start_write(725);
	ppu_initiator_vsync_end_write(730);
	ppu_initiator_vscan_write(750);
	ppu_initiator_enable_write(1);
}