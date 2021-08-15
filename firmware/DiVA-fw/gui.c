

#include <ppu.h>
#include <generated/csr.h>
#include <generated/mem.h>

#include <gui/font.h>

#include <base/stdarg.h>
#include <stdio.h>
#include <stdlib.h>

size_t text_sprintf(ppu_instr_t *prog, int x, int y, const char *fmt, ...);
size_t text(ppu_instr_t *prog, int x, int y, const char *s);
size_t text_char(ppu_instr_t *prog, int x, int y, char c);

static volatile uint32_t *array0 = (uint32_t *)0x40000000UL;
static volatile uint32_t *array1 = (uint32_t *)0x41000000UL;
static volatile uint32_t *buffer;

const int sin[] = {200, 219, 238, 258, 276, 294, 311, 326, 341, 354, 366, 376, 384, 391, 396, 399, 399, 399, 396, 391, 384, 376, 366, 354, 341, 327, 311, 294, 276, 258, 239, 219, 200, 180, 161, 142, 123, 106, 89, 73, 58, 45, 33, 23, 15, 8, 3, 1, 0, 0, 3, 8, 15, 23, 33, 45, 58, 72, 88, 105, 122, 141, 160, 179};

int counter = 0;

int val = 0;

int hold = 0;

int cnt0 = 0;

int frames = 0;
int sec = 0;
int min = 0;

int cycle_cnt = 0;

int x = 800 / 2;
int y = 600 / 2;

size_t square(ppu_instr_t *prog, int x0, int y0, int x1, int y1, int r, int g, int b)
{
	prog += cproc_branch(prog, 15 + (((uint32_t)prog) >> 2), PPU_CPROC_BRANCH_YLT, y0);		// 3
	prog += cproc_branch(prog, 12 + (((uint32_t)prog) >> 2), PPU_CPROC_BRANCH_YGE, y1 + 2); // 3
	prog += cproc_clip(prog, x0, x1);														// 1
	prog += cproc_branch(prog, 7 + (((uint32_t)prog) >> 2), PPU_CPROC_BRANCH_YLT, y1);		// 3
	prog += cproc_fill(prog, 0, 0, 0);														// 1
	prog += cproc_branch(prog, 4 + (((uint32_t)prog) >> 2), PPU_CPROC_BRANCH_ALWAYS, 0);	// 3
	prog += cproc_fill(prog, r, g, b);														// 1
	return 15;
}

size_t blit(ppu_instr_t *prog, int x, int y, int c)
{
	prog += cproc_blit(prog, PPU_SIZE_16, x, y, ((uint32_t)array0 >> 2) + (512 + (c * 16)));
	return 2;
}

size_t text_sprintf(ppu_instr_t *prog, int x, int y, const char *fmt, ...)
{
	char buf[128];
	va_list args;
	va_start(args, fmt);
	vsnprintf(buf, sizeof(buf), fmt, args);
	va_end(args);
	return text(prog, x, y, buf);
}

size_t textbox_sprintf(ppu_instr_t *prog, int x, int y, const char *fmt, ...)
{
	char buf[128];
	va_list args;
	ppu_instr_t* prog0 = prog;

	va_start(args, fmt);
	int len = vsnprintf(buf, sizeof(buf), fmt, args);
	va_end(args);

	prog += square(prog, x-2, y-2, x + 8*len + 3, y + 16 + 2, 255,255,255);
	prog += text(prog, x, y, buf);
	return prog - prog0;
}

size_t text(ppu_instr_t *prog, int x, int y, const char *s)
{
	size_t cnt = 0;
	int i = 0;
	while (*s)
	{
		if(*s > 32){
			cnt += blit(prog, x, y, *s - (33));
			prog += 2;
		}
		s++;
		x += 8;
	}

	/* Ugly hack, BLIT currently has a bug, this extra 'NOP' fixes it */
	*prog++ = (0x8u << 28);
	return cnt + 1;
}

uint32_t data[32] = {0};

void gui_init()
{

	buffer = array0;
	ppu_ppu_pc_write((uint32_t)buffer >> 2);

	array0[0] = 0;
	array1[0] = 0;

	for (int i = 0; i < 1504; i++)
	{
		array0[i + 512] = ~font[i];
	}


	writer_reset_write(1);
	writer_external_sync_write(1);
	writer_sink_mux_write(1);
	writer_burst_size_write(256);
	writer_transfer_size_write(640*512);
	writer_enable_write(1);

}

void gui_render()
{
	timer1_en_write(0);
	timer1_reload_write(0);
	timer1_load_write(-1);
	timer1_en_write(1);



	val = sin[counter] / 4;

	cnt0++;
	if (hold > 0)
	{
		hold--;
	}
	else
	{
		counter += 1;
		if (counter == 16)
		{
			hold = 100;
		}
		if (counter >= 64)
		{
			counter = 0;
		}
	}

	if (buffer == array1)
	{
		buffer = array0;
	}
	else
	{
		buffer = array1;
	}
	ppu_instr_t *ptr = (ppu_instr_t *)buffer;
	//ppu_instr_t* inital = (ppu_instr_t*)buffer;

	uint32_t *vector;

	/* Fill buffers with black */
	ptr += cproc_branch(ptr, ((uint32_t)ptr >> 2) + 5, 2, 2);
	ptr += cproc_clip(ptr, 0, 1280);
	ptr += cproc_fill(ptr, 0, 0, 0);

	/* Draw a square */
	ptr += square(ptr, 0, 10 + val, 10, 20 + val, 0, 32, 255);
	ptr += square(ptr, x - (val >> 4), y - (val >> 4), x + 5 + (val >> 4), y + 5 + (val >> 4), 128, 127, 0);

	ptr += textbox_sprintf(ptr, 150, 64 + 1*18, "Boson Digital Video Adapter");
	ptr += textbox_sprintf(ptr, 150, 64 + 2*18, "   -=-=-=- DiVA -=-=-=-    ");
	ptr += textbox_sprintf(ptr, 150, 64 + 3*18, "Resolution: 1280x720");
	//ptr += textbox_sprintf(ptr, 150, 64 + 4*18, "Setting0: True");
	//ptr += textbox_sprintf(ptr, 150, 64 + 5*18, "Setting1: False");
	


	//ptr += square(ptr, 17 + x, 16 + y, 98 + x, 41 + y, 255, 255, 255);
	ptr += textbox_sprintf(ptr, 22 + x, 20 + y, "%02u:%02u:%02u", min, sec, frames);

	//ptr += square(ptr, 10, 693, 76, 715, 255, 255, 255);
	ptr += textbox_sprintf(ptr, 15, 695, "%06u - %06u", cycle_cnt, ptr - buffer);

	if (++frames >= 60)
	{
		frames = 0;
		if (++sec >= 60)
		{
			sec = 0;
			if (++min >= 60)
			{
				min = 0;
			}
		}
	}

	x = 400 + sin[counter & 63] / 2;
	y = 200 + sin[(counter + 16) & 63] / 2;

	ptr += cproc_sync(ptr);

	timer1_update_value_write(1);
	cycle_cnt = -timer1_value_read() / (int)(CONFIG_CLOCK_FREQUENCY / 1e6);

	/* Swap buffers */
	ppu_ppu_pc_write((uint32_t)buffer >> 2);
}
