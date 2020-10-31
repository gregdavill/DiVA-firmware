#include <string.h>
#include "settings.h"

#include "crc.h"

#ifndef FIRMWARE_HASH
#define FIRMWARE_HASH 0
#endif

settings_t _settings;


const char* palette_value(const menu_item_t* p){
    switch(*(uint8_t*)p->pdata){
        case 0: return "White Hot";
        case 1: return "Black Hot";
        case 2: return "Rainbow";
        case 3: return "Rainbow High Contrast";
        case 4: return "Ironbow";
        case 5: return "Lava";
        case 6: return "Arctic";
        case 7: return "Glowbow";
        case 8: return "Graded Fire";
        case 9: return "Hottest";
        default: return "Invalid";
    }
}

const char* scaler_value(const menu_item_t* p){
    switch(*(uint8_t*)p->pdata){
        case 0: return "1:1";
        case 1: return "Fill";
        default: return "Invalid";
    }
}

const char* enabled_disabled_value(const menu_item_t* p){
    if(*(uint8_t*)p->pdata){
        return "Enabled";
    }
    return "Disabled";
}

const char* boolean_value(const menu_item_t* p){
    if(*(uint8_t*)p->pdata){
        return "true";
    }
    return "false";
}

void basic_integer(menu_item_t* p, event_t e){
    uint8_t* v = (uint8_t*)p->pdata;
    switch(e){
        case BUTTON_A_PRESS:
            if(*v < p->value_max){
                *v = *v + 1;
            } else {
                *v = p->value_min; /* Wrap around */ 
            }
            break;
        
        case BUTTON_B_PRESS:
            if(*v > p->value_min){
                *v = *v - 1;
            } else {
                *v = p->value_max; /* Wrap around */ 
            }
            break;
        default:
            break;
    }
}

void boson_set_lut(uint32_t lut);

void boson_palette_changed(const menu_item_t* p){
    uint8_t lut = *(uint8_t*)p->pdata;
    boson_set_lut(lut);
}


void _boson_scaler_change(const menu_item_t* p){
    uint8_t lut = *(uint8_t*)p->pdata;

    stop_dma();
    
    switch_mode(lut);
    
    msleep(50);
    start_dma();
}

void boson_averager_changed(const menu_item_t* p){
    uint8_t en = *(uint8_t*)p->pdata;
    boson_set_averager(en);
}

void boson_frame_info_overlay(const menu_item_t* p){

}

void boson_debug_info_overlay(const menu_item_t* p){

}

const menu_item_t mi_palette = {
    .name = "Colour Palette",
    .value = palette_value,
    .pdata = &_settings.pallete,
    .act = basic_integer,
    .on_change = boson_palette_changed,
    .value_min = 0,
    .value_max = 9,
};

const menu_item_t mi_scaler = {
    .name = "Scaler (Beta)",
    .value = scaler_value,
    .pdata = &_settings.scaler_enable,
    .act = basic_integer,
    .on_change= _boson_scaler_change,
    .value_min = 0,
    .value_max = 1,
};

const menu_item_t mi_averager = {
    .name = "Averager",
    .value = enabled_disabled_value,
    .pdata = &_settings.averager,
    .act = basic_integer,
    .on_change = boson_averager_changed,
    .value_min = 0,
    .value_max = 1,
};

const menu_item_t mi_frame_info_overlay = {
    .name = "Frame Info",
    .value = enabled_disabled_value,
    .pdata = &_settings.frame_info_overlay,
    .act = basic_integer,
    .on_change = boson_frame_info_overlay,
    .value_min = 0,
    .value_max = 1,
};

const menu_item_t mi_debug_info_overlay = {
    .name = "Debug Info",
    .value = enabled_disabled_value,
    .pdata = &_settings.debug_info_overlay,
    .act = basic_integer,
    .on_change = boson_debug_info_overlay,
    .value_min = 0,
    .value_max = 1,
};



const menu_item_t* setting_menu_items[5] = {
    &mi_palette,
    &mi_scaler,
    &mi_averager,
    &mi_frame_info_overlay,
    &mi_debug_info_overlay
};



const settings_t setting_defaults = {
    0
};

void init_settings(){
    /* Read settings from EEPROM */
    eeprom_init();


    settings_t loaded_settings;
    i2c_read(&loaded_settings, sizeof(settings_t));

    if(!validate(&loaded_settings)){
        load_defaults();
    }
}

void load_defaults(){
    memcpy(&_settings, &setting_defaults, sizeof(settings_t));

    //settings_save();
}

int validate(settings_t* s){
    if(s->firmware_hash != FIRMWARE_HASH){
        return 0;
    }

    if(s->settings_crc != crc16(s+8, sizeof(settings_t)-8)){
        return 0;
    }
}

void settings_save(){
    /* Commit setting to EEPROM */
    create_hashes();
    
}

void create_hashes(){
    _settings.firmware_hash = FIRMWARE_HASH;
    _settings.settings_crc = crc16(&_settings+8, sizeof(settings_t)-8);
}
