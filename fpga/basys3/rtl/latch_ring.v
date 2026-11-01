//==============================================================================
// latch_ring.v
//
// 4-Stage Level-Sensitive D-Latch Ring Multiphase Frequency Divider
// Functionally modeling the Kuo et al. (IEEE LMWT 2025) divide-by-2 topology
// as evaluated in GPDK045 (spectre/divider_gpdk45.scs).
//
// Target Hardware: Digilent Basys 3 (Xilinx Artix-7 XC7A35T-1CPG236C)
//
// Interconnect Topology:
//   Latch 1 (CK):  D1  = Q4b  -> Outputs Q1,  Q1b  [INIT = 1]
//   Latch 2 (CKb): D2  = Q1b  -> Outputs Q2,  Q2b  [INIT = 1]
//   Latch 3 (CKb): D3  = Q2   -> Outputs Q3,  Q3b  [INIT = 0]
//   Latch 4 (CK):  D4  = Q3b  -> Outputs Q4,  Q4b  [INIT = 0]
//
// Note on Primitives:
//   - In synthesis: uses Xilinx 7-series LDCE / LDPE primitives with async reset.
//   - In simulation (`ifdef SIMULATION): uses pure behavioural latches with
//     an optional parameterised per-stage propagation delay STAGE_DELAY_NS.
//==============================================================================

`timescale 1ns/1ps

`ifdef SIMULATION
// Pure behavioural level-sensitive transparent latch with async reset & delay
module dlatch_wrapper #(
    parameter INIT_VAL = 1'b0,
    parameter real DELAY_NS = 0.0
)(
    input  wire d,
    input  wire g,    // Gate / Enable (transparent when high, holds when low)
    input  wire rst,  // Active-high asynchronous reset
    output wire q,
    output wire qb
);
    reg q_reg;

    always @(*) begin
        if (rst) begin
            q_reg = INIT_VAL;
        end else if (g) begin
            q_reg = d;
        end
    end

    // Parameterised continuous delay modeling finite stage propagation delay
    assign #(DELAY_NS) q  = q_reg;
    assign #(DELAY_NS) qb = ~q_reg;

endmodule

`else
// Xilinx 7-series native primitives wrapper for synthesis (Vivado & Yosys)
module dlatch_wrapper #(
    parameter INIT_VAL = 1'b0,
    parameter real DELAY_NS = 0.0
)(
    input  wire d,
    input  wire g,    // Gate / Enable (transparent when high, holds when low)
    input  wire rst,  // Active-high asynchronous reset
    output wire q,
    output wire qb
);
    wire q_int;

    generate
        if (INIT_VAL == 1'b1) begin : gen_ldpe
            // Transparent latch with asynchronous preset
            LDPE #(.INIT(1'b1)) u_latch (
                .Q(q_int),
                .PRE(rst),
                .D(d),
                .G(g),
                .GE(1'b1)
            );
        end else begin : gen_ldce
            // Transparent latch with asynchronous clear
            LDCE #(.INIT(1'b0)) u_latch (
                .Q(q_int),
                .CLR(rst),
                .D(d),
                .G(g),
                .GE(1'b1)
            );
        end
    endgenerate

    assign q  = q_int;
    assign qb = ~q_int;

endmodule
`endif

//------------------------------------------------------------------------------
// Top-level ring module
//------------------------------------------------------------------------------
module latch_ring #(
    parameter real STAGE_DELAY_NS = 0.0
)(
    input  wire       ck,          // Input ring clock
    input  wire       ckb,         // Inverted ring clock (~ck)
    input  wire       rst,         // Active-high async reset / start-up kick
    output wire       q1,  q1b,
    output wire       q2,  q2b,
    output wire       q3,  q3b,
    output wire       q4,  q4b,
    output wire [7:0] phases_rot,  // 8 phases ordered by sequential rising edges
    output wire [7:0] phases_raw   // Direct latch outputs: {q4b,q3b,q2b,q1b, q4,q3,q2,q1}
);

    // Stage 1: clocked on CK, samples Q4b (Db1 = Q4)
    dlatch_wrapper #(
        .INIT_VAL(1'b1),
        .DELAY_NS(STAGE_DELAY_NS)
    ) u_latch1 (
        .d(q4b),
        .g(ck),
        .rst(rst),
        .q(q1),
        .qb(q1b)
    );

    // Stage 2: clocked on CKb, samples Q1b (Db2 = Q1)
    dlatch_wrapper #(
        .INIT_VAL(1'b1),
        .DELAY_NS(STAGE_DELAY_NS)
    ) u_latch2 (
        .d(q1b),
        .g(ckb),
        .rst(rst),
        .q(q2),
        .qb(q2b)
    );

    // Stage 3: clocked on CKb, samples Q2 (Db3 = Q2b)
    dlatch_wrapper #(
        .INIT_VAL(1'b0),
        .DELAY_NS(STAGE_DELAY_NS)
    ) u_latch3 (
        .d(q2),
        .g(ckb),
        .rst(rst),
        .q(q3),
        .qb(q3b)
    );

    // Stage 4: clocked on CK, samples Q3b (Db4 = Q3)
    dlatch_wrapper #(
        .INIT_VAL(1'b0),
        .DELAY_NS(STAGE_DELAY_NS)
    ) u_latch4 (
        .d(q3b),
        .g(ck),
        .rst(rst),
        .q(q4),
        .qb(q4b)
    );

    // Sequential rising edge order:
    //   phase 0 (  0 deg): q1
    //   phase 1 ( 45 deg): q2b
    //   phase 2 ( 90 deg): q3b
    //   phase 3 (135 deg): q4
    //   phase 4 (180 deg): q1b
    //   phase 5 (225 deg): q2
    //   phase 6 (270 deg): q3
    //   phase 7 (315 deg): q4b
    assign phases_rot = {q4b, q3, q2, q1b, q4, q3b, q2b, q1};

    // Raw direct order:
    assign phases_raw = {q4b, q3b, q2b, q1b, q4, q3, q2, q1};

endmodule
