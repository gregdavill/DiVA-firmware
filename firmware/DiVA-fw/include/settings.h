#ifndef SETTINGS_H__
#define SETTINGS_H__

#include <stdint.h>
#include <stdbool.h>
#include "terminal_menu.h"

typedef struct {
    uint16_t firmware_hash;
    uint16_t settings_crc;
    
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


const menu_item_t* setting_menu_items[4];


void init_settings(bool load_defaults);

const char* palette_value(const menu_item_t* p);
const char* scaler_value(const menu_item_t* p);
const char* enabled_disabled_value(const menu_item_t* p);
const char* boolean_value(const menu_item_t* p);
void basic_integer(menu_item_t* p, event_t e);

void boson_set_lut(uint32_t lut);

void boson_palette_changed(const menu_item_t* p);
void _boson_scaler_change(const menu_item_t* p);
void boson_averager_changed(const menu_item_t* p);

void boson_frame_info_overlay(const menu_item_t* p);
void boson_debug_info_overlay(const menu_item_t* p);
void init_settings(bool load_defaults);
int validate(settings_t* s);
void settings_save(void);
void create_hashes(void);



#endif
