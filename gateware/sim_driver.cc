#include <iostream>
#include <fstream>
#include "SDL2/SDL.h"

#include "sim.cc"

cxxrtl_design::p_sim top;

int main()
{
    const int width = 1057;
    const int height = 628;
    const int bpp = 3;

    static uint8_t pixels[width * height * bpp];

    int frames = 0;
    unsigned int lastTime = 0;
    unsigned int currentTime;

    // Set this to 0 to disable vsync
    unsigned int flags = 0;

    if(SDL_Init(SDL_INIT_VIDEO) != 0) {
        fprintf(stderr, "Could not init SDL: %s\n", SDL_GetError());
        return 1;
    }
    SDL_Window *screen = SDL_CreateWindow("cxxrtl",
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

    top.p_rst = value<1>{1u};

    top.p_clk = value<1>{1u};
	top.step();
	top.p_clk = value<1>{0u};
	top.step();
    
    top.p_rst = value<1>{0u};


    for (int i = 0; i < 50; i++) {
        size_t ctr = 0;
        value<1> old_vs{0u};
        // Render one frame
        while (true) {
            // Inofficial cxxrtl hack that improves performance
            top.prev_p_clk = value<1>{0u};
            top.p_clk = value<1>{1u};
            top.step();

            if (ctr < width * height * bpp) {
                pixels[ctr++] = (uint8_t) top.p_video__red.curr.data[0];
                pixels[ctr++] = (uint8_t) top.p_video__green.curr.data[0];
                pixels[ctr++] = (uint8_t) top.p_video__blue.curr.data[0];
            }

            // Break when vsync goes low again
            if (old_vs && !top.p_video__vsync.curr)
                break;
            old_vs = top.p_video__vsync.curr;
        }

        SDL_UpdateTexture(framebuffer, NULL, pixels, width * bpp);
        SDL_RenderCopy(renderer, framebuffer, NULL, NULL);
        SDL_RenderPresent(renderer);

        SDL_Event event;
        if (SDL_PollEvent(&event)) {
            if (event.type == SDL_KEYDOWN)
                break;
        }

        // SDL_Delay(10);

        frames++;

        currentTime = SDL_GetTicks();
        float delta = currentTime - lastTime;
        if (delta >= 1000) {
            std::cout << "FPS: " << (frames / (delta / 1000.0f)) << std::endl;
            lastTime = currentTime;
            frames = 0;
        }
    }


    SDL_DestroyWindow(screen);
    SDL_Quit();
    return 0;
}
