#include <string.h>
#include "settings.h"

#include "crc.h"

#ifndef FIRMWARE_HASH
#define FIRMWARE_HASH 0
#endif

settings_t _settings;

const settings_t setting_defaults = {
    
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


    settings_save();
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
