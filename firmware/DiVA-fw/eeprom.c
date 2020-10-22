#include <generated/csr.h>

#include "i2c.h"

#if 0

static I2C i2c;
static int debug_enabled = 0;

void eeprom_init(void) {
    printf("hdmi_out0: Init I2C...");
    i2c.w_read = i2c_w_read;
    i2c.w_write = i2c_w_write;
    i2c.r_read = i2c_r_read;
    i2c_init(&i2c);
    printf("finished.\n");
}

void eeprom_print(void) {
    int eeprom_addr, e, extension_number = 0;
    unsigned char b;
    unsigned char sum = 0;

    i2c_start_cond(&i2c);
    b = i2c_write(&i2c, 0xa0);
    if (!b && debug_enabled)
        printf("hdmi_out0: NACK while writing slave address!\n");
    b = i2c_write(&i2c, 0x00);
    if (!b && debug_enabled)
        printf("hdmi_out0: NACK while writing eeprom address!\n");
    b = i2c_write(&i2c, 0x00);
    if (!b && debug_enabled)
        printf("hdmi_out0: NACK while writing eeprom address!\n");
    i2c_start_cond(&i2c);
    b = i2c_write(&i2c, 0xa1);
    if (!b && debug_enabled)
        printf("hdmi_out0: NACK while writing slave address (2)!\n");
    for (eeprom_addr = 0 ; eeprom_addr < 128 ; eeprom_addr++) {
        b = i2c_read(&i2c, eeprom_addr == 127 && extension_number == 0 ? 0 : 1);
        sum +=b;
        printf("%02X ", b);
        if(!((eeprom_addr+1) % 16))
            printf("\n");
        if(eeprom_addr == 126)
            extension_number = b;
        if(eeprom_addr == 127 && sum != 0)
        {
            printf("Checksum ERROR in EDID block 0\n");
            i2c_stop_cond(&i2c);
            return;
        }
    }
    i2c_stop_cond(&i2c);
}



void eeprom_write(void) {
    int eeprom_addr, e, extension_number = 0;
    unsigned char b;
    unsigned char sum = 0;

    i2c_start_cond(&i2c);
    b = i2c_write(&i2c, 0xa0);
    if (!b && debug_enabled)
        printf("hdmi_out0: NACK while writing slave address!\n");
    b = i2c_write(&i2c, 0x00);
    if (!b && debug_enabled)
        printf("hdmi_out0: NACK while writing eeprom address!\n");
    b = i2c_write(&i2c, 0x00);
    if (!b && debug_enabled)
        printf("hdmi_out0: NACK while writing eeprom address!\n");
    b = i2c_write(&i2c, 0xA5);
    if (!b && debug_enabled)
        printf("hdmi_out0: NACK while writing eeprom address!\n");
    i2c_stop_cond(&i2c);
}

#endif
