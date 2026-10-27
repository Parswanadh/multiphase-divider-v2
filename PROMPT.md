# MASTER AUTONOMOUS SPECIFICATION & EXECUTION PROMPT
## Multiphase CMOS Frequency Divider: Open-Source Implementation & Next-Gen Architecture (V2)

> **CORE DIRECTIVE FOR OPENCODE:**
> You must run continuously, autonomously, and in an iterative loop until ALL milestones and verification gates are 100% satisfied. Do NOT stop after planning or writing single files. Execute simulations, verify results, generate plots, compile reports, and push to GitHub.

---

### ZERO-TOLERANCE RULES & CONSTRAINTS
1. **NEVER DELETE ANY FILES (STRICT RULE):**
   - You must **NEVER** run `rm` or delete any file or directory.
   - If any file becomes obsolete, superseded, or irrelevant, move it into the `.trash/` directory (`mv <file> .trash/`).
   - `.trash/` is gitignored.
2. **PARALLEL SUBAGENT DELEGATION:**
   - Maximize parallelism. Dispatch tasks to your specialized subagents:
     - `circuit-engineer`: SPICE netlist modeling, BSIM integration, transient simulations.
     - `pvt-metrics-runner`: Automated Python scripts for Power, Delay, PDP, and PVT sweeps.
     - `layout-engineer`: Magic VLSI and KLayout layout scripts, DRC, and LVS checks.
     - `academic-author`: 23ECE302 Assignment (15 marks) and 23ECE383 System Project (40 marks) reports.
     - `research-author`: Publication-grade IEEE letter manuscript for V2.
     - `git-sync`: Continuous commits and pushes to GitHub.
3. **CONTINUOUS GIT PUSH:**
   - Commit and push to `origin main` after EVERY single milestone:
     ```bash
     git add -A
     git commit -m "feat(<milestone>): completed <description>"
     git push origin main
     ```
   - Repository: `https://github.com/Parswanadh/multiphase-divider-v2` (already connected to `origin`).
4. **SUDO CREDENTIALS:**
   - If root privileges are needed, the user password is `Parshu@12` (`echo "Parshu@12" | sudo -S <command>`).
   - Note: `ngspice`, `magic`, `klayout`, `gtkwave`, `python3-matplotlib`, `python3-scipy`, and `python3-numpy` are already pre-installed.

---

### DUAL-TRACK PROJECT SCOPE

```
                                    ┌────────────────────────────────────────────────────────┐
                                    │                     PROJECT SCOPE                      │
                                    └───────────────────────────┬────────────────────────────┘
                                                                │
                     ┌──────────────────────────────────────────┴──────────────────────────────────────────┐
                     ▼                                                                                     ▼
    ┌──────────────────────────────────┐                                                  ┌──────────────────────────────────┐
    │ TRACK A: Academic Deliverables   │                                                  │ TRACK B: IEEE V2 Research Paper  │
    │ (Course 23ECE302 & 23ECE383)     │                                                  │ (Next-Gen Enhanced Divider)      │
    ├──────────────────────────────────┤                                                  ├──────────────────────────────────┤
    │ • 15 Marks: Theory Assignment    │                                                  │ • Exploit 13 Single-Page Audit   │
    │   - Implementation (7)           │                                                  │   Loopholes                      │
    │   - Sizing Concept (8)           │                                                  │ • Fix M7 Saturation Paradox      │
    │ • 40 Marks: Lab System Project   │                                                  │ • Reconcile Timing Budget        │
    │   - Transient Functionality (10) │                                                  │ • Active Phase Tuning (<1° error)│
    │   - Power Calculation (5)        │                                                  │ • Active PMOS Loads (>3.0 GHz)   │
    │   - Delay Calculation (5)        │                                                  │ • Fair Core-Area FoM Benchmark   │
    │   - PDP Calculation (5)          │                                                  │ • Complete Publication IEEE Draft│
    │   - PVT Corner Analysis (5)      │                                                  └──────────────────────────────────┘
    │   - Physical IC Layout (5)       │
    │   - Academic Lab Report (5)      │
    └──────────────────────────────────┘
```

---

