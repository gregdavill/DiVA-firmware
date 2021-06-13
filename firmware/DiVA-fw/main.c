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


#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "tusb.h"

/* prototypes */
void isr(void);


extern volatile uint32_t system_ticks;
void isr(void){
	__attribute__((unused)) unsigned int irqs;

	irqs = irq_pending() & irq_getmask();

	if(irqs & (1 << PPU_INTERRUPT)){
		gui_isr();
		ppu_ev_pending_write(-1);
	}

	
#if CFG_TUSB_RHPORT0_MODE == OPT_MODE_DEVICE
  if (irqs & (1 << USB_INTERRUPT)) {
    tud_int_handler(0);
  }
#endif
  if (irqs & (1 << TIMER0_INTERRUPT)) {
    system_ticks++;
    timer0_ev_pending_write(1);
  }
}

/* Blink pattern
 * - 250 ms  : device not mounted
 * - 1000 ms : device mounted
 * - 2500 ms : device is suspended
 */
enum  {
  BLINK_NOT_MOUNTED = 250,
  BLINK_MOUNTED = 1000,
  BLINK_SUSPENDED = 2500,
};

static uint32_t blink_interval_ms = BLINK_NOT_MOUNTED;

void led_blinking_task(void);
void cdc_task(void);


int main(int i, char **c)
{	
//	irq_setie(1);

//	gui_init();


//	ppu_start();

  //board_init();
  irq_setmask(0);
  irq_setie(1);
  
  timer_init();
  tusb_init();

	while(1){
    tud_task(); // tinyusb device task
  //  led_blinking_task();

    cdc_task();

	}


	
	return 0;
}




//--------------------------------------------------------------------+
// USB CDC
//--------------------------------------------------------------------+
void cdc_task(void)
{
  // connected() check for DTR bit
  // Most but not all terminal client set this when making connection
  // if ( tud_cdc_connected() )
  {
    // connected and there are data available
    if ( tud_cdc_available() )
    {
      // read datas
      char buf[64];
      uint32_t count = tud_cdc_read(buf, sizeof(buf));
      (void) count;

      // Echo back
      // Note: Skip echo by commenting out write() and write_flush()
      // for throughput test e.g
      //    $ dd if=/dev/zero of=/dev/ttyACM0 count=10000
      tud_cdc_write(buf, count);
      tud_cdc_write_flush();
    }
  }
}

// Invoked when cdc when line state changed e.g connected/disconnected
void tud_cdc_line_state_cb(uint8_t itf, bool dtr, bool rts)
{
  (void) itf;
  (void) rts;

  // TODO set some indicator
  if ( dtr )
  {
    // Terminal connected
  }else
  {
    // Terminal disconnected
  }
}

// Invoked when CDC interface received data from host
void tud_cdc_rx_cb(uint8_t itf)
{
  (void) itf;
}
