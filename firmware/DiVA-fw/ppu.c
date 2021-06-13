
#include <ppu.h>
#include <generated/csr.h>


#include <irq.h>

void ppu_start(void){

    ppu_initiator_enable_write(0);

    ppu_ev_pending_write(ppu_ev_pending_read());
	ppu_ev_enable_write(1);

	irq_setmask( (1 << PPU_INTERRUPT));

    /* Start GDPI output at 1280x720 */
	ppu_initiator_hres_write(1280);
	ppu_initiator_hsync_start_write(1280 + 48);
	ppu_initiator_hsync_end_write(1280 + 48 + 32);
	ppu_initiator_hscan_write(1440);
	ppu_initiator_vres_write(720);
	ppu_initiator_vsync_start_write(720 + 3);
	ppu_initiator_vsync_end_write(720 + 3 + 5);
	ppu_initiator_vscan_write(741);
	ppu_initiator_enable_write(1);
}