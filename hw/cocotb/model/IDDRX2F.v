// --------------------------------------------------------------------
// >>>>>>>>>>>>>>>>>>>>>>>>> COPYRIGHT NOTICE <<<<<<<<<<<<<<<<<<<<<<<<<
// --------------------------------------------------------------------
// Copyright (c) 2007 by Lattice Semiconductor Corporation
// --------------------------------------------------------------------
//
//
//                     Lattice Semiconductor Corporation
//                     5555 NE Moore Court
//                     Hillsboro, OR 97214
//                     U.S.A.
//
//                     TEL: 1-800-Lattice  (USA and Canada)
//                          1-408-826-6000 (other locations)
//
//                     web: http://www.latticesemi.com/
//                     email: techsupport@latticesemi.com
//
// --------------------------------------------------------------------
//
// Simulation Library File for IDDRX2F in ECP5U/M, LIFMD
//
// $Header: 
//

`resetall
`timescale 1 ns / 1 ps

`celldefine

module IDDRX2F(D, ECLK, SCLK, RST, ALIGNWD, Q0, Q1, Q2, Q3);

input  D, ECLK, SCLK, RST, ALIGNWD;
output Q0, Q1, Q2, Q3;

  
wire Db, SCLKB, RSTB1, RSTB2, ALIGNWDB;
reg RSTB, QP, QN;
reg M6, M8, M7, M9, S6, S7, S8, S9;
reg last_SCLKB, last_ECLKB;
reg DATA6, DATA9, DATA8, DATA7;
reg R6, R8, R9, R7;
reg CNT0, SEL, UPDATE, slip_reg0, slip_regn1, slip_state;
reg SRN, slip_async;
wire ECLKB, UPDATE_set;

//tri1 GSR_sig = GSR_INST.GSRNET;
//tri1 PUR_sig = PUR_INST.PURNET;

 
buf (Db, D);
buf (SCLKB, SCLK);
buf (ECLKB, ECLK);
buf (RSTB1, RST);
buf (ALIGNWDB, ALIGNWD);

buf (Q0, DATA6);
buf (Q1, DATA7);
buf (Q2, DATA8);
buf (Q3, DATA9);

      function DataSame;
        input a, b;
        begin
          if (a === b)
            DataSame = a;
          else
            DataSame = 1'bx;
        end
      endfunction

initial
begin
QP = 0;
QN = 0;
M6 = 0;
M8 = 0;
M7 = 0;
M9 = 0;
R6 = 0;
R8 = 0;
R9 = 0;
R7 = 0;
S6 = 0;
S8 = 0;
S9 = 0;
S7 = 0;
DATA6 = 0;
DATA8 = 0;
DATA9 = 0;
DATA7 = 0;
UPDATE = 0;
SEL = 0;
CNT0 = 0;
slip_reg0 = 0;
slip_regn1 = 1'b1;
slip_state = 0;
slip_async = 0;
end

initial
begin
last_SCLKB = 1'b0;
last_ECLKB = 1'b0;
end

   assign SRN = 1;
                                                                                               
  not (SR, SRN);
  or INST1 (RSTB2, RSTB1, SR);


always @ (SCLKB or ECLKB)
begin
   last_SCLKB <= SCLKB;
   last_ECLKB <= ECLKB;
end

// UPDATE and SEL signal generation
always @ (ECLKB or RSTB2)     // pos edge
begin
   if (RSTB2 == 1'b1)
   begin
      RSTB <= 1'b1;
   end
   else
   begin
      if (ECLKB === 1'b1 && last_ECLKB === 1'b0)
      begin
         RSTB <= 1'b0;
      end
   end
end

always @ (ECLKB or RSTB)     // pos edge
begin
   if (RSTB == 1'b1)
   begin
      slip_async <= 1'b0;
   end
   else
   begin
      if (ECLKB === 1'b1 && last_ECLKB === 1'b0)
      begin
         slip_async <= ALIGNWDB;
      end
   end
end

always @ (ECLKB or RSTB)     // pos edge
begin
   if (RSTB == 1'b1)
   begin
      slip_reg0 <= 1'b0;
      slip_regn1 <= 1'b1;
   end
   else
   begin
      if (ECLKB === 1'b1 && last_ECLKB === 1'b0)
      begin
         slip_reg0 <= slip_async;
         slip_regn1 <= ~slip_reg0;
      end
   end
end

and INST2 (slip_rst, slip_reg0, slip_regn1);
assign slip_trig = slip_rst;
nand INST3 (cnt_en, slip_rst, slip_state);
assign UPDATE_set = CNT0;  // latest fix in schematic (08/29)

always @ (ECLKB or RSTB)     // pos edge
begin
   if (RSTB == 1'b1)
   begin
      UPDATE <= 1'b0;
   end
   else
   begin
      if (ECLKB === 1'b1 && last_ECLKB === 1'b0)
      begin
         if (UPDATE_set == 1'b1)
         begin
            UPDATE <= 1'b1;
         end
         else if (UPDATE_set == 1'b0)
         begin
            UPDATE <= 1'b0;
         end
      end
   end
end

always @ (ECLKB or RSTB)
begin
   if (RSTB == 1'b1)
   begin
      CNT0 <= 1'b0;
      slip_state <= 1'b0;
      SEL <= 1'b0;
   end
   else
   begin
      if (ECLKB === 1'b1 && last_ECLKB === 1'b0)
      begin
         if (slip_trig == 1'b0)
         begin
            slip_state <= slip_state;
         end
         else if (slip_trig == 1'b1)
         begin
            slip_state <= ~slip_state;
         end

         if (cnt_en == 1'b0)
         begin
            CNT0 <= CNT0;
         end
         else if (cnt_en == 1'b1)
         begin
            CNT0 <= ~CNT0;
         end

         if (slip_trig == 1'b0)
         begin
            SEL <= SEL;
         end
         else if (slip_trig == 1'b1)
         begin
            SEL <= ~SEL;
         end
      end
   end
end

always @ (ECLKB or RSTB2)     //  edge
begin
   if (RSTB2 == 1'b1)
   begin
      QP <= 1'b0;
      QN <= 1'b0;
   end
   else
   begin
      if (ECLKB === 1'b1 && last_ECLKB === 1'b0)
      begin
         QP <= Db;
      end
      if (ECLKB === 1'b0 && last_ECLKB === 1'b1)
      begin
         QN <= Db;
      end
   end
end

always @ (ECLKB or RSTB2)     // pos edge
begin
   if (RSTB2 == 1'b1)
   begin
      R6 <= 1'b0;
      R8 <= 1'b0;
      R9 <= 1'b0;
      R7 <= 1'b0;
   end
   else
   begin
      if (ECLKB === 1'b1 && last_ECLKB === 1'b0)
      begin
         R8 <= QP;
         R6 <= R8;
         R9 <= QN;
         R7 <= R9;
      end
   end
end

always @ (R6 or R7 or SEL)
begin
   case (SEL)
        1'b0 :  M6 = R6;
        1'b1 :  M6 = R7;
        default M6 = DataSame(R7, R6);
   endcase
end

always @ (R8 or R9 or SEL)
begin
   case (SEL)
        1'b0 :  M8 = R8;
        1'b1 :  M8 = R9;
        default M8 = DataSame(R9, R8);
   endcase
end

always @ (R8 or R7 or SEL)
begin
   case (SEL)
        1'b0 :  M7 = R7;
        1'b1 :  M7 = R8;
        default M7 = DataSame(R8, R7);
   endcase
end

always @ (QP or R9 or SEL)
begin
   case (SEL)
        1'b0 :  M9 = R9;
        1'b1 :  M9 = QP;
        default M9 = DataSame(QP, R9);
   endcase
end

always @ (ECLKB or RSTB2)     // pos edge
begin
   if (RSTB2 == 1'b1)
   begin
      S6 <= 1'b0;
      S8 <= 1'b0;
      S9 <= 1'b0;
      S7 <= 1'b0;
   end
   else
   begin
      if (ECLKB === 1'b1 && last_ECLKB === 1'b0)
      begin
         if (UPDATE == 1'b1)
         begin
            S6 <= M6;
            S8 <= M8;
            S9 <= M9;
            S7 <= M7;
         end
      end
   end
end

always @ (SCLKB or RSTB2)     // pos edge
begin
   if (RSTB2 == 1'b1)
   begin
      DATA6 <= 1'b0;
      DATA8 <= 1'b0;
      DATA9 <= 1'b0;
      DATA7 <= 1'b0;
   end
   else
   begin
      if (SCLKB === 1'b1 && last_SCLKB === 1'b0)
      begin
         DATA6 <= S6;
         DATA8 <= S8;
         DATA9 <= S9;
         DATA7 <= S7;
      end
   end
end

endmodule

`endcelldefine
