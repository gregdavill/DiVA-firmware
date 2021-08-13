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
#include "usb/cdc.h"

volatile uint8_t flag = 0;

/* prototypes */
void isr(void);

extern volatile uint32_t system_ticks;
void isr(void){
	__attribute__((unused)) unsigned int irqs;

	irqs = irq_pending() & irq_getmask();

	
  if (irqs & (1 << USB_INTERRUPT)) {
    tud_int_handler(0);
  }
  
  if (irqs & (1 << TIMER0_INTERRUPT)) {
    system_ticks++;
    timer0_ev_pending_write(1);
  }

   if (irqs & (1 << TIMER1_INTERRUPT)) {
    timer0_ev_pending_write(1);
  }

  if (irqs & (1 << PPU_INTERRUPT)) {
    ppu_ev_pending_write(1);
    flag = 1;
  }

}

void led_blinking_task(void);

int main(int i, char **c)
{	
  console_set_write_hook((console_write_hook)cdc_write_hook);
  leds_out_write(1);

  irq_setmask(0);
  irq_setie(1);
  
  timer_init();
  tusb_init();

  leds_out_write(2);

  gui_init();
  leds_out_write(4);
  ppu_start();

  leds_out_write(0xF);

	while(1){
    tud_task(); // tinyusb device task
    cdc_task();
    led_blinking_task();

    if(flag){
      flag = 0;
       gui_render();
    }

    int b_val = button_raw_read();
    if(b_val & BUTTON_A_HOLD){
      reboot_ctrl_write(0xac);
    }
	}


	
	return 0;
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

//--------------------------------------------------------------------+
// Device callbacks
//--------------------------------------------------------------------+

// Invoked when device is mounted
void tud_mount_cb(void)
{
  blink_interval_ms = BLINK_MOUNTED;
}

// Invoked when device is unmounted
void tud_umount_cb(void)
{
  blink_interval_ms = BLINK_NOT_MOUNTED;
}

// Invoked when usb bus is suspended
// remote_wakeup_en : if host allow us  to perform remote wakeup
// Within 7ms, device must draw an average of current less than 2.5 mA from bus
void tud_suspend_cb(bool remote_wakeup_en)
{
  (void) remote_wakeup_en;
  blink_interval_ms = BLINK_SUSPENDED;
}

// Invoked when usb bus is resumed
void tud_resume_cb(void)
{
  blink_interval_ms = BLINK_MOUNTED;
}


//--------------------------------------------------------------------+
// BLINKING TASK
//--------------------------------------------------------------------+
void led_blinking_task(void)
{
  static uint32_t start_ms = 0;
  static bool led_state = false;

  // Blink every interval ms
  if ( board_millis() - start_ms < blink_interval_ms) return; // not enough time
  start_ms += blink_interval_ms;

  
  board_led_write(led_state);
  static count = 0;
  printf("count=%u\r\n", count++);
  led_state = 1 - led_state; // toggle

  static int welcome = 0;
  if(tud_cdc_connected()){
    if(!welcome){
      welcome = 1;
      

    printf("     ______    ___   __   __   _______ \n");
    printf("    |      |  |___| |  | |  | |   _   |\n");
    printf("    |  _    |  ___  |  |_|  | |  |_|  |\n");
    printf("    | | |   | |   | |       | |       |\n");
    printf("    | |_|   | |   | |       | |       |\n");
    printf("    |       | |   |  |     |  |   _   |\n");
    printf("    |______|  |___|   |___|   |__| |__|\n");


    printf("   - Digital Video Interface for Boson -\n");
    printf("\n (c) Copyright 2019-2021 GetLabs \n");
    printf(" fw built: "__DATE__ " " __TIME__ " \n\n");

    printf("   Firmware git sha1: "DIVA_GIT_SHA1"\n");
    printf("      Migen git sha1: "MIGEN_GIT_SHA1"\n");
    printf("      LiteX git sha1: "LITEX_GIT_SHA1"\n");


    printf("   Clock Frequency: %u.%02uMHz\n", (int)(CONFIG_CLOCK_FREQUENCY / 1e6), (int)(CONFIG_CLOCK_FREQUENCY/ 1e4) % 100);
    printf("   HypeRAM Frequency: %u.%02uMHz\n", (int)(2*CONFIG_CLOCK_FREQUENCY / 1e6), (int)(2*CONFIG_CLOCK_FREQUENCY/ 1e4) % 100);

	/* On power up we need these to be set to 0 so that 
	 * PRBS memtest still works */
	buffers_adr0_write(0x0);
	buffers_adr1_write(0x0);
	buffers_adr2_write(0x0);

hyperram_init();

	printf("\n");	

	prbs_memtest(HYPERRAM_BASE, HYPERRAM_SIZE);

    }
  }else{
    welcome = 0;
  }
}



void board_led_write(bool state)
{
	leds_out_write(state ? 1 : 0);
}
