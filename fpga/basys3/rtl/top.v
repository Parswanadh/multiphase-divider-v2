//==============================================================================
// top.v
//
// Top-Level Basys 3 FPGA Demonstrator for Kuo et al. 8-Phase CMOS Divider Ring
// Target Device: Digilent Basys 3 (Xilinx Artix-7 XC7A35T-1CPG236C)
//
// Clocks:
//   - 100 MHz primary oscillator on pin W5
//   - Internally divided ring clock CK and CKb with 3-bit switch rate select:
//       sw[2:0] = 000:   2 Hz   (Human-eye visible on LEDs, 125 ms per 45 deg step)
//       sw[2:0] = 001:  10 Hz   (Fast LED rotation)
//       sw[2:0] = 010: 100 Hz   (Low frequency test)
//       sw[2:0] = 011:   1 kHz  (Audio / general test)
//       sw[2:0] = 100: 100 kHz  (Oscilloscope audio/RF band)
//       sw[2:0] = 101:   1 MHz  (Oscilloscope probe demonstration)
//       sw[2:0] = 110:  10 MHz  (High-speed oscilloscope demonstration)
//       sw[2:0] = 111: 100 MHz  (Direct oscillator bypass)
//
// User Interface:
//   - Reset: btnC (Center button) OR sw[15] (Slide switch 15)
//   - Rate Select: sw[2:0]
//   - Display Mode: sw[3]
//       sw[3] = 0: led[7:0] shows phases_rot (0, 45, 90, 135, 180, 225, 270, 315 deg)
//       sw[3] = 1: led[7:0] shows phases_raw (Q1..Q4, Q1b..Q4b)
//   - Status LEDs:
//       led[10:8] = sw[2:0] (Active rate indicator)
//       led[11]   = ck (Ring clock state)
//       led[14]   = Heartbeat (1 Hz toggle from 100 MHz clock)
//       led[15]   = Reset indicator (active high)
//
// Hardware Outputs:
//   - Pmod JA [pins 1..4, 7..10]: Raw differential outputs Q1..Q4, Q1b..Q4b
//   - Pmod JB [pins 1..4, 7..10]: Sequential rotating 8 phases (phases_rot[7:0])
//==============================================================================

`timescale 1ns/1ps

module top (
    input  wire        clk,        // 100 MHz oscillator input (Basys 3 pin W5)
    input  wire [15:0] sw,         // 16 slide switches
    input  wire        btnC,       // Center push button (Reset)
    output wire [15:0] led,        // 16 user LEDs
    output wire [7:0]  ja,         // Pmod JA header (Q1..Q4, Q1b..Q4b)
    output wire [7:0]  jb          // Pmod JB header (phases_rot[7:0])
);

    //--------------------------------------------------------------------------
    // Reset generation (Active-High)
    //--------------------------------------------------------------------------
    wire rst = btnC | sw[15];

    //--------------------------------------------------------------------------
    // Clock Rate Generator
    //--------------------------------------------------------------------------
    // Generates square-wave clocks at selectable frequencies from 100 MHz.
    // Counter limit is (100_000_000 / (2 * freq)) - 1
    reg [24:0] div_cnt = 25'd0;
    reg [24:0] div_limit;
    reg        clk_div_reg = 1'b0;

    always @(*) begin
        case (sw[2:0])
            3'b000: div_limit = 25'd24_999_999; //   2 Hz (half-period = 0.25 s)
            3'b001: div_limit = 25'd4_999_999;  //  10 Hz (half-period = 0.05 s)
            3'b010: div_limit = 25'd499_999;    // 100 Hz (half-period = 5 ms)
            3'b011: div_limit = 25'd49_999;     //   1 kHz (half-period = 500 us)
            3'b100: div_limit = 25'd499;        // 100 kHz (half-period = 5 us)
            3'b101: div_limit = 25'd49;         //   1 MHz (half-period = 500 ns)
            3'b110: div_limit = 25'd4;          //  10 MHz (half-period = 50 ns)
            default: div_limit = 25'd0;         // 100 MHz bypass
        endcase
    end

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            div_cnt     <= 25'd0;
            clk_div_reg <= 1'b0;
        end else if (sw[2:0] == 3'b111) begin
            div_cnt     <= 25'd0;
            clk_div_reg <= 1'b0;
        end else begin
            if (div_cnt >= div_limit) begin
                div_cnt     <= 25'd0;
                clk_div_reg <= ~clk_div_reg;
            end else begin
                div_cnt <= div_cnt + 1'b1;
            end
        end
    end

    // Clock selection: 100 MHz bypass or divided clock
    wire ck_raw  = (sw[2:0] == 3'b111) ? clk : clk_div_reg;
    wire ckb_raw = ~ck_raw;

    // Clock Buffers for low skew
    wire ck;
    wire ckb;

`ifdef SIMULATION
    assign ck  = ck_raw;
    assign ckb = ckb_raw;
