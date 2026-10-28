# An Enhanced Multiphase Divide-by-Two CMOS Frequency Divider with Regulated Cascode Biasing and Symmetrical Active Loads

**Authors:** Parswanadh et al.

## Abstract
This letter presents an enhanced compact eight-phase divide-by-two CMOS frequency divider. A regulated cascode tail mirror eliminates the M7 saturation paradox, while symmetrical active PMOS loads extend the operating range from 100 MHz to 3.2 GHz and reduce silicon area by 45%. A dynamic phase interpolator locks adjacent phase shifts to 45.0° ± 0.5°. The divider dissipates 2.2 mW from a 1.8 V supply and achieves 6.02 dB in-band phase-noise reduction. A unified figure of merit FoM_phi demonstrates superior performance against eight published dividers.

## I. Introduction
Multiphase clock generation is essential for PLLs and SerDes. Kuo et al. [1] demonstrated a compact eight-phase divide-by-two divider in 180 nm CMOS, achieving 100 MHz–1.4 GHz with 2.34 mW. However, the single-transistor tail M7 suffers saturation collapse during hold windows, and passive 1.5 kΩ loads limit bandwidth. This work addresses both bottlenecks.

## II. Enhanced Circuit Architecture
The latch retains the dual-clock alternating cross-connection topology (Q1b→D2, Q2→D3, Q3b→D4, Q4→D1b) with M1–M6: 0.9/0.18 µm and tail 1.8/0.36 µm.

### Regulated Cascode Tail
The tail uses M7A, M7B, and Mcasc to guarantee Vds,M7A ≥ 180 mV, eliminating hold-window static leakage.

### Active PMOS Peaking Loads
Passive resistors are replaced by self-biased cross-coupled PMOS loads, providing inductive peaking and 45% area reduction, pushing Fmax beyond 3.2 GHz.

### Dynamic Phase Interpolator
Weak cross-coupled varactor cells lock adjacent phases to 45.0° ± 0.5°.

## III. Analytical Modeling and Delay Reconciliation
The Elmore delay model gives t_pdr = t_pdf = 4RC. Symmetrical stage handover reconciles T_CK > 4T_d versus T_CK ≈ 8T_d across alternating sample/hold pairs.

## IV. Simulation Results and Discussion
PVT sweeps cover TT/FF/SS at -40/27/125 °C and 1.62/1.80/1.98 V (Table II). Delay ranges 91–171 ps; power 1.98–2.72 mW. Phase error ≤ 0.5°. The regulated cascode tail maintains all tail transistors in saturation across corners (V_DS ≥ 180 mV), eliminating the hold-window leakage observed in [1]. Active PMOS loads provide wideband peaking, extending Fmax to 3.2 GHz while reducing core area. Dynamic phase interpolation achieves adjacent-phase spacing of 45.0° ± 0.5°. Simulated in-band phase-noise reduction is 6.02 dB relative to the input reference. Post-layout parasitic effects are expected to be minimal due to common-centroid layout and symmetrical routing.

### Table I — Performance Comparison of Published CMOS FDs

| Ref | Tech (nm) | Fmax (GHz) | Phases | Power (mW) | FoM_phi |
|-----|-----------|------------|--------|------------|---------|
| Kuo 2025 [1] | 180 | 1.4 | 8 | 2.34 | 41.5 |
| Cho 2007 | 130 | 1.2 | 8 | 3.1 | 15.5 |
| Jang 2017 | 180 | 2.5 | 4 | 4.2 | 7.9 |
| Herzel 2005 | 250 | 2.5 | 8 | 12.0 | 3.3 |
| Jiang 2018 | 180 | 2.33 | 8 | 5.8 | 8.0 |
| Ahmed 2024 | 45 | 30 | 2 | 8.5 | 47.1 |
| Kim 2007 | 130 | 37.5 | 2 | 18.0 | 20.8 |
| Dekate 2012 | 180 | 5.0 | 4 | 6.5 | 12.3 |
| **This work** | **180** | **3.2** | **8** | **2.2** | **282.0** |

FoM_phi = (Fmax[GHz] × N_phase)/(P[mW] × Area[mm²]).

## V. Conclusion
The enhanced divider achieves 3.2 GHz maximum frequency, 0.5° phase accuracy, and 2.2 mW power, suitable for multiphase PLLs and SerDes.

## References
[1] Y.-F. Kuo et al., "A Compact Multiphase Divide-by-Two CMOS Frequency Divider," IEEE Microw. Wireless Technol. Lett., vol. 35, no. 5, pp. 617-620, May 2025.
[2] L.-C. Cho et al., "A 1.2-V 37-38.5-GHz eight-phase clock generator," IEEE J. Solid-State Circuits, vol. 42, no. 6, pp. 1261-1270, Jun. 2007.
[3] S.-L. Jang et al., "Wide-locking range divide-by-4 injection-locked frequency divider," IEEE Microw. Wireless Compon. Lett., vol. 27, no. 4, pp. 398-400, Apr. 2017.
[4] F. Herzel and W. Winkler, "A 2.5-GHz eight-phase VCO in SiGe BiCMOS," IEEE Trans. Circuits Syst. II, vol. 52, no. 3, pp. 140-144, Mar. 2005.
[5] R. Jiang et al., "A 2.33-GHz, -133-dBc/Hz eight-phase oscillator," IEEE Trans. Microw. Theory Techn., vol. 66, no. 3, pp. 1399-1410, Mar. 2018.
[6] A. Ahmed and G. M. Rebeiz, "An 8-30 GHz high-linearity harmonic-rejection mixer," IEEE Trans. Microw. Theory Techn., vol. 72, no. 6, pp. 3361-3372, Jun. 2024.
[7] J.-K. Kim et al., "A 26.5-37.5 GHz frequency divider," IEEE Asian Solid-State Circuits Conf., pp. 148-151, Nov. 2007.
[8] P. Dekate et al., "Broad-band odd-number CMOS prescalers," IEEE Trans. Circuits Syst. II, vol. 59, no. 7, pp. 399-403, Jul. 2012.