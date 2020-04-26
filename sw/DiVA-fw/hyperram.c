#include <stdio.h>
#include <stdlib.h>
#include <console.h>
#include <string.h>
#include <uart.h>
#include <system.h>
#include <id.h>
#include <irq.h>
#include <crc.h>
#include <stdint.h>
#include <stdbool.h>

#include <generated/csr.h>
#include <generated/mem.h>
#include <generated/git.h>

/* 
	Test memory location by writing a value and attempting read-back.
	Try twice to avoid situation where memory is read-only and set from a previous test.
*/
static int basic_memtest(volatile uint32_t* addr){

	*(addr) = 0xDEADBEEF;
	if(*(addr) != 0xDEADBEEF)
		return 0;

	*(addr) = 0xABABCDCD;
	if(*(addr) != 0xABABCDCD)
		return 0;

	return 1;
}


void hyperram_init(){

	printf("HyperRAM PLL Tuning\n");

	int window = 0;
	int i = 0;
	for(i = 0; i < 1024; i++){
		int pass = basic_memtest(HYPERRAM_BASE);

		// Shift our PLL up
		crg_phase_sel_write(0);
		crg_phase_dir_write(1);
		crg_phase_step_write(0);
		crg_phase_step_write(1);

	    printf("%c", pass + '0');

		if(pass == 1){
			window++;
		}
		else if(pass != 1){
			if(window > 8){
				break;
			}else {
				window = 0;
			}
		}

	}
	printf("Window: %u, steps:%u\n", window, i);

	for(i = 0; i < window/2; i++){
		// Shift our PLL up
		crg_phase_sel_write(0);
		crg_phase_dir_write(0);
		crg_phase_step_write(0);
		crg_phase_step_write(1);
	}

	printf("HyperRAM PLL Tuning: Done\n");
}




static unsigned int seed_to_data_32(unsigned int seed, int random)
{
	if (random)
		return 1664525*seed + 1013904223;
	else
		return seed + 1;
}

static unsigned short seed_to_data_16(unsigned short seed, int random)
{
	if (random)
		return 25173*seed + 13849;
	else
		return seed + 1;
}

#define ONEZERO 0xAAAAAAAA
#define ZEROONE 0x55555555

#ifndef MEMTEST_BUS_SIZE
#define MEMTEST_BUS_SIZE (512)
#endif

//#define MEMTEST_BUS_DEBUG

static int memtest_bus(volatile unsigned int *array)
{
	int i, errors;
	unsigned int rdata;

	errors = 0;

	for(i=0;i<MEMTEST_BUS_SIZE/4;i++) {
		array[i] = ONEZERO;
	}
	flush_cpu_dcache();
#ifdef CONFIG_L2_SIZE
	flush_l2_cache();
#endif
	for(i=0;i<MEMTEST_BUS_SIZE/4;i++) {
		rdata = array[i];
		if(rdata != ONEZERO) {
			errors++;
#ifdef MEMTEST_BUS_DEBUG
			printf("[bus: 0x%0x]: 0x%08x vs 0x%08x\n", i, rdata, ONEZERO);
#endif
		}
	}

	for(i=0;i<MEMTEST_BUS_SIZE/4;i++) {
		array[i] = ZEROONE;
	}
	flush_cpu_dcache();
#ifdef CONFIG_L2_SIZE
	flush_l2_cache();
#endif
	for(i=0;i<MEMTEST_BUS_SIZE/4;i++) {
		rdata = array[i];
		if(rdata != ZEROONE) {
			errors++;
#ifdef MEMTEST_BUS_DEBUG
			printf("[bus 0x%0x]: 0x%08x vs 0x%08x\n", i, rdata, ZEROONE);
#endif
		}
	}

	return errors;
}

#ifdef HYPERRAM_SIZE
#define MEMTEST_DATA_SIZE HYPERRAM_SIZE
#else
#define MEMTEST_DATA_SIZE (1024*8)
#endif

#ifndef MEMTEST_DATA_SIZE
#define MEMTEST_DATA_SIZE (2*1024*1024)
#endif
#define MEMTEST_DATA_RANDOM 1

//#define MEMTEST_DATA_DEBUG

