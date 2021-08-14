void hdmi_out0_i2c_init(void);
void hdmi_out0_print_edid(void);
void hdmi_out0_read_edid(uint8_t* buf);

struct edid {
	uint8_t header[8];

	uint8_t manufacturer[2];
	uint8_t product_code[2];
	uint8_t serial_number[4];
	uint8_t manufacture_week;
	uint8_t manufacture_year;

	uint8_t edid_version;
	uint8_t edid_revision;

	uint8_t video_input;
	uint8_t h_image_size;
	uint8_t v_image_size;
	uint8_t gamma;
	uint8_t feature_support;

	uint8_t cc_rg_l;
	uint8_t cc_bw_l;
	uint8_t cc_rx_h;
	uint8_t cc_ry_h;
	uint8_t cc_gx_h;
	uint8_t cc_gy_h;
	uint8_t cc_bx_h;
	uint8_t cc_by_h;
	uint8_t cc_wx_h;
	uint8_t cc_wy_h;

	uint8_t est_timings_1;
	uint8_t est_timings_2;
	uint8_t rsv_timings;

	uint8_t timings_std[16];

	uint8_t data_blocks[4][18];

	uint8_t ext_block_count;

	uint8_t checksum;
} __attribute__((packed));