### TECHNICAL CIRCUIT SPECIFICATIONS (BASELINE)

* **Source Reference:** Kuo et al., *"A Compact Multiphase Divide-by-Two CMOS Frequency Divider"*, IEEE LMWT, May 2025.
* **Technology:** 180nm CMOS process models, $V_{DD} = 1.8\text{ V}$.
* **Core Architecture:**
  - 4 cascading differential D-latches (Latch1, Latch2, Latch3, Latch4) forming a closed loop with alternate cross-connections:
    $$Q_{1b} \to D_2,\quad Q_2 \to D_3,\quad Q_{3b} \to D_4,\quad Q_4 \to D_{1b}$$
  - Differential input clocks: `CK` and `CKb` (operating range $100\text{ MHz}$ to $1.4\text{ GHz}$).
  - Outputs: 8 multiphase taps ($f_0, f_{45}, f_{90}, f_{135}, f_{180}, f_{225}, f_{270}, f_{315}$) at divided frequency ($50\text{ MHz}$ to $700\text{ MHz}$).
* **Transistor Sizing per Latch:**
  - Differential sampling pair ($M_1, M_2$): $W = 0.9\ \mu\text{m}, L = 0.18\ \mu\text{m}$.
  - Positive clock switch ($M_5$): $W = 0.9\ \mu\text{m}, L = 0.18\ \mu\text{m}$.
  - Cross-coupled hold pair ($M_3, M_4$): $W = 0.9\ \mu\text{m}, L = 0.18\ \mu\text{m}$.
  - Negative clock switch ($M_6$): $W = 0.9\ \mu\text{m}, L = 0.18\ \mu\text{m}$.
  - Current source ($M_7$): biased in saturation, $W = 1.8\ \mu\text{m}, L = 0.36\ \mu\text{m}$.
  - Pull-up resistors: $R_1 = R_2 = 1.5\text{ k}\Omega$ (satisfying $R_{load} = R_{on}/2$ for Elmore delay matching).
* **Sizing Concept Math:**
  $$t_{pdf} = (8C)(R/2) = 4RC$$
  $$t_{pdr} = (8C)(R_1) = (8C)(R/2) = 4RC \implies t_{pdr} = t_{pdf}$$

---

### TRACK B: LOOPHOLES TO EXPLOIT FOR THE V2 PAPER
Derived from the audit report (`https://multiphase-divider-report.balchaparshu.workers.dev/#overview`):
1. **Loophole 1 (Timing Budget Inconsistency):** Reconcile $T_{CK} > 4T_d$ (settling bound) with $T_{CK} \approx 8T_d$ (uniform $45^\circ$ spacing) by implementing balanced symmetrical stage delay.
2. **Loophole 2 (Phase Deviation under Load):** The baseline open-loop design fails strict phase spacing under unequal parasitic load. Implement an **Active Phase-Alignment / Tuning Cell** to guarantee phase error $< 1.0^\circ$.
3. **Loophole 3 (M7 Saturation Paradox):** Fix the grounded node-$b$ triode-region flaw by implementing a **Regulated Cascode Current Mirror** with explicit gate biasing, eliminating static hold leakage.
4. **Loophole 4 (Passive Resistor Limit):** Replace passive poly resistors with **Active Symmetric PMOS Loads**, expanding maximum frequency from $1.4\text{ GHz}$ to $> 3.0\text{ GHz}$ while saving $40\%$ silicon area.
5. **Loophole 5 (FoM Transparency):** Publish true Core-Area FoM alongside Die-Area FoM and include phase accuracy in the benchmarking comparison table.

---

### EXECUTION ROADMAP & MILESTONES

#### Milestone 1: Baseline Architecture & SPICE Netlisting
- Create directory structure:
  ```bash
  mkdir -p spice/models scripts results layout report paper .trash
  ```
- Obtain/generate standard 180nm / BSIM4 model file: `spice/models/cmos180.mod` (with NMOS and PMOS typical, fast, and slow models).
- Create `spice/divider_baseline.cir`:
  - Complete 4-latch subcircuit (`X_LATCH1` to `X_LATCH4`).
  - Tail bias, $V_{DD} = 1.8\text{ V}$, input clock sources at $1.4\text{ GHz}$ (`CK` and `CKb` with 50 ps rise/fall times).
