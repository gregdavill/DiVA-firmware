#include <stdint.h>
#include "terminal.h"
#include "terminal_menu.h"
#include "settings.h"


typedef void (*on_exit_t)(void);
typedef void (*on_entry_t)(void);
typedef void (*act_t)(event_t);

typedef struct {
    on_entry_t on_entry;
    on_exit_t on_exit;
    act_t act;
} menu_t;


void settings_act(event_t e);
void settings_on_entry();
void settings_on_exit();

void settings_change_act(event_t e);
void settings_change_on_entry();
void settings_change_on_exit();

void null_act(event_t e);
void null_on_entry();
void null_on_exit();

const menu_t menu_settings = {
    .on_entry = settings_on_entry,
    .on_exit = settings_on_exit,
    .act = settings_act
};

const menu_t menu_settings_change = {
    .on_entry = settings_change_on_entry,
    .on_exit = settings_change_on_exit,
    .act = settings_change_act
};

const menu_t null_menu = {
    .on_entry = null_on_entry,
    .on_exit = null_on_exit,
    .act = null_act
};

menu_t* current_menu = &null_menu;

void menu_act(event_t e){
    menu_t* _old = current_menu;
    current_menu->act(e);

    /* Handle switching states */
    if(current_menu != _old){
        _old->on_exit();
        current_menu->on_entry();
    }
}

void highlight_colours(){
   	terminal_set_fg(TERMINAL_BLUE);
    terminal_set_bg(TERMINAL_WHITE);
}

void standard_colours(){
    terminal_set_fg(TERMINAL_WHITE);
   	terminal_set_bg(TERMINAL_BLUE);
}





static int selected_index = 0;
const int index_total = sizeof(setting_menu_items)/sizeof(menu_item_t*);

void draw_menu_item(int idx){
    terminal_set_cursor(19, 21+idx);
    printf("%s [ %s ]", setting_menu_items[idx]->name, setting_menu_items[idx]->value(setting_menu_items[idx]));
}

void draw_menu_item_highlight(int idx){
    terminal_set_cursor(19, 21+idx);
    standard_colours();
    printf("%s [", setting_menu_items[idx]->name);
    highlight_colours();
    printf(" %s ", setting_menu_items[idx]->value(setting_menu_items[idx]));
    standard_colours();
    printf("]");
}

void fill_row(uint32_t idx){
    terminal_set_cursor(17, 21+idx);

    for(int i = 0; i < 67; i++){
        terminal_write(' ');
    }    
}

void settings_act(event_t e){

    const uint32_t width = 70;
	const uint32_t height = 10;
	const uint32_t window_x = (100 - width) / 2;
	const uint32_t window_y = 20;

    switch(e){
        case BUTTON_A_HOLD:
            current_menu = &menu_settings_change;
        break;
        case BUTTON_A_PRESS:
                
                if(selected_index > 0){
                    standard_colours();
                    fill_row(selected_index);
                    draw_menu_item(selected_index);
 
                    selected_index--;
                    highlight_colours();
                    fill_row(selected_index);
                    draw_menu_item(selected_index);
                }
        break;
        case BUTTON_B_HOLD:
            current_menu = &null_menu;
        break;
        case BUTTON_B_PRESS:
            
            if(selected_index < (index_total-1)){
                standard_colours();
                fill_row(selected_index);
                draw_menu_item(selected_index);

                selected_index++;
                highlight_colours();
                fill_row(selected_index);
                draw_menu_item(selected_index);
            }
        break;
    }
}

void settings_on_entry(){
    /* Draw the main settings window */
    const uint32_t width = 70;
	const uint32_t height = 10;
	const uint32_t window_x = (100 - width) / 2;
	const uint32_t window_y = 20;
	
				
	terminal_set_bg(TERMINAL_BLUE);
	terminal_set_fg(TERMINAL_WHITE);

	treminal_draw_box(window_x, window_y, width, height);
	terminal_set_cursor(window_x + 1, window_y);
	printf("Settings");
	
	
	terminal_set_fg(TERMINAL_BLUE);
	terminal_set_bg(TERMINAL_WHITE);
    if((selected_index < 0) || (selected_index > (index_total-1))){
        selected_index = 0;
    }

    //printf("LUT [%s]%.*s", palette[0], width - 10 - strlen(palette[0]), padding);
    for(int idx = 0; idx < index_total; idx++){
        standard_colours();
        if(idx == selected_index){
            highlight_colours();
            fill_row(idx);
        }
        draw_menu_item(idx);
    }

}

void settings_on_exit(){

}




void settings_change_act(event_t e){

    

    switch(e){
        case BUTTON_B_HOLD:
            current_menu = &menu_settings;
        break;
        default:
            break;
    }

    setting_menu_items[selected_index]->act(setting_menu_items[selected_index], e);    

    standard_colours();
    fill_row(selected_index);
    draw_menu_item_highlight(selected_index);

    if(setting_menu_items[selected_index]->on_change){
        setting_menu_items[selected_index]->on_change(setting_menu_items[selected_index]);
    }
}

void settings_change_on_entry(){
    standard_colours();
    fill_row(selected_index);
    draw_menu_item_highlight(selected_index);
}

void settings_change_on_exit(){

}





void null_act(event_t e){
    switch(e){
        case BUTTON_A_HOLD:
            current_menu = &menu_settings;
        break;
        case BUTTON_A_PRESS:
        break;
        case BUTTON_B_HOLD:
        break;
        case BUTTON_B_PRESS:
        break;
    }
}

void null_on_entry(){
    /* Clear screen */
    const uint32_t width = 70;
	const uint32_t height = 10;
	const uint32_t window_x = (100 - width) / 2;
	const uint32_t window_y = 20;

    terminal_set_fg(TERMINAL_TRANSPARENT);
    terminal_set_bg(TERMINAL_TRANSPARENT);
    terminal_fill(window_x, window_y, width+1, height+1);
}

void null_on_exit(){
}