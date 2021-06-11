#ifndef _PPU_H_
#define _PPU_H_

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>


#define PPU_PIXMODE_ARGB1555 0u
#define PPU_PIXMODE_PAL8     1u
#define PPU_PIXMODE_PAL4     2u
#define PPU_PIXMODE_PAL1     3u

#define COLOUR_RED 0x7c00u
#define COLOUR_GREEN 0x3e0u
#define COLOUR_BLUE 0x1fu


#define PPU_CPROC_SYNC  (0x0u << 28)
#define PPU_CPROC_CLIP  (0x1u << 28)
#define PPU_CPROC_FILL  (0x2u << 28)
#define PPU_CPROC_BLIT  (0x3u << 28)
#define PPU_CPROC_TILE  (0x5u << 28)
#define PPU_CPROC_ABLIT (0x6u << 28)
#define PPU_CPROC_ATILE (0x7u << 28)
#define PPU_CPROC_PUSH  (0xeu << 28)
#define PPU_CPROC_POPJ  (0xfu << 28)

#define PPU_CPROC_BRANCH_ALWAYS 0x0
#define PPU_CPROC_BRANCH_YLT    0x1
#define PPU_CPROC_BRANCH_YGE    0x2

#define PPU_FORMAT_ARGB1555 0
#define PPU_FORMAT_PAL8 1
#define PPU_FORMAT_PAL4 2
#define PPU_FORMAT_PAL1 3

#define PPU_SIZE_8    0
#define PPU_SIZE_16   1
#define PPU_SIZE_32   2
#define PPU_SIZE_64   3
#define PPU_SIZE_128  4
#define PPU_SIZE_256  5
#define PPU_SIZE_512  6
#define PPU_SIZE_1024 7

#define PPU_ABLIT_FULLSIZE 0
#define PPU_ABLIT_HALFSIZE 1

typedef uint32_t ppu_instr_t;

// ----------------------------------------------------------------------------
// Rendering instructions

static inline size_t cproc_sync(ppu_instr_t *prog)
{
	*prog++ = PPU_CPROC_SYNC;
	return 1;
}

static inline size_t cproc_clip(ppu_instr_t *prog, uint16_t x_start, uint16_t x_end) {
	*prog++ = PPU_CPROC_CLIP | (x_start & 0xfffu) | ((x_end & 0xfffu) << 12);
	return 1;
}

static inline size_t cproc_fill(ppu_instr_t *prog, uint8_t r, uint8_t g, uint8_t b) {
	*prog++ = PPU_CPROC_FILL | ((r & 0x1fu) << 10) | ((g & 0x1fu) << 5) | (b & 0x1fu);
	return 1;
}


static inline size_t cproc_blit(ppu_instr_t *prog, uint8_t size, uint32_t x, uint32_t y, uint32_t img) {
	*prog++ = PPU_CPROC_BLIT | (size << 24) | (y << 12) | x;
	*prog++ = img;
	return 2;
}

// ----------------------------------------------------------------------------
// Control flow instructions

// "Unresolved" branch/jump variants give you a pointer to the jump target
// vector, so you can fill in the target later. Usually the regular ones suffice

static inline size_t cproc_branch(ppu_instr_t *prog, const ppu_instr_t *target, uint32_t condition, uint16_t compval) {
	*prog++ = PPU_CPROC_PUSH;
	*prog++ = (uint32_t)target;
	*prog++ = PPU_CPROC_POPJ | ((condition & 0xfu) << 26) | (compval & 0xfffu);
	return 3;
}

static inline size_t cproc_branch_unresolved(ppu_instr_t *prog, uint32_t **vector_out, uint32_t condition, uint16_t compval) {
	*vector_out = (uint32_t*)(prog);
	return cproc_branch(prog, 0, condition, compval);
}

static inline size_t cproc_jump(ppu_instr_t *prog, const ppu_instr_t *target) {
	return cproc_branch(prog, target, PPU_CPROC_BRANCH_ALWAYS, 0);
}

static inline size_t cproc_jump_unresolved(ppu_instr_t *prog, uint32_t **vector_out) {
	return cproc_branch_unresolved(prog, vector_out, PPU_CPROC_BRANCH_ALWAYS, 0);
}

static inline size_t cproc_call_unresolved(ppu_instr_t *prog, uint32_t **vector_out) {
	*prog++ = PPU_CPROC_PUSH;
	uint32_t *return_vector = prog;
	*prog++ = 0; // dummy
	size_t jump_size = cproc_jump_unresolved(prog, vector_out);
	*return_vector = (uint32_t)(prog + jump_size);
	return 2 + jump_size;
}

static inline size_t cproc_call(ppu_instr_t *prog, const ppu_instr_t *target) {
	uint32_t *call_vector_loc;
	size_t ret = cproc_call_unresolved(prog, &call_vector_loc);
	*call_vector_loc = (uint32_t)target;
	return ret;
}

static inline size_t cproc_ret(ppu_instr_t *prog) {
	*prog++ = PPU_CPROC_POPJ;
	return 1;
}

#endif // _PPU_H_
