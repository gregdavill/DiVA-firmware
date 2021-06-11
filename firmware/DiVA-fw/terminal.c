#include "include/terminal.h"
#include <generated/mem.h>

static uint8_t current_colour;

static uint8_t cursor_x = 0;
static uint8_t cursor_y = 0;

#define TERMINAL_WIDTH 100
#define TERMINAL_HEIGHT 50


void terminal_write_xy(uint32_t x, uint32_t y, uint8_t c, uint8_t colour){
	
    
}

void terminal_write(uint8_t c){
	
}


void terminal_set_cursor(uint8_t x, uint8_t y){
}

void terminal_set_fg(colours_t fg){
}

void terminal_set_bg(colours_t bg){
}

void terminal_clear(void){
    
}

void terminal_fill(uint8_t x, uint8_t y, uint8_t w, uint8_t h){

}

void treminal_draw_box(uint8_t x, uint8_t y, uint8_t w, uint8_t h){
   
}