- Run ngspice in batch mode:
  ```bash
  ngspice -b -r results/baseline_tran.raw spice/divider_baseline.cir
  ```
- **Verification Gate 1:** Output divides frequency by 2 (input 1.4 GHz $\to$ output 700 MHz).
- **Git Sync:** `git add . && git commit -m "feat(m1): baseline spice netlist and functional transient run" && git push origin main`

#### Milestone 2: Waveform Extraction, Phase Spacing & Rubric Metrics
- Build `scripts/analyze_waveform.py`:
  - Parse `results/baseline_tran.raw` (or exported CSV).
  - Plot high-resolution publication-quality PNGs in `results/plots/`:
    - `8_phase_transient.png`: Overlaid 8 phases with color coding.
    - `phase_difference_histogram.png`: Measured $\Delta \phi$ between adjacent channels vs ideal $45.0^\circ$.
  - Compute Average Power: $P_{avg} = V_{DD} \times I_{avg}$ (compare to paper's $2.34\text{ mW}$).
  - Compute Propagation Delay: $T_d$ (clock-to-Q 50% crossing delay).
  - Compute Power-Delay Product: $\text{PDP} = P_{avg} \times T_d$ (fJ).
  - Save all metrics into `results/metrics_baseline.json`.
- **Verification Gate 2:** All 8 phases present; Power, Delay, and PDP mathematically verified and saved in JSON.
- **Git Sync:** `git add . && git commit -m "feat(m2): waveform analysis, 8-phase plots, power and PDP calculation" && git push origin main`

#### Milestone 3: Automated PVT Corner Sweep
- Build `scripts/run_pvt_sweep.py`:
  - **Process Corners:** Typical-Typical (TT), Fast-Fast (FF), Slow-Slow (SS).
  - **Voltages:** $1.62\text{ V}$ ($-10\%$), $1.80\text{ V}$ (nominal), $1.98\text{ V}$ ($+10\%$).
  - **Temperatures:** $-40^\circ\text{C}, 27^\circ\text{C}, 85^\circ\text{C}, 125^\circ\text{C}$.
  - Total combinations: $\ge 9$ PVT corners.
  - Automatically extract frequency lock, phase error, power, and delay for each corner.
  - Export `results/pvt_summary_table.csv` and generate `results/plots/pvt_delay_power.png`.
- **Verification Gate 3:** Full PVT matrix generated with zero simulation failures; divider functions across corners.
- **Git Sync:** `git add . && git commit -m "feat(m3): comprehensive PVT corner analysis and summary table" && git push origin main`

#### Milestone 4: Physical Transistor Layout (Magic & KLayout)
- In `layout/`:
  - Implement Magic layout script `layout/generate_latch_layout.tcl`:
    - Draw NMOS active diffusions, polysilicon gates, metal-1 contacts.
    - Implement the paper's 2-finger common-centroid configuration for $(M_1, M_2)$ and $(M_3, M_4)$.
    - Place symmetric resistive loads and routing channels.
  - Execute Magic DRC check via command line:
    ```bash
    magic -dnull -noconsole layout/generate_latch_layout.tcl
    ```
  - Export GDSII layout `layout/divider_core.gds` and visual layout screenshot `results/plots/layout_view.png` using KLayout Python API (`klayout.db`).
- **Verification Gate 4:** Zero DRC violations in core latch cell; GDSII successfully generated.
- **Git Sync:** `git add . && git commit -m "feat(m4): physical transistor layout, DRC verification and GDS export" && git push origin main`

#### Milestone 5: Track B — Next-Gen Divider V2 Implementation
- Create `spice/divider_v2_enhanced.cir`:
  - Replace M7 with **Regulated Cascode Current Mirror** ($M_{7A}, M_{7B}, M_{casc}$) with bias generator.
  - Implement **Active Symmetric PMOS Loads** ($M_{L1}, M_{L2}$) with cross-coupled negative-conductance booster.
  - Add **Fine Phase-Tuning Varactors / Interpolators** on inter-latch nodes.
- Run transient, power, and frequency sweep from $100\text{ MHz}$ to $3.2\text{ GHz}$.
- Run Python analysis `scripts/compare_v1_vs_v2.py`:
  - Generates `results/plots/v1_vs_v2_comparison.png` showing maximum operating frequency, phase accuracy ($<0.8^\circ$ error), and FoM improvement.
  - Generates `results/v2_fom_table.csv` benchmarked against Table I of the IEEE paper.
- **Verification Gate 5:** V2 achieves $>2.5\text{ GHz}$ maximum frequency and tighter phase alignment than baseline.
- **Git Sync:** `git add . && git commit -m "feat(m5): v2 enhanced divider with cascode tail, active loads, and phase alignment" && git push origin main`

#### Milestone 6: Academic Report Generation (55 Marks Rubrics)
- Build `scripts/generate_academic_report.py`:
  - Compiles `report/23ECE302_Theory_Assignment.pdf` (or Markdown):
    - Detailed transistor schematic diagram.
    - Full mathematical derivation of Elmore delay ($t_{pdr} = t_{pdf} = 4RC$).
    - Transistor sizing table ($W/L$ for $M_1$ through $M_7$).
  - Compiles `report/23ECE383_System_Design_Project_Report.pdf` (or Markdown):
    - Section 1: Abstract & Design Specifications.
    - Section 2: Transient Analysis & 8-Phase Functionality (Plots + Discussion).
    - Section 3: Power Calculation ($P_{avg}$ breakdown).
    - Section 4: Delay Calculation & Power-Delay Product (PDP).
    - Section 5: PVT Corner Analysis (Tables and Graphs).
    - Section 6: Physical Layout, DRC & LVS Documentation.
    - Section 7: Conclusion & Rubric Compliance Matrix.
- **Verification Gate 6:** Reports address every parameter in the instructor's evaluation table.
- **Git Sync:** `git add . && git commit -m "feat(m6): complete academic assignment and lab system project reports" && git push origin main`

#### Milestone 7: IEEE Letter Manuscript Draft (Publication Ready)
- Draft `paper/manuscript_v2.md` following IEEE Transactions/Letters format:
  - Title: *"An Enhanced High-Frequency Multiphase Divide-by-Two CMOS Frequency Divider with Active Phase-Alignment and Regulated Current Mirror"*
  - Abstract & Introduction citing Kuo et al. (IEEE LMWT 2025).
  - Section II: Circuit Architecture, Cascode Biasing, and Active Loads.
  - Section III: Analysis of Timing Budget Reconciliation & Phase Accuracy.
  - Section IV: Simulation Results & Comprehensive PVT Benchmark.
  - Section V: Performance Comparison Table (FoM) & Conclusion.
- **Verification Gate 7:** Complete, submission-ready manuscript with formatted tables, equation numbering, and figure references.
- **Git Sync:** `git add . && git commit -m "feat(m7): complete IEEE letter manuscript draft for v2 divider" && git push origin main`

---

### AUTONOMOUS VERIFICATION CHECKLIST (EXIT CONDITION)
Do not declare completion until every checkbox is verified:
- [ ] `spice/models/cmos180.mod` functional and calibrated.
- [ ] Baseline 1.4 GHz $\to$ 700 MHz division verified in ngspice.
- [ ] 8-phase output waveforms extracted and plotted in `results/plots/`.
- [ ] Average power, delay, and PDP calculated and saved in `results/metrics_baseline.json`.
- [ ] PVT sweep across 9+ corners completed with `results/pvt_summary_table.csv`.
- [ ] Magic layout generated with clean DRC in `layout/divider_core.gds`.
- [ ] V2 architecture implemented, solving M7 saturation and extending $F_{max} > 2.5\text{ GHz}$.
- [ ] 23ECE302 Assignment & 23ECE383 System Project reports finalized in `report/`.
- [ ] IEEE Letter manuscript draft finalized in `paper/manuscript_v2.md`.
- [ ] All commits pushed to GitHub repository `origin main`.
- [ ] Zero deleted files; all discarded materials safely moved to `.trash/`.
