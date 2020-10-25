#include "include/terminal.h"
#include <generated/mem.h>

static uint8_t current_colour;

static uint8_t cursor_x = 0;
static uint8_t cursor_y = 0;

#define TERMINAL_WIDTH 100
#define TERMINAL_HEIGHT 50


static void terminal_write_xy(uint32_t x, uint32_t y, uint8_t c, uint8_t colour){
	volatile uint32_t* terminal_mem = (volatile uint32_t*) (TERMINAL_BASE);
    /* Check bounds */
    if((x < 100) && (y < 60)){
        terminal_mem += x*2 + y*100*2;
        *terminal_mem++ = c;
        *terminal_mem = colour;
	}
}

void terminal_write(uint8_t c){
	volatile uint32_t* vga = (volatile uint32_t*) (TERMINAL_BASE);
	if(c == '\r'){
		cursor_x = 0;
	}else if(c == '\n'){
		cursor_y += 1;
        if(cursor_y >= TERMINAL_HEIGHT){
            cursor_y = 0;
        }
	}else{
		if(cursor_x >= TERMINAL_WIDTH){
			cursor_x = 0;
			cursor_y += 1;
		}

        terminal_write_xy(cursor_x, cursor_y, c, current_colour);
		cursor_x += 1;
	}
}


void terminal_set_cursor(uint8_t x, uint8_t y){
    cursor_x = x;
    cursor_y = y;
}

void terminal_set_fg(colours_t fg){
    current_colour &= ~0x0F;
    current_colour |= (fg & 0xF);
}

void terminal_set_bg(colours_t bg){
    current_colour &= ~0xF0;
    current_colour |= ((bg & 0xF) << 4);
}

void terminal_clear(void){
    volatile uint32_t* vga = (volatile uint32_t*) (TERMINAL_BASE);
    for(int i = 0; i < 100*50; i++){
        vga[i*2+1] = current_colour;
        vga[i*2] = 0;
    }
}


void treminal_draw_box(uint8_t x, uint8_t y, uint8_t w, uint8_t h){
    for(int i = x+1; i < (x+w); i++){
        /* ═ : 205 in CP437 */
        terminal_write_xy(i, y,     205,current_colour);
        terminal_write_xy(i, y + h, 205,current_colour);
    }

    for(int i = y+1; i < (y+h); i++){
        /* ║ : 186 in CP437 */
        terminal_write_xy(x, i,     186,current_colour);
        terminal_write_xy(x + w, i, 186,current_colour);
    }

    /* Corners */
    terminal_write_xy(x,   y,   /* ╔ */ 201, current_colour);
    terminal_write_xy(x,   y+h, /* ╚ */ 202, current_colour);
    terminal_write_xy(x+w, y,   /* ╗ */ 187, current_colour);
    terminal_write_xy(x+w, y+h, /* ╝ */ 188, current_colour);
}

void treminal_box_add_hline(uint8_t x, uint8_t y, uint8_t w){
    for(int i = x+1; i < (x+w); i++){
        /* ═ : 205 in CP437 */
        terminal_write_xy(i, y,     205,current_colour);
    }

    /* Edges */
    terminal_write_xy(x,   y, /* ╠ */ 204, current_colour);
    terminal_write_xy(x+w, y, /* ╣ */ 185, current_colour);
}

void treminal_box_add_vline(uint8_t x, uint8_t y, uint8_t h){
    for(int i = y+1; i < (y+h); i++){
        /* ║ : 186 in CP437 */
        terminal_write_xy(x, i,     186,current_colour);
    }

    /* Edges */
    terminal_write_xy(x,   y, /* ╦ */ 203, current_colour);
    terminal_write_xy(x, y+h, /* ╩ */ 202, current_colour);
}