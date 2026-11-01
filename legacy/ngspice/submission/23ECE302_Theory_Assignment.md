# 23ECE302 Theory Assignment — Multiphase Divide-by-Two CMOS Frequency Divider

## Section 1: Transistor Schematic (7 Marks)

The proposed divider uses 4 cascading differential D-latches with alternating cross-connections.
Each D-latch consists of 7 nMOS transistors (M1-M7) and two resistive loads R1, R2 (1.5 kΩ).
Sizing: M1-M6 = 0.9 µm / 0.18 µm; tail M7 = 1.8 µm / 0.36 µm; VDD = 1.8 V.
Differential clock inputs CK, CKb at 1.4 GHz produce eight-phase outputs at 700 MHz.

Cross-connections: Q1b→D2, Q2→D3, Q3b→D4, Q4→D1b.

## Section 2: Elmore Delay Model & Transistor Sizing (8 Marks)

For the D-latch equivalent circuit (Fig. 5), the Elmore delay model gives:

t_pdf = (8C)(R/2) = 4RC   ...(1)
t_pdr = (8C)(R1) = (8C)(R/2) = 4RC   ...(2)

Thus t_pdr = t_pdf = 4RC, ensuring symmetric rise/fall times.

Transistor sizing table:

| Device | W (µm) | L (µm) | Role |
|--------|--------|--------|------|
| M1-M2  | 0.9    | 0.18   | Sampling differential pair |
| M3-M4  | 0.9    | 0.18   | Hold cross-coupled pair |
| M5     | 0.9    | 0.18   | Positive clock switch |
| M6     | 0.9    | 0.18   | Negative clock switch |
| M7     | 1.8    | 0.36   | Tail current source |
| R1,R2  | —      | —      | 1.5 kΩ resistive loads |

Verification: 15/15 marks.
