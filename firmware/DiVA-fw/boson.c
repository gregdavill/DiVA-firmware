#include "include/boson.h"

#include <generated/csr.h>

volatile static uint16_t boson_crc;

#define UART_EV_TX	0x1
#define UART_EV_RX	0x2

static uint8_t boson_uart_read(void)
{
	uint8_t c;
	while (boson_uart_rxempty_read());
	c = boson_uart_rxtx_read();
	boson_uart_ev_pending_write(UART_EV_RX);
	return c;
}

static int boson_uart_read_nonblock(void)
{
	return (boson_uart_rxempty_read() == 0);
}

static void boson_uart_write(uint8_t c)
{
    boson_crc = ByteCRC16((int)c, boson_crc);
	while (boson_uart_txfull_read());
	boson_uart_rxtx_write(c);
	boson_uart_ev_pending_write(UART_EV_TX);
}

static void boson_uart_write_escaped(uint8_t c)
{
    if ((c == START_FRAME_BYTE) || (c == END_FRAME_BYTE) || (c == ESCAPE_BYTE)){
        boson_uart_write(ESCAPE_BYTE);
        
        switch (c)
        {
            case END_FRAME_BYTE:
                c = ESCAPED_END_FRAME_BYTE;
                break;
            case START_FRAME_BYTE:
                c = ESCAPED_START_FRAME_BYTE;
                break;
            case ESCAPE_BYTE:
                c = ESCAPED_ESCAPE_BYTE;
                break;
            default:
                break;
        }
    }
    
    boson_uart_write(c);
}



static void boson_uart_init(void)
{
	boson_uart_ev_pending_write(boson_uart_ev_pending_read());
	boson_uart_ev_enable_write(UART_EV_TX | UART_EV_RX);
}

static void boson_uart_sync(void)
{
	while (boson_uart_txfull_read());
}


static void boson_uart_write_array(const uint8_t* array, uint32_t len){
    for(int i = 0; i < len; i++){
        boson_uart_write_escaped(array[i]);
    }
}

/* Similar to the FLIR SDK functions, but without buffering */
FLR_RESULT dispatcher_tx(uint32_t seqNum, FLR_FUNCTION fnID, const uint8_t *sendData, const uint32_t sendBytes) {
    
    uint8_t tmp_array[4];

    boson_uart_write(START_FRAME_BYTE);
    
    /* Reset CRC, START_FRAME_BYTE not included in calculation */
    boson_crc = FLIR_CRC_INITIAL_VALUE;
    boson_uart_write(0); /* Channel ID: Command Channel */
    
    /* Send Sequence number */
    UINT_32ToByte(seqNum, (const uint8_t *)tmp_array);
    boson_uart_write_array(tmp_array, 4);
    

    /* Send function ID */
    UINT_32ToByte((const uint32_t) fnID, (const uint8_t *)tmp_array);
    boson_uart_write_array(tmp_array, 4);
    
    /* Send 0xFFFFFFFF */
    UINT_32ToByte(0xFFFFFFFF, (const uint8_t *)tmp_array);
    boson_uart_write_array(tmp_array, 4);


    /* Send sendData */
    if(sendBytes > 0){
        boson_uart_write_array(sendData, sendBytes);
    }
    
    /* Send out the CRC */
    uint8_t crcbyte0 = ((boson_crc >> 8) & 0xFF);
    uint8_t crcbyte1 = (boson_crc & 0xFF);
    boson_uart_write_escaped(crcbyte0);
    boson_uart_write_escaped(crcbyte1);
    
    boson_uart_write(END_FRAME_BYTE);

    return R_SUCCESS;


}
// Asynchronous (MultiService compatible) receive part
FLR_RESULT dispatcher_rx(void) {

    /* Setup a timeout interval */
    int timeout = 500;
    int timeout_count = 0;

    uint8_t payload[128];
    uint8_t max_len = 128;
    
    uint16_t len = 0;

    printf("bsn << ");
    while(++timeout_count < timeout){

        while(boson_uart_read_nonblock()) {    

            payload[len] = boson_uart_read();
            printf("%02x ", payload[len]);
            

            if(payload[0] != 0x8e)
              break;

            /* Basic bounds protection */
            if(len < max_len)
                len++;
        }
        
        if((len > 0) && (payload[0] != 0x8e))
              break;

//        /* Once we have the header */
//        if(len > 6){
//            /* Check for total payload length */
//            uint16_t payload_len = (payload[4] << 8) | payload[5];
//            if(len == payload_len + 10){
//                break;
//            }
//        }else if(len > 0 && payload[0] != 0x6e){
//            /* Invalid process code */
//
//        }
//
        msleep(1);
    }

    printf("(%u ms)\n", timeout_count);

    return R_SUCCESS;
} // End CLIENT_dispatcher()



void boson_init(){

    boson_uart_init();

    msleep(2000);

    while(boson_uart_rxempty_read() == 0)
        boson_uart_read();


    dispatcher_tx(10, BOSON_GETCAMERASN, 0, 0);
    dispatcher_rx();
    msleep(2000);

    dispatcher_tx(11, BOSON_GETCAMERASN, 0, 0);
    dispatcher_rx();

    msleep(2000);
    dispatcher_tx(12, BOSON_RUNFFC, 0, 0);
    dispatcher_rx();
    msleep(2000);

    while(1);
}