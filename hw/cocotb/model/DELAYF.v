// --------------------------------------------------------------------
// >>>>>>>>>>>>>>>>>>>>>>>>> COPYRIGHT NOTICE <<<<<<<<<<<<<<<<<<<<<<<<<
// --------------------------------------------------------------------
// Copyright (c) 2005 by Lattice Semiconductor Corporation
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
// Simulation Library File for DELAYF in ECP5U/M, LIFMD
//
// $Header: $ 
//
`resetall
`timescale 1 ns / 1 ps
`celldefine
module DELAYF (A, LOADN, MOVE, DIRECTION, CFLAG, Z);
  input A, LOADN, MOVE, DIRECTION;
  output Z, CFLAG;
 
  parameter DEL_MODE = "USER_DEFINED";
  parameter DEL_VALUE = 0;


  localparam DEL_VALUE_ALI =0; //if users select the DEL_MODE to other than USER_DEFINED, this initial value depends on 
                              // device characterization data and may change
  localparam WAIT_FOR_EDGE = "DISABLED";
  
wire AB, LOADNB, MOVEB, DIRECTIONB, move_en;
reg drn, ZB, CFLAGB, last_move_en_reg, last_ZB, move_en_reg;
reg  [6:0] cntl_reg, cntl_reg_load;
realtime delta, cntl_delay;

   buf (AB, A);
   buf (LOADNB, LOADN);
   buf (MOVEB, MOVE);
   buf (DIRECTIONB, DIRECTION);
   buf (Z, ZB);
   buf (CFLAG, CFLAGB);
 
initial
begin
   cntl_delay = 0.0;
   delta = 0.025;
   CFLAGB = 0;
   drn = 0;
   move_en_reg = 0;
   
   if (DEL_MODE=="USER_DEFINED") begin 
   cntl_reg = (DEL_VALUE);
   end
   else begin 
   cntl_reg = (DEL_VALUE_ALI);
   end

   cntl_reg_load = cntl_reg;
   cntl_delay = cntl_reg_load * delta;
end

   always @ (move_en_reg, ZB)
   begin
      last_move_en_reg <= move_en_reg;
      last_ZB <= ZB;
   end

   always @(LOADNB, move_en_reg)
   begin
      if (LOADNB == 1'b0)
      begin
         drn <= 1'b0;
      end
      else
      begin
         if (move_en_reg === 1'b0 && last_move_en_reg === 1'b1)
            drn <= DIRECTIONB;
      end
   end


   always @(cntl_reg, LOADNB, move_en_reg)
   begin
      if (LOADNB == 1'b0)
      begin
         cntl_reg_load <= cntl_reg;
      end
      else
      begin
         if (move_en_reg === 1'b0 && last_move_en_reg === 1'b1)
         begin
            if (LOADNB == 1'b1)
            begin
               if (drn == 1'b0)   // up-delay
               begin
                  if (CFLAGB == 1'b0 || (cntl_reg_load == 7'b0000000))
                  begin
                     cntl_reg_load <= cntl_reg_load + 1;
                  end
               end
               else if (drn == 1'b1)   // down-delay
               begin
                  if (CFLAGB == 1'b0 || (cntl_reg_load == 7'b1111111))
                  begin
                     cntl_reg_load <= cntl_reg_load - 1'b1;
                  end
               end
            end
         end
      end
   end

  always @(cntl_reg_load)
  begin
      cntl_delay = cntl_reg_load * delta;
  end

  always @(*)
  begin
     if (DEL_MODE == "USER_DEFINED")
     begin
        ZB <= #cntl_delay AB;
     end
     else
    begin
        ZB <= AB;
     end
  end

   initial begin 
    if (DEL_MODE != "USER_DEFINED")
	$display("DEL_MODE!=USER_DEFINED, the initial value is %d  which cannot be changed ", DEL_VALUE_ALI);
    end
                                                                                                    
  always @(cntl_reg_load)
  begin
     if ((cntl_reg_load == 7'b1111111 && drn == 1'b0) || (cntl_reg_load == 7'b0000000 && drn == 1'b1))
        CFLAGB <= 1'b1;
     else
        CFLAGB <= 1'b0;
  end

  assign move_en = MOVEB & ~CFLAGB;

   always @(*)
   begin
      if (WAIT_FOR_EDGE == "ENABLED")
      begin
         if (ZB === 1'b0 && last_ZB === 1'b1)
         begin
            move_en_reg <= move_en;
         end
      end
      else
      begin
         move_en_reg <= move_en;
      end
   end

endmodule
`endcelldefine
