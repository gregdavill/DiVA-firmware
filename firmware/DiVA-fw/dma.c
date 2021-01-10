#include <dma.h>
#include <generated/csr.h>

void start_dma(void){
	reader_reset_write(1);
	
	reader_transfer_size_write(640*512);
	reader_burst_size_write(128);
	reader_enable_write(1);
}

void stop_dma(void){
	reader_reset_write(1);
}