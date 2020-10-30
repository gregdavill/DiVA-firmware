
#include <stdint.h>

#include "../boson/FunctionCodes.h"
#include "../boson/Serializer_BuiltIn.h"
#include "../boson/ReturnCodes.h"
#include "../boson/flirCRC.h"
#include "../boson/FSLP.h"


void boson_init(void);
FLR_RESULT dispatcher_tx(uint32_t seqNum, FLR_FUNCTION fnID, const uint8_t *sendData, const uint32_t sendBytes);
FLR_RESULT dispatcher_rx(uint8_t* recvData, uint32_t* recvBytes);
FLR_RESULT dispatcher(FLR_FUNCTION fnID, const uint8_t *sendData, const uint32_t sendBytes);
void boson_set_lut(uint32_t lut);
void boson_set_averager(uint32_t en);