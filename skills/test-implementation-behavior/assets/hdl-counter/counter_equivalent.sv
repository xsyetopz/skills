module counter(input logic clk, reset, enable, output logic [3:0] count);
  logic [3:0] next_count;
  always_comb begin
    next_count = count;
    if (enable && count < 4'd15) next_count = count + 4'd1;
    if (reset) next_count = 4'd0;
  end
  always_ff @(posedge clk) count <= next_count;
endmodule
