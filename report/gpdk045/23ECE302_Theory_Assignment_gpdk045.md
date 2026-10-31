# 23ECE302 Theory Assignment: Multiphase Divide-by-Two CMOS Frequency Divider (GPDK045, 45 nm)

Reference: Y.-F. Kuo et al., "A Compact Multiphase Divide-by-Two CMOS Frequency Divider," IEEE Microw. Wireless Technol. Lett., vol. 35, no. 5, pp. 617-620, May 2025. Section and figure numbers below refer to that paper. The process here is the Cadence GPDK045 (45 nm) kit. The device is `g45n1svt` (the 1.0 V standard-Vt NMOS, Virtuoso cell nmos1v).

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

**Sizing rules (paper Sec. II, applied to 45 nm starting values).**
- Each unit nMOS except M7 uses the 45 nm channel length (L = 45 nm) and W = 240 nm.
- M7 uses a longer channel (L = 90 nm, W = 480 nm) so that it behaves as a current source in saturation.
- The gate capacitance is assumed equal to one diffusion capacitance, called C.
- The nMOS turn-on resistance R is designed to be twice the load resistance R1 (so R1 = R/2) to obtain equal rise and
  fall times. M7 is always on, so node b is approximately grounded.

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

**Sizing table (45 nm starting values; the tuned-value column is filled after the gpdk045 sweep).**

| Device | W | L or R | Reason | Tuned value |
|---|---|---|---|---|
| M1, M2 | 240 nm | 45 nm | Sampling pair, unit device | ___ |
| M3, M4 | 240 nm | 45 nm | Hold pair, unit device | ___ |
| M5, M6 | 240 nm | 45 nm | Clock switches (CK, CKb), unit devices | ___ |
| M7 | 480 nm | 90 nm | Long channel so it acts as a current source in saturation | ___ |
| R1, R2 (load) | 8 kOhm | n/a | Load; the paper uses 1.5 kOhm (see below) | ___ |

**Why the load is 8 kOhm and not the paper's 1.5 kOhm.** The paper uses R1 = R2 = 1.5 kOhm. A pre-check on a generic
LEVEL=1 180 nm model (not the gpdk045 model; not a gpdk045 result) showed that the latch with 1.5 kOhm did not divide: the
hold pair must have gm x R above 1 to regenerate the state, and at 1.5 kOhm it did not. The 45 nm starting value is therefore
8 kOhm. The required value depends on the device transconductance, which differs between the generic model and gpdk045, so
the load must be retuned on gpdk045 and the tuned-value column records the result.
