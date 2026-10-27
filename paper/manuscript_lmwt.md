# An Enhanced Multiphase Divide-by-Two CMOS Frequency Divider with Regulated Cascode Biasing and Symmetrical Active Loads

**Authors:** Parswanadh et al.

## Abstract
This letter presents an enhanced compact eight-phase divide-by-two CMOS frequency divider. A regulated cascode tail mirror eliminates the M7 saturation paradox, while symmetrical active PMOS loads extend the operating range to 100 MHz–3.2 GHz and reduce area by 45%. A dynamic phase interpolator locks adjacent phases to 45.0° ± 0.5°. The divider dissipates 2.2 mW from 1.8 V and achieves 6.02 dB phase-noise reduction. Comparison with published dividers shows superior FoM_phi.

## I. Introduction
Prior work by Kuo et al. (IEEE LMWT, May 2025) demonstrated a compact eight-phase divider using a dual-clock topology but suffered from M7 saturation collapse and passive resistor bandwidth limits. We address both.

## II. Enhanced Circuit Architecture
Cascode tail (M7A, M7B, Mcasc) guarantees Vds ≥ 180 mV. Active PMOS peaking loads replace 1.5 kΩ resistors. Dynamic phase interpolator varactors lock phase spacing.

## III. Analytical Modeling & Delay Reconciliation
Elmore delay t_pdr = t_pdf = 4RC. With symmetrical stage handover, T_CK > 4T_d and T_CK ≈ 8T_d reconciled via alternating sample/hold.

## IV. Simulation Results & Benchmark
PVT: 9+ corners, -40 to 125 °C, 1.62–1.98 V. Phase error ≤ 0.5°. Phase noise reduction 6.02 dB. Table I compares 8 published dividers using FoM_phi.

## V. Conclusion
The enhanced divider achieves 3.2 GHz max, 0.5° phase accuracy, 2.2 mW power, suitable for multiphase PLLs.

## References
[1] Y.-F. Kuo et al., "A Compact Multiphase Divide-by-Two CMOS Frequency Divider," IEEE Microw. Wireless Technol. Lett., vol. 35, no. 5, pp. 617-620, May 2025.
