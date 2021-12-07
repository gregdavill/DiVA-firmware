#ifndef HYPERRAM_H__
#define HYPERRAM_H__
#include <stdint.h>

void hyperram_init(void);
void prbs_memtest(uint32_t base, uint32_t len);

#endif