static int memtest_data(volatile unsigned int *array)
{
	int i, errors;
	unsigned int seed_32;
	unsigned int rdata;

	errors = 0;
	seed_32 = 0;

	for(i=0;i<MEMTEST_DATA_SIZE/4;i++) {
		seed_32 = seed_to_data_32(seed_32, MEMTEST_DATA_RANDOM);
		array[i] = seed_32;
	}

	seed_32 = 0;
	flush_cpu_dcache();
#ifdef CONFIG_L2_SIZE
	flush_l2_cache();
#endif
	for(i=0;i<MEMTEST_DATA_SIZE/4;i++) {
		seed_32 = seed_to_data_32(seed_32, MEMTEST_DATA_RANDOM);
		rdata = array[i];
		if(rdata != seed_32) {
			errors++;
#ifdef MEMTEST_DATA_DEBUG
			printf("[data 0x%0x]: 0x%08x vs 0x%08x\n", i, rdata, seed_32);
#endif
		}
	}

	return errors;
}
#ifndef MEMTEST_ADDR_SIZE
#define MEMTEST_ADDR_SIZE (32*1024)
#endif
#define MEMTEST_ADDR_RANDOM 0

//#define MEMTEST_ADDR_DEBUG

static int memtest_addr(volatile unsigned int *array)
{
	int i, errors;
	unsigned short seed_16;
	unsigned short rdata;

	errors = 0;
	seed_16 = 0;

	for(i=0;i<MEMTEST_ADDR_SIZE/4;i++) {
		seed_16 = seed_to_data_16(seed_16, MEMTEST_ADDR_RANDOM);
		array[(unsigned int) seed_16] = i;
	}

	seed_16 = 0;
	flush_cpu_dcache();
#ifdef CONFIG_L2_SIZE
	flush_l2_cache();
#endif
	for(i=0;i<MEMTEST_ADDR_SIZE/4;i++) {
		seed_16 = seed_to_data_16(seed_16, MEMTEST_ADDR_RANDOM);
		rdata = array[(unsigned int) seed_16];
		if(rdata != i) {
			errors++;
#ifdef MEMTEST_ADDR_DEBUG
			printf("[addr 0x%0x]: 0x%08x vs 0x%08x\n", i, rdata, i);
#endif
		}
	}

	return errors;
}

static void memspeed(volatile unsigned int *array)
{
	int i;
	unsigned int start, end;
	unsigned long write_speed;
	unsigned long read_speed;
	__attribute__((unused)) unsigned int data;

	/* init timer */
	timer0_en_write(0);
	timer0_reload_write(0);
	timer0_load_write(0xffffffff);
	timer0_en_write(1);

	/* write speed */
	timer0_update_value_write(1);
	start = timer0_value_read();
	for(i=0;i<MEMTEST_DATA_SIZE/4;i++) {
		array[i] = i;
	}
	timer0_update_value_write(1);
	end = timer0_value_read();
	write_speed = (8*MEMTEST_DATA_SIZE*(CONFIG_CLOCK_FREQUENCY/1000000))/(start - end);

	/* flush CPU and L2 caches */
	flush_cpu_dcache();
#ifdef CONFIG_L2_SIZE
	flush_l2_cache();
#endif

	/* read speed */
	timer0_en_write(1);
	timer0_update_value_write(1);
	start = timer0_value_read();
	for(i=0;i<MEMTEST_DATA_SIZE/4;i++) {
		data = array[i];
	}
	timer0_update_value_write(1);
	end = timer0_value_read();
	read_speed = (8*MEMTEST_DATA_SIZE*(CONFIG_CLOCK_FREQUENCY/1000000))/(start - end);

	printf("Memspeed Writes: %dMbps Reads: %dMbps\n", write_speed, read_speed);
}

int memtest(volatile unsigned int *array)
{
	int bus_errors, data_errors, addr_errors;

	bus_errors = memtest_bus(array);
	if(bus_errors != 0)
		printf("Memtest bus failed: %d/%d errors\n", bus_errors, 2*128);

	data_errors = memtest_data(array);
	if(data_errors != 0)
		printf("Memtest data failed: %d/%d errors\n", data_errors, MEMTEST_DATA_SIZE/4);

	addr_errors = memtest_addr(array);
	if(addr_errors != 0)
		printf("Memtest addr failed: %d/%d errors\n", addr_errors, MEMTEST_ADDR_SIZE/4);

	if(bus_errors + data_errors + addr_errors != 0)
		return 0;
	else {
		printf("Memtest OK\n");
		memspeed(array);
		return 1;
	}
}