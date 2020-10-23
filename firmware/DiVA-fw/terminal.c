#include "include/terminal.h"
#include <generated/mem.h>

static uint8_t colour;

static uint8_t cursor_x = 0;
static uint8_t cursor_y = 0;

#define TERMINAL_WIDTH 100
#define TERMINAL_HEIGHT 50


void terminal_write(uint8_t c){
	volatile uint32_t* vga = (volatile uint32_t*) (TERMINAL_BASE);
	if(c == '\r'){
		cursor_x = 0;
	}else if(c == '\n'){
		cursor_y += 1;
	}else{
		if(cursor_x >= 99){
			cursor_x = 0;
			cursor_y += 1;
		}

		vga[cursor_x*2 + cursor_y*100*2] = c; 
		vga[cursor_x*2 + cursor_y*100*2 + 1] = colour; 
		cursor_x += 1;
	}
}


void terminal_set_cursor(uint8_t x, uint8_t y){
    cursor_x = x;
    cursor_y = y;
}

void terminal_set_fg(colours_t fg){
    colour &= ~0x0F;
    colour |= (fg & 0xF);
}

void terminal_set_bg(colours_t bg){
    colour &= ~0xF0;
    colour |= ((bg & 0xF) << 4);
}

void terminal_clear(void){
    volatile uint32_t* vga = (volatile uint32_t*) (TERMINAL_BASE);
    for(int i = 0; i < 100*50; i++){
        vga[i*2+1] = colour;
        vga[i*2] = 0;
    }
}