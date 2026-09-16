`timescale 1ns/1ps
module counter_tb;
  logic clk = 0, reset = 1, enable = 0;
  wire [3:0] count;
  counter dut(.clk(clk), .reset(reset), .enable(enable), .count(count));
  always #5 clk = ~clk;

  task automatic cycle(input bit rst, en, input logic [3:0] expected);
    @(negedge clk);
    reset = rst;
    enable = en;
    @(posedge clk);
    #1; // Observe after this fixture's nonblocking assignments.
    if (count !== expected) begin
      $display("CONTRACT FAIL: expected=%0d observed=%0d", expected, count);
      $fatal(1, "counter output violates the stated contract");
    end
  endtask

  initial begin
    cycle(1, 1, 0); // Reset wins over enable.
    cycle(0, 0, 0);
    for (int value = 1; value <= 15; value++)
      cycle(0, 1, 4'(value));
    cycle(0, 1, 15); // Reject the wrapping mutant here.
    cycle(0, 0, 15);
    cycle(1, 0, 0);
    cycle(0, 1, 1);
    $display("CONTRACT PASS");
    $finish;
  end
  initial begin
    #1000; // Fixture deadlock watchdog, not a product timing requirement.
    $fatal(2, "testbench did not complete");
  end
endmodule
