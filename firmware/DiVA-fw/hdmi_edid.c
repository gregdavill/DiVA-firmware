#include <generated/csr.h>

//#include "i2c.h"

#if 0

I2C hdmi_out0_i2c;
int hdmi_out0_debug_enabled = 0;

void hdmi_out0_i2c_init(void) {
    printf("hdmi_out0: Init I2C...");
    hdmi_out0_i2c.w_read = hdmi_i2c_w_read;
    hdmi_out0_i2c.w_write = hdmi_i2c_w_write;
    hdmi_out0_i2c.r_read = hdmi_i2c_r_read;
    i2c_init(&hdmi_out0_i2c);
    printf("finished.\n");
}

void hdmi_out0_print_edid(void) {
    int eeprom_addr, e, extension_number = 0;
    unsigned char b;
    unsigned char sum = 0;

    i2c_start_cond(&hdmi_out0_i2c);
    b = i2c_write(&hdmi_out0_i2c, 0xa0);
    if (!b && hdmi_out0_debug_enabled)
        printf("hdmi_out0: NACK while writing slave address!\n");
    b = i2c_write(&hdmi_out0_i2c, 0x00);
    if (!b && hdmi_out0_debug_enabled)
        printf("hdmi_out0: NACK while writing eeprom address!\n");
    i2c_start_cond(&hdmi_out0_i2c);
    b = i2c_write(&hdmi_out0_i2c, 0xa1);
    if (!b && hdmi_out0_debug_enabled)
        printf("hdmi_out0: NACK while writing slave address (2)!\n");
    for (eeprom_addr = 0 ; eeprom_addr < 128 ; eeprom_addr++) {
        b = i2c_read(&hdmi_out0_i2c, eeprom_addr == 127 && extension_number == 0 ? 0 : 1);
        sum +=b;
        printf("%02X ", b);
        if(!((eeprom_addr+1) % 16))
            printf("\n");
        if(eeprom_addr == 126)
            extension_number = b;
        if(eeprom_addr == 127 && sum != 0)
        {
            printf("Checksum ERROR in EDID block 0\n");
            i2c_stop_cond(&hdmi_out0_i2c);
            return;
        }
    }
    for(e = 0; e < extension_number; e++)
    {
        printf("\n");
        sum = 0;
        for (eeprom_addr = 0 ; eeprom_addr < 128 ; eeprom_addr++) {
            b = i2c_read(&hdmi_out0_i2c, eeprom_addr == 127 && e == extension_number - 1 ? 0 : 1);
            sum += b;
            printf("%02X ", b);
            if(!((eeprom_addr+1) % 16))
                printf("\n");
            if(eeprom_addr == 127 && sum != 0)
            {
                printf("Checksum ERROR in EDID extension block %d\n", e);
                i2c_stop_cond(&hdmi_out0_i2c);
                return;
            }
        }
    }
    i2c_stop_cond(&hdmi_out0_i2c);
}

#endif
