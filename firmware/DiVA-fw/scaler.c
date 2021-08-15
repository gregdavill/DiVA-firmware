#include <scaler.h>
#include <generated/csr.h>


void init_scaler_640x512_upto_800x600(void);


 // Scaler coefficients generated with the following parameters:
 // delta_offset=0.1466666666666666
 // n_phases=75
 // n_taps=4

const uint32_t scaler_coef_64upto75 [300] = {
        0x00000000, 0x01000100, 0x02000000, 0x03000000, 0x0001fff3, 0x010100f3, 0x0201001c, 0x0301fffe, 0x0002ffee, 0x010200d2, 0x02020047, 0x0302fff9, 0x0003ffef, 0x010300a4, 0x0203007a, 0x0303fff3, 
        0x0004fff4, 0x01040071, 0x020400ad, 0x0304ffee, 0x8005fffa, 0x8105003f, 0x820500d9, 0x8305ffee, 0x0006ffff, 0x01060016, 0x020600f7, 0x0306fff5, 0x0007fffd, 0x010700ff, 0x02070003, 0x03070000, 
        0x0008fff1, 0x010800ee, 0x02080023, 0x0308fffd, 0x0009ffee, 0x010900cb, 0x02090050, 0x0309fff8, 0x000afff0, 0x010a009b, 0x020a0084, 0x030afff2, 0x000bfff5, 0x010b0067, 0x020b00b6, 0x030bffee, 
        0x800cfffb, 0x810c0036, 0x820c00e0, 0x830cffef, 0x000dffff, 0x010d0010, 0x020d00fa, 0x030dfff7, 0x000efffa, 0x010e00fe, 0x020e0008, 0x030e0000, 0x000ffff0, 0x010f00e9, 0x020f002b, 0x030ffffc, 
        0x0010ffee, 0x011000c3, 0x02100059, 0x0310fff6, 0x0011fff0, 0x01110092, 0x0211008d, 0x0311fff1, 0x0012fff6, 0x0112005e, 0x021200be, 0x0312ffee, 0x8013fffc, 0x8113002e, 0x821300e6, 0x8313fff0, 
        0x00140000, 0x0114000a, 0x021400fd, 0x0314fff9, 0x0015fff8, 0x011500fc, 0x0215000d, 0x03150000, 0x0016ffef, 0x011600e3, 0x02160032, 0x0316fffb, 0x0017ffee, 0x011700ba, 0x02170063, 0x0317fff5, 
        0x0018fff1, 0x01180088, 0x02180097, 0x0318fff0, 0x0019fff7, 0x01190055, 0x021900c7, 0x0319ffee, 0x801afffd, 0x811a0027, 0x821a00ec, 0x831afff1, 0x001b0000, 0x011b0005, 0x021b00ff, 0x031bfffc, 
        0x001cfff6, 0x011c00f9, 0x021c0013, 0x031cffff, 0x001dffee, 0x011d00dd, 0x021d003b, 0x031dfffa, 0x001effee, 0x011e00b2, 0x021e006c, 0x031efff4, 0x001ffff2, 0x011f007f, 0x021f00a0, 0x031fffef, 
        0x0020fff8, 0x0120004c, 0x022000ce, 0x0320ffee, 0x8021fffe, 0x81210020, 0x822100f1, 0x8321fff2, 0x00220000, 0x01220001, 0x022200ff, 0x0322ffff, 0x0023fff4, 0x012300f5, 0x02230019, 0x0323ffff, 
        0x0024ffee, 0x012400d6, 0x02240043, 0x0324fff9, 0x0025ffef, 0x012500a9, 0x02250075, 0x0325fff3, 0x0026fff3, 0x01260075, 0x022600a9, 0x0326ffef, 0x8027fff9, 0x81270043, 0x822700d6, 0x8327ffee, 
        0x0028ffff, 0x01280019, 0x022800f5, 0x0328fff4, 0x0029ffff, 0x012900ff, 0x02290001, 0x03290000, 0x002afff2, 0x012a00f1, 0x022a0020, 0x032afffe, 0x002bffee, 0x012b00ce, 0x022b004c, 0x032bfff8, 
        0x002cffef, 0x012c00a0, 0x022c007f, 0x032cfff2, 0x002dfff4, 0x012d006c, 0x022d00b2, 0x032dffee, 0x802efffa, 0x812e003b, 0x822e00dd, 0x832effee, 0x002fffff, 0x012f0013, 0x022f00f9, 0x032ffff6, 
        0x0030fffc, 0x013000ff, 0x02300005, 0x03300000, 0x0031fff1, 0x013100ec, 0x02310027, 0x0331fffd, 0x0032ffee, 0x013200c7, 0x02320055, 0x0332fff7, 0x0033fff0, 0x01330097, 0x02330088, 0x0333fff1, 
        0x0034fff5, 0x01340063, 0x023400ba, 0x0334ffee, 0x8035fffb, 0x81350032, 0x823500e3, 0x8335ffef, 0x00360000, 0x0136000d, 0x023600fc, 0x0336fff8, 0x0037fff9, 0x013700fd, 0x0237000a, 0x03370000, 
        0x0038fff0, 0x013800e6, 0x0238002e, 0x0338fffc, 0x0039ffee, 0x013900be, 0x0239005e, 0x0339fff6, 0x003afff1, 0x013a008d, 0x023a0092, 0x033afff0, 0x003bfff6, 0x013b0059, 0x023b00c3, 0x033bffee, 
        0x803cfffc, 0x813c002b, 0x823c00e9, 0x833cfff0, 0x003d0000, 0x013d0008, 0x023d00fe, 0x033dfffa, 0x003efff7, 0x013e00fa, 0x023e0010, 0x033effff, 0x003fffef, 0x013f00e0, 0x023f0036, 0x033ffffb, 
        0x0040ffee, 0x014000b6, 0x02400067, 0x0340fff5, 0x0041fff2, 0x01410084, 0x0241009b, 0x0341fff0, 0x0042fff8, 0x01420050, 0x024200cb, 0x0342ffee, 0x8043fffd, 0x81430023, 0x824300ee, 0x8343fff1, 
        0x00440000, 0x01440003, 0x024400ff, 0x0344fffd, 0x0045fff5, 0x014500f7, 0x02450016, 0x0345ffff, 0x0046ffee, 0x014600d9, 0x0246003f, 0x0346fffa, 0x0047ffee, 0x014700ad, 0x02470071, 0x0347fff4, 
        0x0048fff3, 0x0148007a, 0x024800a4, 0x0348ffef, 0x8049fff9, 0x81490047, 0x824900d2, 0x8349ffee, 0x004afffe, 0x014a001c, 0x024a00f3, 0x034afff3, 
};

 // Scaler coefficients generated with the following parameters:
 // delta_offset=0.19999999999999996
 // n_phases=5
 // n_taps=4

