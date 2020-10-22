#include <stdlib.h>
#include <iostream>
#include <fstream>
#include "SDL2/SDL.h"
#include "Vsim.h"
#include "verilated.h"
#include <verilated_vcd_c.h>

int main(int argc, char **argv)
{

    // Initialize Verilators variables
	Verilated::commandArgs(argc, argv);
    Verilated::traceEverOn(true);

	// Create an instance of our module under test
	Vsim *tb = new Vsim;


    const int width = 1057;
    const int height = 628;
    const int bpp = 3;

    static uint8_t pixels[width * height * bpp];

    int frames = 0;
    unsigned int lastTime = 0;
    unsigned int currentTime;

    // Set this to 0 to disable vsync
    unsigned int flags = 0;
    unsigned int m_tickcount = 1;

    VerilatedVcdC* m_trace = new VerilatedVcdC;
    tb->trace(m_trace, 99);
    m_trace->open("trace.vcd");

    bool exit = false;

    if(SDL_Init(SDL_INIT_VIDEO) != 0) {
        fprintf(stderr, "Could not init SDL: %s\n", SDL_GetError());
        return 1;
    }
    SDL_Window *screen = SDL_CreateWindow("verilator",
            SDL_WINDOWPOS_UNDEFINED,
            SDL_WINDOWPOS_UNDEFINED,
            width, height,
            0);
    if(!screen) {
        fprintf(stderr, "Could not create window\n");
        return 1;
    }
    SDL_Renderer *renderer = SDL_CreateRenderer(screen, -1, flags);
    if(!renderer) {
        fprintf(stderr, "Could not create renderer\n");
        return 1;
    }

    SDL_Texture* framebuffer = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_RGB24, SDL_TEXTUREACCESS_STREAMING, width, height);



    tb->rst = 1;
    tb->clk = 1;
    tb->eval();
    tb->clk = 0;
    tb->eval();
    
    tb->rst = 0;

    int frame = 4000;

    for (int i = 0; i < 10000; i++) {
        size_t ctr = 0;
        int old_vs = 0;
        // Render one frame
        while (true) {
            if(i == frame)
            m_tickcount++;
            // Inofficial cxxrtl hack that improves performance
            if(i == frame)
            m_trace->dump(10*m_tickcount-2);
            tb->clk = 1;
            tb->eval();

            if(i == frame)
            m_trace->dump(10*m_tickcount);
            tb->clk = 0;
            tb->eval();
            if(i == frame)
            m_trace->dump(10*m_tickcount+5);
            //if(i == frame)
            if(tb->sim__DOT__main_terminal_ce == 0){
                continue;
            }

            if (ctr < width * height * bpp) {
                pixels[ctr++] = (uint8_t) tb->video_blue;
                pixels[ctr++] = (uint8_t) tb->video_green;
                pixels[ctr++] = (uint8_t) tb->video_red;
            }

            // Break when vsync goes low again
            if (old_vs && !tb->video_vsync)
                break;
            old_vs = tb->video_vsync;
        }

        SDL_UpdateTexture(framebuffer, NULL, pixels, width * bpp);
        SDL_RenderCopy(renderer, framebuffer, NULL, NULL);
        SDL_RenderPresent(renderer);

        SDL_Event event;
        while (SDL_PollEvent(&event)) {
            std::cout << event.type << std::endl;
            if (event.type == SDL_KEYDOWN){
                if(event.key.keysym.sym == SDLK_q){
                    exit = true;
                    break;
                }
                if(event.key.keysym.sym == SDLK_LEFT)
                    tb->btn_a = true;
                if(event.key.keysym.sym == SDLK_RIGHT)
                    tb->btn_b = true;
            }
            if (event.type == SDL_KEYUP){
                if(event.key.keysym.sym == SDLK_LEFT)
                    tb->btn_a = false;
                if(event.key.keysym.sym == SDLK_RIGHT)
                    tb->btn_b = false;
            }
        }

        if(exit)
            break;
        //SDL_Delay(10);

        frames++;

        currentTime = SDL_GetTicks();
        float delta = currentTime - lastTime;
        if (delta >= 1000) {
            std::cout << "FPS: " << (frames / (delta / 1000.0f)) << std::endl;
            lastTime = currentTime;
            frames = 0;
        }
    }


    m_trace->flush();

    SDL_DestroyWindow(screen);
    SDL_Quit();
    return 0;
}
