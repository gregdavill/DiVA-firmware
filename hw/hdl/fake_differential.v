// DDR mode uses Lattice ECP5 vendor-specific module ODDRX1F

module fake_differential
(
  input clk_shift, // used only in DDR mode
  // [1:0]:DDR [0]:SDR TMDS
  input [1:0] in_clock, in_red, in_green, in_blue,
  // [3]:clock [2]:red [1]:green [0]:blue 
  output [3:0] out_p,

  input [3:0] move,
  input loadn,
  input dir
);
    parameter C_ddr = 1'b0; // 0:SDR 1:DDR

    wire [1:0] tmds[3:0];
    assign tmds[3] = in_clock;
    assign tmds[2] = in_red;
    assign tmds[1] = ~in_green;
    assign tmds[0] = in_blue;

    // register stage to improve timing of the fake differential
    reg [1:0] R_tmds_p[3:0];
    generate
      genvar i;
      for(i = 0; i < 4; i++)
      begin : TMDS_pn_registers
        always @(posedge clk_shift) R_tmds_p[i] <=  tmds[i];
      end
    endgenerate

    wire [3:0] _out_p;
    
    // output SDR/DDR to fake differential
    generate
      genvar i;
      if(C_ddr == 1'b1)
        for(i = 0; i < 4; i++)
        begin : DDR_output_mode
          ODDRX1F
          ddr_p_instance
          (
            .D0(R_tmds_p[i][0]),
            .D1(R_tmds_p[i][1]),
            .Q(_out_p[i]),
            .SCLK(clk_shift),
            .RST(0)
          );
          DELAYF
          #(
            .DEL_MODE("USER_DEFINED"),
            .DEL_VALUE(0)
          )
          del_p
          (
            .A(_out_p[i]),
            .LOADN(loadn),
            .MOVE(move[i]),
            .DIRECTION(dir),
            .Z(out_p[i])
          );
        end
      else
        for(i = 0; i < 4; i++)
        begin : SDR_output_mode
          assign out_p[i] = R_tmds_p[i][0];
        end
    endgenerate

endmodule
