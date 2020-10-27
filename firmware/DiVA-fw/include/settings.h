#ifndef SETTINGS_H__
#define SETTINGS_H__

#include <stdint.h>

typedef struct {
    uint32_t firmware_hash;
    uint32_t settings_crc;
    
    uint8_t pallete;
    uint8_t scaler_en;

} settings_t;

#endif
