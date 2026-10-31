# Cadence gpdk045 progress ledger

All numbers below come from Cadence Spectre 12.1 (MMSIM121) runs inside the CentOS VM, gpdk045_v_6_0, model sections tt/ff/ss/fs/sf, device g45n1svt (Virtuoso cell nmos1v). No local ngspice runs are used for the final report.

## Facts established (evidence in results/gpdk045 and git history)
- Unit-size devices (m=1) with the paper rule R1 = Ron/2 (Ron = 2.3 kOhm measured, dc sweep of W=240n L=45n at Vgs=1.0 V, Vd 10..100 mV: 2.28..2.73 kOhm) do NOT divide at 1, 1.4 or 2 GHz (outputs within ~20 mV).
- Division at 1.4 GHz needs load R >= ~1.1x the pull-down stack resistance (3*Ron/m): (m6,1.5k), (m4,2k), (m3,3k) divide; (m4,1k), (m3,2k), (m2,any<=3k) do not.
- PVT (45 runs: 5 corners x -40/27/125 C x 0.9/1.0/1.1 V, 1.4 GHz, strict 8-output division check):
  - A (m4, 2k, vb 0.8): 23/45; B (m4, 2k, vb 1.0): 27/45; C (m6, 1.5k, vb 0.8): 27/45
  - D (m4, 3k, vb 1.0): 41/45; E (m6, 2k, vb 1.0): 41/45; only 125 C corners fail
- Phase error falls with input frequency and is small only near the design's frequency limit: B reaches 3.78 deg at 6 GHz; D 13.8 deg at 5.5 GHz; E 15.2 deg at 7 GHz.

## Rulings
- Ruling: nominal VDD = 1.0 V with +-10% (0.9/1.1) — PDK rates nmos1v at 1.1 V (max_vdd_1v=1.1), +10% lands exactly on the rating — if wrong, the 1.1 V corner is at the soft limit rather than 10% above a 1.1 V nominal.
- Ruling: two operating points reported (user request): 1.4 GHz (paper frequency; design D, PVT-robust) and 6 GHz (design B, 3.78 deg phase error) — the same topology and sizing rule, different load R — if wrong, the report can drop one column.
- Ruling: "without sizing" = unit devices (m=1) with the paper's rule R1 = Ron/2 literally applied; it does not divide, so its delay/PDP are n/a and only power is reported — if wrong, a working unsized variant (m=1, R=8k) can replace it.
- Ruling: strict division check (all 8 outputs at f_in/2 within 0.1 %, swing >= 0.1 V) after the advisor found false passes in the Q1-only check.
- Ruling: waveform figures are plotted from the Spectre output when a Cadence viewer screenshot is not available; the report says which is which.

## Tasks
- T1 VM environment (perl/gcc 32-bit fixes, disk, serial channel): complete
- T2 design exploration + PVT matrices: complete
- T3 final nominal runs with raw waveforms, op-point (M7 saturation): complete (M7 is in triode: V(tail) 8-67 mV vs Vdsat 358 mV)
- T4 schematic in Virtuoso: built in batch Virtuoso 6.1.5 (DLATCH, divider_core, tb_divider; schCheck 0/0, 0/0, 0/1); core connectivity diffed against the Spectre netlist: 0 mismatches; GUI screenshots pending
- T5 layout + DRC in Virtuoso/Assura: pending
- T6 report data assembly + docx: pending

## SKILL debugging findings (Virtuoso 6.1.5, 32-bit, batch)
- Lisp-style cond clauses `((null(x)) ...)` parse as calls of x: write `(null(x) ...)`.
- Variables are dynamically scoped: the PDK's libInit.il assigns a global `y` on first use (it overwrote a local named y): locals renamed v2y and the PDK is warmed up first.
- schCreateWireLabel 9-arg form must end with nil (t left the wire unnamed).
- Set CDF parameters before wiring (nmos1v symbol is rebuilt by the PDK callback).
- Ground net must be gnd! (analogLib gnd symbol), not 0.
- dbOpenCellViewByType for symbols needs viewType schematicSymbol.