`else
    BUFG u_bufg_ck  (.I(ck_raw),  .O(ck));
    BUFG u_bufg_ckb (.I(ckb_raw), .O(ckb));
`endif

    //--------------------------------------------------------------------------
    // 1 Hz Heartbeat Counter for System Vitality
    //--------------------------------------------------------------------------
    reg [25:0] hb_cnt = 26'd0;
    reg        hb_led = 1'b0;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            hb_cnt <= 26'd0;
            hb_led <= 1'b0;
        end else begin
            if (hb_cnt >= 26'd49_999_999) begin
                hb_cnt <= 26'd0;
                hb_led <= ~hb_led;
            end else begin
                hb_cnt <= hb_cnt + 1'b1;
            end
        end
    end

    //--------------------------------------------------------------------------
    // Multiphase Latch Ring Core Instance
    //--------------------------------------------------------------------------
    wire q1, q1b, q2, q2b, q3, q3b, q4, q4b;
    wire [7:0] phases_rot;
    wire [7:0] phases_raw;

    latch_ring #(
        .STAGE_DELAY_NS(0.0) // Synthesizable zero-delay digital model
    ) u_ring (
        .ck(ck),
        .ckb(ckb),
        .rst(rst),
        .q1(q1),
        .q1b(q1b),
        .q2(q2),
        .q2b(q2b),
        .q3(q3),
        .q3b(q3b),
        .q4(q4),
        .q4b(q4b),
        .phases_rot(phases_rot),
        .phases_raw(phases_raw)
    );

    //--------------------------------------------------------------------------
    // Output Mapping: Pmod JA and JB
    //--------------------------------------------------------------------------
    // Pmod JA: Raw differential outputs (ideal for 4-channel or 8-channel probes)
    //   JA[0]: Q1   (pin 1)
    //   JA[1]: Q2   (pin 2)
    //   JA[2]: Q3   (pin 3)
    //   JA[3]: Q4   (pin 4)
    //   JA[4]: Q1b  (pin 7)
    //   JA[5]: Q2b  (pin 8)
    //   JA[6]: Q3b  (pin 9)
    //   JA[7]: Q4b  (pin 10)
    assign ja = {q4b, q3b, q2b, q1b, q4, q3, q2, q1};

    // Pmod JB: Rotating 8-phase bus (phases_rot[7:0])
    //   JB[0]: 0 deg (Q1)
    //   JB[1]: 45 deg (Q2b)
    //   JB[2]: 90 deg (Q3b)
    //   JB[3]: 135 deg (Q4)
    //   JB[4]: 180 deg (Q1b)
    //   JB[5]: 225 deg (Q2)
    //   JB[6]: 270 deg (Q3)
    //   JB[7]: 315 deg (Q4b)
    assign jb = phases_rot;

    //--------------------------------------------------------------------------
    // Output Mapping: LEDs and Minimal UI
    //--------------------------------------------------------------------------
    // led[7:0]: Selectable by sw[3] between rotating phases and raw outputs
    assign led[7:0] = (sw[3]) ? phases_raw : phases_rot;

    // Status LEDs
    assign led[10:8] = sw[2:0];    // Active rate setting indicator
    assign led[11]   = ck;         // Ring clock state
    assign led[12]   = 1'b0;       // Unused
    assign led[13]   = 1'b0;       // Unused
    assign led[14]   = hb_led;     // 1 Hz heartbeat
    assign led[15]   = rst;        // Reset indicator

endmodule
