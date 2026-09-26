module counter(input logic clk, reset, enable, output logic [3:0] count);
  always_ff @(posedge clk) begin
    if (reset) count <= 4'd0;
    else if (enable && count != 4'd15) count <= count + 4'd1;
  end
endmodule