const uint32_t scaler_coef_4upto5 [20] = {
        0x00000000, 0x01000100, 0x02000000, 0x03000000, 0x0001fff0, 0x010100e9, 0x0201002b, 0x0301fffc, 0x0002ffee, 0x010200b2, 0x0202006c, 0x0302fff4, 0x8003fff4, 0x8103006c, 0x820300b2, 0x8303ffee, 
        0x0004fffc, 0x0104002b, 0x020400e9, 0x0304fff0, 
};



 // Scaler coefficients generated with the following parameters:
 // delta_offset=0.5
 // n_phases=2
 // n_taps=3

const uint32_t scaler_coef_1upto2 [6] = {
        0x80000000, 0x81000100, 0x82000000, 0x0001fff0, 0x01010090, 0x02010090, 
};


 // Scaler coefficients generated with the following parameters:
 // delta_offset=0.28888888888888886
 // n_phases=45
 // n_taps=3

const uint32_t scaler_coef_32upto45 [135] = {
        0x00000000, 0x01000100, 0x02000000, 0x0001ffee, 0x010100d3, 0x02010046, 0x8002fff3, 0x81020074, 0x820200aa, 0x0003ffff, 0x01030019, 0x020300f5, 0x0004fff2, 0x010400f1, 0x0204001e, 0x8005ffef, 
        0x810500a3, 0x8205007c, 0x0006fffa, 0x0106003f, 0x020600d9, 0x0007fffe, 0x010700ff, 0x02070003, 0x0008ffee, 0x010800cd, 0x0208004d, 0x8009fff4, 0x8109006c, 0x820900b2, 0x000affff, 0x010a0014, 
        0x020a00f8, 0x000bfff1, 0x010b00ed, 0x020b0024, 0x800cfff0, 0x810c009b, 0x820c0084, 0x000dfffb, 0x010d0038, 0x020d00df, 0x000efffb, 0x010e00fe, 0x020e0006, 0x000fffee, 0x010f00c7, 0x020f0055, 
        0x8010fff5, 0x81100064, 0x821000b9, 0x00110000, 0x0111000f, 0x021100fb, 0x0012fff0, 0x011200e9, 0x0212002b, 0x8013fff0, 0x81130093, 0x8213008c, 0x0014fffc, 0x01140031, 0x021400e4, 0x0015fff9, 
        0x011500fd, 0x0215000a, 0x0016ffee, 0x011600c0, 0x0216005c, 0x8017fff6, 0x8117005c, 0x821700c0, 0x00180000, 0x0118000a, 0x021800fd, 0x0019ffef, 0x011900e4, 0x02190031, 0x801afff1, 0x811a008c, 
        0x821a0093, 0x001bfffc, 0x011b002b, 0x021b00e9, 0x001cfff7, 0x011c00fb, 0x021c000f, 0x001dffee, 0x011d00b9, 0x021d0064, 0x801efff7, 0x811e0055, 0x821e00c7, 0x001f0000, 0x011f0006, 0x021f00fe, 
        0x0020ffef, 0x012000df, 0x02200038, 0x8021fff2, 0x81210084, 0x8221009b, 0x0022fffd, 0x01220024, 0x022200ed, 0x0023fff5, 0x012300f8, 0x02230014, 0x0024ffee, 0x012400b2, 0x0224006c, 0x8025fff8, 
        0x8125004d, 0x822500cd, 0x00260000, 0x01260003, 0x022600ff, 0x0027ffee, 0x012700d9, 0x0227003f, 0x8028fff2, 0x8128007c, 0x822800a3, 0x0029fffe, 0x0129001e, 0x022900f1, 0x002afff4, 0x012a00f5, 
        0x022a0019, 0x802bffee, 0x812b00aa, 0x822b0074, 0x002cfff9, 0x012c0046, 0x022c00d3, 
};


