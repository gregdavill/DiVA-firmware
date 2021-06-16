#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <generated/csr.h>

#include "spi.h"

enum pin {
	PIN_MOSI = 0,
	PIN_CLK = 1,
	PIN_CS = 2,
	PIN_MISO_EN = 3,
	PIN_MISO = 4, // Value is ignored
};

void spiBegin(void) {
	spiflash_bitbang_write((0 << PIN_CLK) | (0 << PIN_CS));
}

void spiEnd(void) {
	spiflash_bitbang_write((0 << PIN_CLK) | (1 << PIN_CS));
}

static void spi_single_tx(uint8_t out) {
	int bit;

	for (bit = 7; bit >= 0; bit--) {
		if (out & (1 << bit)) {
			spiflash_bitbang_write((0 << PIN_CLK) | (1 << PIN_MOSI));
			spiflash_bitbang_write((1 << PIN_CLK) | (1 << PIN_MOSI));
			spiflash_bitbang_write((0 << PIN_CLK) | (1 << PIN_MOSI));
		} else {
			spiflash_bitbang_write((0 << PIN_CLK) | (0 << PIN_MOSI));
			spiflash_bitbang_write((1 << PIN_CLK) | (0 << PIN_MOSI));
			spiflash_bitbang_write((0 << PIN_CLK) | (0 << PIN_MOSI));
		}
	}
}

static uint8_t spi_single_rx(void) {
	int bit = 0;
	uint8_t in = 0;

	spiflash_bitbang_write((1 << PIN_MISO_EN) | (0 << PIN_CLK));

	while (bit++ < 8) {
		spiflash_bitbang_write((1 << PIN_MISO_EN) | (1 << PIN_CLK));
		in = (in << 1) | spiflash_miso_read();
		spiflash_bitbang_write((1 << PIN_MISO_EN) | (0 << PIN_CLK));
	}

	return in;
}

static uint8_t spi_read_status(void) {
	uint8_t val;

	spiBegin();
	spi_single_tx(0x05);
	val = spi_single_rx();
	spiEnd();
	return val;
}

int spiIsBusy(void) {
  	return spi_read_status() & (1 << 0);
}

__attribute__((used))
uint32_t spiId(void) {
	uint32_t spi_id = 0;

	spiBegin();
	spi_single_tx(0x90);               // Read manufacturer ID
	spi_single_tx(0x00);               // Dummy byte 1
	spi_single_tx(0x00);               // Dummy byte 2
	spi_single_tx(0x00);               // Dummy byte 3
	spi_id = (spi_id << 8) | spi_single_rx();  // Manufacturer ID
	spi_id = (spi_id << 8) | spi_single_rx();  // Device ID
	spiEnd();

	spiBegin();
	spi_single_tx(0x9f);               // Read device id
	(void)spi_single_rx();             // Manufacturer ID (again)
	spi_id = (spi_id << 8) | spi_single_rx();  // Memory Type
	spi_id = (spi_id << 8) | spi_single_rx();  // Memory Size
	spiEnd();

	return spi_id;
}

uint8_t spiReset(void) {
	// Writing 0xff eight times is equivalent to exiting QPI mode,
	// or if CFM mode is enabled it will terminate CFM and return
	// to idle.
	unsigned int i;
	spiBegin();
	for (i = 0; i < 8; i++)
		spi_single_tx(0xff);
	spiEnd();

	// Some SPI parts require this to wake up
	spiBegin();
	spi_single_tx(0xab);    // Read electronic signature
	spiEnd();

	return 0;
}

int spiInit(void) {

	// Ensure CS is deasserted and the clock is high
	spiflash_bitbang_write((0 << PIN_CLK) | (1 << PIN_CS));

	// Disable memory-mapped mode and enable bit-bang mode
	spiflash_bitbang_en_write(1);

	// Reset the SPI flash, which will return it to SPI mode even
	// if it's in QPI mode, and ensure the chip is accepting commands.
	spiReset();

	spiId();

	return 0;
}


void spiSetQE(void){
	// Check for supported FLASH ID
	uint32_t id = spiId();

    if(id == 0x1f138501){
        // Set QE bit on AT25SF081 if not set
        
		// READ status register
        uint8_t status1 = spi_read_status();

		spiBegin();
		spi_single_tx(0x35);
		uint8_t status2 = spi_single_rx();
		spiEnd();
        
		// Check Quad Enable bit
        if((status2 & 0x02) == 0){
            // Enable Write-Enable Latch (WEL)
            spiBegin();
            spi_single_tx(0x06);
            spiEnd();

            // Write back status1 and status2 with QE bit set
            status2 |= 0x02;
            spiBegin();
            spi_single_tx(0x01);
            spi_single_tx(status1);
            spi_single_tx(status2);
            spiEnd();
            
            // loop while write in progress set
            while(spi_read_status() & 1) {}
        }
    }else{
		while(1);
	}
}

void spiFree(void) {
	// Re-enable memory-mapped mode
	spiflash_bitbang_en_write(0);
}
