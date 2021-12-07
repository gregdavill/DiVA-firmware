#include <stdio.h>
#include <irq.h>
#include <uart.h>
#include <usb.h>
#include <time.h>
#include <dfu.h>
#include <rgb.h>
#include <spi.h>
#include <generated/csr.h>
#include <generated/mem.h>

// reboot function
__attribute__((noreturn)) static inline void warmboot_to_image(uint8_t image_index) {
	reboot_ctrl_write(0xac | (image_index & 3) << 0);
	while (1);
}


// ICE40UP5K bitstream images (with SB_MULTIBOOT header) are
// 104250 bytes.  The SPI flash has 4096-byte erase blocks.
// The smallest divisible boundary is 4096*26.
#define FBM_OFFSET ((void *)(SPIFLASH_BASE + 0x0000))

void isr(void)
{
    unsigned int irqs;

    irqs = irq_pending() & irq_getmask();

    if (irqs & (1 << USB_INTERRUPT))
        usb_isr();
    
}

static void riscv_reboot_to(const void *addr, uint32_t boot_config) {
    reboot_addr_write((uint32_t)addr);

    // If requested, just let USB be idle.  Otherwise, reset it.
    if (boot_config & 0x00000020) // NO_USB_RESET
        usb_idle();
    else
        usb_disconnect();

#if defined(CSR_PICORVSPI_BASE)
    // Figure out what mode to put SPI flash into.
    if (boot_config & 0x00000001) { // QPI_EN
        // spiEnableQuad();
        picorvspi_cfg3_write(picorvspi_cfg3_read() | 0x20);
    }
    if (boot_config & 0x00000002) // DDR_EN
        picorvspi_cfg3_write(picorvspi_cfg3_read() | 0x40);
    if (boot_config & 0x00000002) // CFM_EN
        picorvspi_cfg3_write(picorvspi_cfg3_read() | 0x10);
#endif
    rgb_mode_error();

    // Vexriscv requires three extra nop cycles to flush the cache.
    if (boot_config & 0x00000010) { // FLUSH_CACHE
        asm("fence.i");
        asm("nop");
        asm("nop");
        asm("nop");
    }

    // Reset the Return Address, zero out some registers, and return.
    asm volatile(
        "mv ra,%0\n\t"    /* x1  */
        "mv sp,zero\n\t"  /* x2  */
        "mv gp,zero\n\t"  /* x3  */
        "mv tp,zero\n\t"  /* x4  */
        "mv t0,zero\n\t"  /* x5  */
        "mv t1,zero\n\t"  /* x6  */
        "mv t2,zero\n\t"  /* x7  */
        "mv x8,zero\n\t"  /* x8  */
        "mv s1,zero\n\t"  /* x9  */
        "mv a0,zero\n\t"  /* x10 */
        "mv a1,zero\n\t"  /* x11 */

        // /* Flush the caches */
        // ".word 0x400f\n\t"
        // "nop\n\t"
        // "nop\n\t"
        // "nop\n\t"

        "ret\n\t"

        :
        : "r"(addr)
    );
}


#if defined(CONFIG_FOMU_REV)
/// Tell whether the user is doing a "nerve pinch" to bypass
/// one of the subsequent boot modes.
static int nerve_pinch(void) {
    unsigned int i;

#ifdef CSR_TOUCH_BASE
    // Set pin 2 as output, and pin 0 as input, and see if it loops back.
    touch_oe_write((1 << 2) | (0 << 0));

    // Write a sequence of 10 bits out TOUCH2, and check their value
    // on TOUCH0.  If it doesn't match, then the user isn't doing
    // the nerve pinch.
    for (i = 0; i < 10; i++) {
        touch_o_write((i&1) << 2);
        if (!((i&1) == (touch_i_read() & (1 << 0))))
            return 0;
    }
    return 1;
#else
    return 1;
#endif
}
#endif

static int button_pressed(void){
#ifdef CSR_BUTTON_BASE
    return button_i_read() != 1;
#else
    return 1;
#endif
}

