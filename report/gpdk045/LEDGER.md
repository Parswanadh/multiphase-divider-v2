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
- T4 schematic in Virtuoso: built in batch Virtuoso 6.1.5 (DLATCH, divider_core, tb_divider; schCheck 0/0, 0/0, 0/1); core connectivity diffed against the Spectre netlist: 0 mismatches; GUI screenshots captured in Virtuoso 6.1.5 at 1600x1200 (report/gpdk045/screens/schematic_*.png); library rebuilt with design D (R=3k, m=4), parameters read back from the database (results/gpdk045/virtuoso_dlatch_params_designD.txt)
- T5 layout + DRC: placement-only layout generated in Virtuoso (DLATCH: 7 nmos1v pcells + 2 poly resistors + pins; divider_core: 4 instances 2x2, clock-star lengths equal). Assura 4.1 DRC on DLATCH/layout: 21 errors in 3 rules (psubstrate StampErrorMult 1, StampErrorConnect 6, METAL1.A.1 area 14). NOT routed, NOT LVS-checked, no post-layout simulation.
- T6 report data assembly + docx: pending

## SKILL debugging findings (Virtuoso 6.1.5, 32-bit, batch)
- Lisp-style cond clauses `((null(x)) ...)` parse as calls of x: write `(null(x) ...)`.
- Variables are dynamically scoped: the PDK's libInit.il assigns a global `y` on first use (it overwrote a local named y): locals renamed v2y and the PDK is warmed up first.
- schCreateWireLabel 9-arg form must end with nil (t left the wire unnamed).
- Set CDF parameters before wiring (nmos1v symbol is rebuilt by the PDK callback).
- Ground net must be gnd! (analogLib gnd symbol), not 0.
- dbOpenCellViewByType for symbols needs viewType schematicSymbol.

- Console resolution raised to 1600x1200 via xrandr for legible screenshots; GUI sessions self-exit via hiRegTimer.
- Ruling: schematics in the report show design D (R=3k, m=4); the unsized variant (m=1, R=1.15k) is described by its netlist and simulation only — if wrong, rebuild with resR=1.15k mult=1 and recapture (about 5 min).

- Ruling: layout reported as placement-only with the real DRC count (21), because routing/LVS-clean layout was not achievable in the available time — if wrong, the layout section needs a routed layout; the report states the limitation.
- Assura batch RSF that works: avParameters(?inputLayout ("df2" "divider_lib") ?cellName ?viewName ?rulesFile ?workingDirectory ?runName ?avrpt t); run `assura file.rsf` (no avDRC call).

- Ruling (after independent review): 'without sizing' = dividing unit-size baseline m=1, R=8k, vb=1.0 at 1.4 GHz (Cadence run; 0.138 mW, 62.2 ps, 8.56 fJ, 26.4 deg); the paper-rule m=1/R1=1.15k circuit stays as the non-dividing finding. Threshold: R >= ~7k (stack rule predicts 7.6k). — if wrong, the baseline can be replaced by any other m=1 row of results/gpdk045/final/unsized_baseline.tsv.
- Review (REVIEW.md): 4 critical / 11 important / 13 minor; single fix pass dispatched (FIXLOG.md records outcomes).

- Schematic-driven simulation (OCEAN on divider_lib/tb_divider): divides 1 GHz -> 500 MHz, Q1 swing 0.713-1.006 V, 0.39 mW (tbVbias 0.8 V, differs from design D's 1.0 V): results/gpdk045/ocean_schematic_run.txt; script cadence/ocean/run_schematic_tb.ocn. NOT yet in the report text (add as 'simulation from the Virtuoso schematic' evidence).
- Layout automation research (Layout XL generate-from-source, router) agent running; notes expected in cadence/skill/auto/. Docs copied to /home/parshu/vm/cdsdocs/ic615_doc (not in git).
- Netlist from Virtuoso netlister diffed against standalone: devices/values identical; file results/gpdk045/virtuoso_netlist_tb_divider.scs
- Draft subsection for the OCEAN schematic simulation written by an agy/Gemini 3.8 Flash worker (text only, facts checked against the evidence files): report/gpdk045/section_schematic_sim.md; not yet merged into the docx builder.
