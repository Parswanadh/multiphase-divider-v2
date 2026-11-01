# 23ECE302 Theory Assignment: Multiphase Divide-by-Two CMOS Frequency Divider

Reference: Y.-F. Kuo et al., "A Compact Multiphase Divide-by-Two CMOS Frequency Divider," IEEE Microw. Wireless Technol. Lett., vol. 35, no. 5, pp. 617-620, May 2025. Section and figure numbers below refer to that paper.

## Section 1: Transistor schematic (7 marks)

The divider is four cascaded differential D-latches (paper Figs. 2 and 3). A single latch has:

| Device | Role | Connections (drain, gate, source) |
|---|---|---|
| M1, M2 | Sampling differential pair | Q / D / xs and Qb / Db / xs |
| M5 | Positive-controlled sampling switch | xs / CK / tail |
| M3, M4 | Hold cross-coupled pair | Q / Qb / xh and Qb / Q / xh |
| M6 | Negative-controlled hold switch | xh / CKb / tail |
| M7 | NMOS tail current source, saturation | tail / bias / ground |
| R1, R2 | Resistive loads | VDD to Q and VDD to Qb |

Latch 1 and latch 4 sample when CK is high; latch 2 and latch 3 sample when CKb is high (they receive CK and CKb swapped).
The alternating cross-connections between latches are

- Q1b to D2, Q2 to D3, Q3b to D4, Q4 to D1b (and the complementary signals to Db).

Operation: when CK is high, latch 1 samples and latch 2 holds; when CK falls the roles swap. A signal therefore needs two
input clock periods to travel the loop once, which gives divide-by-two. Because the signal passes through latches whose
delays add up, the outputs are separated by multiples of the latch delay Td, and f0, f45, ..., f315 are taken from the
eight output nodes. Draw the full schematic of Fig. 2 with every net labelled and mark which latch uses CK and which CKb.

## Section 2: Sizing concept and Elmore delay (8 marks)

**Sizing rules used in the paper (Sec. II).**
- Each unit nMOS except M7 uses L = 180 nm and W = 0.9 um; M7 uses a longer channel (L = 360 nm, W = 1.8 um) so it behaves as a
  current source in saturation.
- The gate capacitance is assumed equal to one diffusion capacitance, called C.
- The nMOS turn-on resistance R is designed to be twice the load resistance R1 (so R1 = R/2) to obtain equal rise and fall
  times. M7 is always on, so node b is approximately grounded.

**Elmore delay (paper Eqs. 1 and 2, Fig. 5).** The Elmore delay of a path is the sum of the RC products along the
discharging (or charging) path.
1. Falling output (Fig. 5b): node a has already discharged to ground through capacitance 2C and resistance R/2. Node Q1 has
   capacitance (6 + 2)C = 8C and resistance R/2 to ground, so

   t_pdf = (8C)(R/2) = 4RC.
2. Rising output (Fig. 5c): the load is R1 = R/2 charging the same 8C, so

   t_pdr = (8C)(R1) = (8C)(R/2) = 4RC.
3. Hence t_pdr = t_pdf: equal rise and fall delays, which keeps the output symmetric.

**Speed limit.** Each latch has delay Td. Sampling and holding each take half a clock period, and a signal passes through two
latches (2 Td) in a half period, so the maximum input frequency is limited by 2 Td < T_CK / 2. Equally spaced 45 degree
phases need the delay step 2 Td to match T_CK / 4 (T_CK close to 8 Td).

**Sizing table.**

| Device | W (um) | L (um) | Reason |
|---|---|---|---|
| M1, M2 | 0.9 | 0.18 | Sampling pair, unit device |
| M3, M4 | 0.9 | 0.18 | Hold pair, unit device |
| M5, M6 | 0.9 | 0.18 | Clock switches, unit device |
| M7 | 1.8 | 0.36 | Long channel for current-source behaviour |
| R1, R2 | n/a | n/a | Load; the paper uses 1.5 kOhm |

**Simulation note (our own finding).** In the local ngspice model with the paper's 1.5 kOhm load the latch did not divide;
the hold pair needs gm x R above 1. A 5 kOhm load with a 1.2 V tail bias and 30 fF output loading divided correctly in
simulation (see the lab report), so R is a tuned value and depends on the device model.
