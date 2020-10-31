#ifndef SETTINGS_H__
#define SETTINGS_H__

#include <stdint.h>
#include "terminal_menu.h"

typedef struct {
    uint32_t firmware_hash;
    uint32_t settings_crc;
    
    uint8_t pallete;
    uint8_t averager;
    uint8_t frame_info;
    uint8_t debug_info_overlay;
    uint8_t frame_info_overlay;
    
    uint8_t scaler_enable;

} settings_t;

settings_t _settings;


typedef struct menu_item menu_item_t;

typedef struct menu_item {
    const char* name;
    const char* (*value)(const menu_item_t*);
    void (*act)(menu_item_t*, event_t);
    void (*on_change)(menu_item_t*);
    void* pdata;
    int value_min;
    int value_max;
} menu_item_t;


const menu_item_t* setting_menu_items[5];



void load_defaults(void);



#endif
