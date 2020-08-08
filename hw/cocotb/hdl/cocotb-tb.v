`timescale 100ps / 1ps

module tb(
    input clock_2x_in,
    input clock_2x_in_90,
	input clock,
	input reset,
	output hyperRAM_rst_n,
	input hyperRAM_clk_p,
	input hyperRAM_clk_n,
	output hyperRAM_cs_n,
	inout [7:0] hyperRAM_dq,
	inout hyperRAM_rwds,
	input [29:0] wishbone_adr,
	output [31:0] wishbone_dat_r,
	input [31:0] wishbone_dat_w,
	input [3:0] wishbone_sel,
	input wishbone_cyc,
	input wishbone_stb,
	output wishbone_ack,
	input wishbone_we,
	input [2:0] wishbone_cti,
	input [1:0] wishbone_bte,
	output wishbone_err,
	input [4095:0] test_name
);

sim sim (
	.clock_2x_in(clock_2x_in),
	.clock_2x_in_90(clock_2x_in_90),
	.clock(clock),
	.reset(reset),
    .hyperRAM_rst_n(hyperRAM_rst_n),
	.hyperRAM_clk_p(hyperRAM_clk_p),
	.hyperRAM_clk_n(hyperRAM_clk_n),
	.hyperRAM_cs_n(hyperRAM_cs_n),
	.hyperRAM_dq(hyperRAM_dq),
	.hyperRAM_rwds(hyperRAM_rwds),
	.wishbone_adr(wishbone_adr),
	.wishbone_dat_r(wishbone_dat_r),
	.wishbone_dat_w(wishbone_dat_w),
	.wishbone_sel(wishbone_sel),
	.wishbone_cyc(wishbone_cyc),
	.wishbone_stb(wishbone_stb),
	.wishbone_ack(wishbone_ack),
	.wishbone_we(wishbone_we),
	.wishbone_cti(wishbone_cti),
	.wishbone_bte(wishbone_bte),
	.wishbone_err(wishbone_err)
);

  // Dump waves
  initial begin
    $dumpfile("dump.vcd");
    $dumpvars(0, tb);
  end

endmodule