static void load_height(const uint32_t* coeffs, uint32_t len, uint32_t phases){
	uint32_t bank_mask = 0;
	//if(pipeline_config_scaler_bank_read()){
	//	bank_mask |= 0x40000000;
	//}

	for(int i = 0; i < len; i++){
		scaler_height_coeff_data_write(coeffs[i] | bank_mask);
	}
	scaler_height_phases_write(phases);
}

static void load_width(const uint32_t* coeffs, uint32_t len, uint32_t phases){
	uint32_t bank_mask = 0;
	//if(pipeline_config_scaler_bank_read()){
	//	bank_mask |= 0x40000000;
	//}
	
	for(int i = 0; i < len; i++){
		scaler_width_coeff_data_write(coeffs[i] | bank_mask);
	}
	scaler_width_phases_write(phases);
}

static void load_64upto75(void (*func)(const uint32_t*, uint32_t, uint32_t)){
	func(scaler_coef_64upto75, sizeof(scaler_coef_64upto75) / sizeof(const uint32_t), 75);
}

static void load_4upto5(void (*func)(const uint32_t*, uint32_t, uint32_t)){
	func(scaler_coef_4upto5, sizeof(scaler_coef_4upto5) / sizeof(const uint32_t), 5);
}

static void load_1upto2(void (*func)(const uint32_t*, uint32_t, uint32_t)){
	func(scaler_coef_1upto2, sizeof(scaler_coef_1upto2) / sizeof(const uint32_t), 2);
}

static void load_32upto45(void (*func)(const uint32_t*, uint32_t, uint32_t)){
	func(scaler_coef_32upto45, sizeof(scaler_coef_32upto45) / sizeof(const uint32_t), 45);
}


void init_scaler_640x512_upto_800x600(void){
	load_64upto75(load_height);
	load_4upto5(load_width);
}

void init_scaler_640x512_upto_750x600(void){
	load_64upto75(load_height);
	load_64upto75(load_width);
}

void init_scaler_640x512_upto_800x640(void){
	load_4upto5(load_height);
	load_4upto5(load_width);
}

void init_scaler(void){
	load_32upto45(load_height);
	load_1upto2(load_width);
}

void switch_mode(int mode){

	/* Toggle bank, will be applied on write to update_values() */
	pipeline_config_scaler_bank_write(pipeline_config_scaler_bank_read() == 0 ? 1 : 0);
	pipeline_config_scaler_fill_write(0);

	if(mode == 0){ /* 1:1 */
		pipeline_config_x_start_write(213 + (800-640)/2);
		pipeline_config_y_start_write(27 +  (600-512)/2);
		pipeline_config_x_stop_write(640 + pipeline_config_x_start_read());
		pipeline_config_y_stop_write(512 + pipeline_config_y_start_read());

		pipeline_config_scaler_enable_write(0);
	}
	
	if(mode == 1){ /* Full Screen */
		pipeline_config_x_start_write(213);
		pipeline_config_y_start_write(27);
		pipeline_config_x_stop_write(800 + pipeline_config_x_start_read());
		pipeline_config_y_stop_write(600-2 + pipeline_config_y_start_read());


		init_scaler_640x512_upto_800x600();

		pipeline_config_scaler_enable_write(1);
	}

	if(mode == 2){ /* Fit Screen */
		pipeline_config_x_start_write(213 + 25);
		pipeline_config_y_start_write(27);
		pipeline_config_x_stop_write(750 + pipeline_config_x_start_read());
		pipeline_config_y_stop_write(600-2 + pipeline_config_y_start_read());

		init_scaler_640x512_upto_750x600();

		pipeline_config_scaler_enable_write(1);
	}

	if(mode == 3){ /* Fill Screen */
		pipeline_config_x_start_write(213);
		pipeline_config_y_start_write(24);
		pipeline_config_x_stop_write(800 + pipeline_config_x_start_read());
		pipeline_config_y_stop_write(618 + pipeline_config_y_start_read());

		init_scaler_640x512_upto_800x640();

		pipeline_config_scaler_enable_write(1);
		pipeline_config_scaler_fill_write(1);
	}
	
	/* Use new parameters */
	pipeline_config_update_values_write(1);
}