/// If the updater exists and has a valid header, then jump
/// to the updater.
__attribute__((used))
uint32_t update_ignore_reason;
__attribute__((used))
uint32_t update_ignore_val1;
__attribute__((used))
uint32_t update_ignore_val2;
void maybe_boot_updater(void) {
    extern uint32_t spi_id;
    uint32_t corrected_spi_id = spi_id;

    // These two PVT SPI IDs are functionally identical,
    // so convert one to the other.
    // The canonical ID is 0xc2152815.
    if (spi_id == 0xc8144015)
        corrected_spi_id = 0xc2152815;

    uint32_t booster_base = SPIFLASH_BASE + 0x5a000;
    if (csr_read_simple(booster_base + 4) != 0xfaa999b1) {
        update_ignore_reason = 1;
        update_ignore_val1 = csr_read_simple(booster_base + 4);
        update_ignore_val2 = 0xfaa999b1;
        return;
    }
    if (csr_read_simple(booster_base + 28) != corrected_spi_id) {
        update_ignore_reason = 2;
        update_ignore_val1 = csr_read_simple(booster_base + 28);
        update_ignore_val2 = corrected_spi_id;
        return;
    }
    uint32_t booster_size = csr_read_simple(booster_base + 8);
    uint32_t target_sum = csr_read_simple(booster_base + 12);
    uint32_t computed_sum = 0;
    uint32_t booster_offset;
    for (booster_offset = 0x20; booster_offset < booster_size; booster_offset++) {
        computed_sum += *((uint8_t *)(booster_offset + booster_base));
    }
    if (target_sum != computed_sum) {
        update_ignore_reason = 3;
        update_ignore_val1 = target_sum;
        update_ignore_val2 = computed_sum;
        return;
    }

    riscv_reboot_to((const void *)booster_base, 0x20);
}

#if defined(CONFIG_FOMU_REV)
/// If Foboot_Main exists on SPI flash, and if the bypass isn't active,
/// jump to FBM.
static void maybe_boot_fbm(void) {
    unsigned int i;
    // We've determined that we won't force entry into FBR.  Check to see
    // if the FBM signature exists on flash.
    uint32_t *fbr_addr = FBM_OFFSET;
    for (i = 0; i < 64; i++) {
        if (fbr_addr[i] == 0x032bd37d)
            riscv_reboot_to(FBM_OFFSET, 0);
    }
}

#endif

void reboot(void) {
    irq_setie(0);
    irq_setmask(0);

    uint32_t reboot_addr = dfu_origin_addr();
    uint32_t boot_config = 0;

    // Free the SPI controller, which returns it to memory-mapped mode.
    spiFree();

    // Scan for configuration data.
    int i;
    int riscv_boot = 0;
#if defined(CONFIG_FOMU_REV)
    uint32_t *destination_array = (uint32_t *)reboot_addr;
    for (i = 0; i < 32; i++) {
        // Look for FPGA sync pulse.
        if ((destination_array[i] == CONFIG_BITSTREAM_SYNC_HEADER1)
         || (destination_array[i] == CONFIG_BITSTREAM_SYNC_HEADER2)) {
            riscv_boot = 0;
            break;
        }
        // Look for "boot config" word
        else if (destination_array[i] == 0xb469075a) {
            boot_config = destination_array[i + 1];
        }
    }
#elif defined(CONFIG_ORANGECRAB_REV_R0_1) | defined(CONFIG_ORANGECRAB_REV_R0_2) | defined(CONFIG_BOOT_RISCV)
    char *destination_array = (char *)reboot_addr;
    // We want to support murtiple parts, 
    // so we just check the start of the bitstream header.
    const char magic[]="\xFF\x00";
    if((destination_array[0] == magic[0]) && (destination_array[1] == magic[1])) {
        riscv_boot = 0; // FLASH appears to be an ECP5 bitstream
    }else {
        riscv_boot = 1; // Assume it's RISCV code, and jump to it.
    }
#endif

    //if (riscv_boot) {
   // //    riscv_reboot_to((void *)reboot_addr, boot_config);
    //}
    //else {
        // Issue a reboot
        while(1){
            // For some reason writing to this register can fail if followed by an empty while loop
            reboot_ctrl_write(0xac); 
        }
   // }
    __builtin_unreachable();
}

static void init(void)
{
#ifdef FLASH_BOOT_ADDRESS
    spiInit();
    spiFree();
    riscv_reboot_to((void *)FLASH_BOOT_ADDRESS, 0);
#endif

    rgb_init();
    usb_init();
#if defined(CSR_PICORVSPI_BASE)
    picorvspi_cfg4_write(0x80);
#endif
    spiInit();

#if defined(CONFIG_ORANGECRAB_REV_R0_1) | defined(CONFIG_QSPI_ENABLE)
    // Check for QE bit set. If not set, enable it.
    spiSetQE();
#endif

#if defined(CONFIG_FOMU_REV)
    if (!nerve_pinch()) {
        lxspi_bitbang_en_write(0);
        maybe_boot_updater();
        maybe_boot_fbm();
        lxspi_bitbang_en_write(1);
    }
#elif defined(CSR_BUTTON_BASE)
    if(!button_pressed()){
        spiFree();
        reboot();
    }
#endif

#ifdef CSR_UART_BASE
    init_printf(NULL, rv_putchar);
#endif
    irq_setmask(0);
    irq_setie(1);

    time_init();
    dfu_init();
}

int main(int argc, char **argv)
{
    (void)argc;
    (void)argv;

    init();


    usb_connect();
    
    while (1)
    {
        usb_poll();
        dfu_poll();
    }
    return 0;
}
