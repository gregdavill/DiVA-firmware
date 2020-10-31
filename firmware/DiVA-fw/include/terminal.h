
#include <stdint.h>

typedef enum {
    TERMINAL_BLACK,
    TERMINAL_BLUE,
    TERMINAL_GREEN,
    TERMINAL_CYAN,
    TERMINAL_RED,
    TERMINAL_TRANSPARENT, // Magenta used as see-thru colour.
    TERMINAL_BRAWN,
    TERMINAL_LIGHT_GREY,
    TERMINAL_DARK_GREY,
    TERMINAL_LIGHT_BLUE,
    TERMINAL_LIGHT_GREEN,
    TERMINAL_LIGHT_CYAN,
    TERMINAL_LIGHT_RED,
    TERMINAL_LIGHT_MAGENTA,
    TERMINAL_YELLOW,
    TERMINAL_WHITE,
} colours_t;


void terminal_write_xy(uint32_t x, uint32_t y, uint8_t c, uint8_t colour);
void terminal_write(uint8_t c);
void terminal_set_cursor(uint8_t x, uint8_t y);

void terminal_set_fg(colours_t fg);
void terminal_set_bg(colours_t bg);

void terminal_clear(void);

void terminal_fill(uint8_t x, uint8_t y, uint8_t w, uint8_t h);
void treminal_draw_box(uint8_t x, uint8_t y, uint8_t w, uint8_t h);
void treminal_box_add_hline(uint8_t x, uint8_t y, uint8_t w);
void treminal_box_add_vline(uint8_t x, uint8_t y, uint8_t h);
