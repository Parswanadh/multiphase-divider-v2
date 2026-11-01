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
PVT: 9+ corners, -40 to 125 °C, 1.62–1.98 V. Enhanced divider: Fmax = 3.2 GHz, phase error ≤ 0.5°, power = 2.2 mW, area = 26.72×15.53 µm². Phase noise reduction = 6.02 dB. Delay range 91–171 ps across corners.

Unified figure of merit: FoM_phi = (f_max [GHz] × N_phase)/(P [mW] × Area [mm²]).

### Table I — Performance Comparison of Published CMOS FDs

| Ref | Tech (nm) | f_max (GHz) | Phases | Power (mW) | Area (mm²) | FoM_phi |
|-----|-----------|-------------|--------|------------|------------|---------|
| [1] Kuo 2025 | 180 | 1.4 | 8 | 2.34 | 0.0014 | 41.5 |
| [2] Cho 2007 | 130 | 1.2 | 8 | 3.1 | 0.0020 | 15.5 |
| [3] Jang 2017 | 180 | 2.5 | 4 | 4.2 | 0.0030 | 7.9 |
| [4] Herzel 2005 | 250 | 2.5 | 8 | 12.0 | 0.0050 | 3.3 |
| [5] Jiang 2018 | 180 | 2.33 | 8 | 5.8 | 0.0040 | 8.0 |
| [6] Ahmed 2024 | 45 | 30 | 2 | 8.5 | 0.0015 | 47.1 |
| [7] Kim 2007 | 130 | 37.5 | 2 | 18.0 | 0.0020 | 20.8 |
| [8] Dekate 2012 | 180 | 5.0 | 4 | 6.5 | 0.0025 | 12.3 |
| This work | 180 | 3.2 | 8 | 2.2 | 0.000415 | 282.0 |

## V. Conclusion
The enhanced divider achieves 3.2 GHz max, 0.5° phase accuracy, 2.2 mW power, suitable for multiphase PLLs.

## References
[1] Y.-F. Kuo et al., "A Compact Multiphase Divide-by-Two CMOS Frequency Divider," IEEE Microw. Wireless Technol. Lett., vol. 35, no. 5, pp. 617-620, May 2025.
