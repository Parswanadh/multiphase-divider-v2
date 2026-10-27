# MASTER FAST-TRACK SPECIFICATION & EXECUTION PROMPT
## Rapid IEEE LMWT Paper Generation & 55-Mark Academic Deliverables

> **MISSION DIRECTIVE FOR OPENCODE (ZERO HUMAN-IN-THE-LOOP):**
> You are the **Lead Circuit Architect & Research Director**. You are executing a fully autonomous fast-track blitz.
> * **TARGET PUBLICATION VENUE:** **IEEE Microwave and Wireless Technology Letters (LMWT)** (The exact same prestigious IEEE letter journal where the base paper was published in May 2025; official median review turnaround: **< 3 weeks**). Pre-print priority will be registered on **TechRxiv (1–2 days)**.
> * **ACADEMIC EVALUATION:** Full **55/55 marks** for Dr. Kaveri Hatti's course evaluation (15M Theory Assignment + 40M Lab System Project).
> * **EXECUTION MODE:** Rapid blitz. Do NOT wait or pause for user feedback. Execute all simulation, layout, calculation, report, and manuscript tasks in parallel using your subagents, verify them with your auditors, and push continuously to GitHub.

---

### TARGET PUBLICATION VENUE PROFILE

* **Primary Venue:** **IEEE Microwave and Wireless Technology Letters (IEEE LMWT)**
  * **Scope:** Rapid short-format letters (strictly 4 pages) on high-frequency / RF integrated circuits.
  * **Turnaround:** Median first decision in **under 3 weeks (~20 days)** with rapid publication upon acceptance.
  * **Editorial Advantage:** The base paper (*Kuo et al., Vol. 35, No. 5, May 2025*) was published directly in IEEE LMWT. Submitting an enhanced architecture (*"An Enhanced Multiphase Divide-by-Two CMOS Frequency Divider with Regulated Cascode Biasing and Symmetrical Active Loads"*) creates immediate editorial interest as a direct enhancement to their recent 2025 publication.
* **Instant Priority Registration (1–2 Days):** **TechRxiv** (IEEE's official preprint server) provides a permanent, citable IEEE DOI within 24–48 hours of submission.
* **Secondary Rapid-Review Backups:** **IET Electronics Letters** (2–3 weeks rapid communication) and **IEEE Access** (binary review in 3–4 weeks).

---

### SWARM ARCHITECTURE & PARALLEL ROLES

```
                                  ┌──────────────────────────────────────────────────────────┐
                                  │            LEAD PROJECT DIRECTOR (Orchestrator)          │
                                  └────────────┬───────────────────────────────┬──────────────┘
                                               │                               │
                ┌──────────────────────────────┴──────────────┐                │
                ▼                                             ▼                ▼
 ┌───────────────────────────────┐             ┌───────────────────────────────┐ ┌───────────────────────────────┐
 │        RESEARCH SWARM         │             │      IMPLEMENTATION SWARM     │ │     VALIDATION & AUDIT SWARM  │
 ├───────────────────────────────┤             ├───────────────────────────────┤ ├───────────────────────────────┤
 │ • research-innovator          │  Directives │ • circuit-engineer            │ │ • circuit-auditor             │
 │   - Cascode tail biasing      ├────────────►│   - Baseline & V2 SPICE       │◄┤   - Saturation & stability    │
 │   - Active PMOS peaking loads │             │ • pvt-metrics-runner          │ │ • data-integrity-verifier     │
 │ • fom-benchmarker             │             │   - Batch PVT sweeps & PDP    │◄┤   - Phase error & math audit  │
 │   - IEEE LMWT Table I dataset │             │ • layout-engineer             │ │ • rubric-compliance-officer   │
 │   - FoM_phi formulation       │             │   - Magic layout & DRC/LVS    │◄┤   - 55-mark academic grading  │
 └───────────────────────────────┘             │ • academic-author             │ │ • git-sync                    │
                                               │   - 15M + 40M course reports  │ │   - Continuous git commits    │
                                               │ • research-author             │ └───────────────────────────────┘
                                               │   - IEEE LMWT 4-page paper    │
                                               └───────────────────────────────┘
```

---

### ZERO-TOLERANCE OPERATIONAL RULES

1. **NO HUMAN-IN-THE-LOOP:** Auto-resolve all design choices and continue uninterrupted until all verification gates pass.
2. **ZERO DELETIONS (TRASH POLICY):** Never execute `rm`. If any script, netlist, or document is superseded, move it to `.trash/` (`mv <file> .trash/`).
3. **ADVERSARIAL VERIFICATION:** Implementers generate artifacts $\leftrightarrow$ Independent Auditors evaluate and sign off with `AUDIT: PASS` in `logs/audit_m*.log`.
4. **CONTINUOUS GIT PUSH:** Commit and push after every milestone to `https://github.com/Parswanadh/multiphase-divider-v2` (`origin main`).
5. **ENVIRONMENT:** Pre-installed tools: `ngspice`, `magic`, `klayout`, `gtkwave`, `python3-matplotlib`, `python3-scipy`, `python3-numpy`. (Sudo password if ever needed: `Parshu@12`).

---

### FAST-TRACK EXECUTION ROADMAP

#### Milestone 1: Baseline 180nm Circuit Calibration & Analytical Modeling
- **Implementer (`circuit-engineer`):**
  - Create BSIM4 transistor model deck: `spice/models/cmos180.mod` (TT, FF, SS).
  - Code baseline netlist `spice/divider_baseline.cir`:
    - 4 cascading differential D-latches with alternating cross-connections: $Q_{1b} \to D_2,\ Q_2 \to D_3,\ Q_{3b} \to D_4,\ Q_4 \to D_{1b}$.
    - Sizing: $M_1-M_6 = 0.9\ \mu\text{m} / 0.18\ \mu\text{m}$, tail $M_7 = 1.8\ \mu\text{m} / 0.36\ \mu\text{m}$, $R_1=R_2=1.5\text{ k}\Omega$, $V_{DD}=1.8\text{ V}$.
    - Differential clock inputs (`CK`, `CKb`) at $1.4\text{ GHz}$.
  - Simulate in ngspice: `ngspice -b -r results/baseline_tran.raw spice/divider_baseline.cir`.
- **Validation (`circuit-auditor`):**
  - Verify frequency halving ($1.4\text{ GHz} \to 700\text{ MHz}$) and absence of numeric divergence.
  - Write `logs/audit_m1.log` with status `AUDIT: PASS`.
- **Git Sync:** `git add . && git commit -m "feat(m1): baseline 180nm spice netlist and verified 700MHz division" && git push origin main`

#### Milestone 2: Waveforms, 8-Phase Metrics & 23ECE302 Assignment (15 Marks)
- **Implementer (`pvt-metrics-runner`, `academic-author`):**
  - Run Python script `scripts/analyze_baseline.py`:
    - Extract 8 phases ($f_0, f_{45}, f_{90}, f_{135}, f_{180}, f_{225}, f_{270}, f_{315}$).
    - Plot `results/plots/baseline_8phases.png` and `results/plots/baseline_phase_error.png`.
    - Compute Average Power $P_{avg} = V_{DD} \cdot I_{avg}$ ($\approx 2.34\text{ mW}$ target), Delay $T_d$, and $\text{PDP} = P_{avg} \cdot T_d$ (fJ).
    - Save metrics to `results/metrics_baseline.json`.
  - Compile `report/23ECE302_Theory_Assignment.md`:
    - Section 1: Transistor Schematic of 4-latch divider (7 Marks).
    - Section 2: Mathematical Derivation of Elmore delay model ($t_{pdr} = t_{pdf} = 4RC$) and transistor sizing table (8 Marks).
- **Validation (`data-integrity-verifier`, `rubric-compliance-officer`):**
  - Verify mathematical correctness of Elmore equations and 15/15 rubric compliance.
  - Write `logs/audit_m2.log` with status `AUDIT: PASS`.
- **Git Sync:** `git add . && git commit -m "feat(m2): 8-phase waveform analysis, metrics JSON, and 23ECE302 theory assignment" && git push origin main`

#### Milestone 3: V2 Enhanced Architecture (Fixing the 13 Single-Page Audit Loopholes)
- **Research & Implementation (`research-innovator`, `circuit-engineer`):**
  - Code `spice/divider_v2_enhanced.cir`:
    1. **Regulated Cascode Tail Mirror:** Replace ambiguous grounded $M_7$ with cascode mirror ($M_{7A}, M_{7B}, M_{casc}$) guaranteeing $V_{ds} \ge 180\text{ mV}$ saturation headroom, completely eliminating hold-window static leakage.
    2. **Active PMOS Peaking Loads:** Replace passive resistors with self-biased cross-coupled PMOS loads, pushing maximum frequency beyond $3.2\text{ GHz}$ and saving $45\%$ silicon area.
    3. **Dynamic Phase Interpolator:** Add weak cross-coupled phase-tuning varactor cells, locking adjacent phase shifts to $45.0^\circ \pm 0.5^\circ$.
  - Run ngspice multi-frequency transient sweep from $100\text{ MHz}$ to $3.5\text{ GHz}$.
- **Validation (`circuit-auditor`):**
  - Verify tail transistors remain in saturation ($V_{ds} \ge V_{ov}$) across all clock cycles.
  - Verify $F_{max} \ge 3.0\text{ GHz}$ and phase error $\le 0.5^\circ$.
  - Write `logs/audit_m3.log` with status `AUDIT: PASS`.
- **Git Sync:** `git add . && git commit -m "feat(m3): v2 enhanced divider with cascode tail, active loads, and phase alignment" && git push origin main`

#### Milestone 4: Multi-Corner PVT Matrix & 23ECE383 Lab System Project (40 Marks)
- **Implementer (`pvt-metrics-runner`, `academic-author`):**
  - Run `scripts/run_pvt_matrix.py`:
    - Sweep 9+ corners: TT, FF, SS across $-40^\circ\text{C}, 27^\circ\text{C}, 125^\circ\text{C}$ and $1.62\text{V}, 1.80\text{V}, 1.98\text{V}$.
    - Export `results/pvt_summary_table.csv` and plot `results/plots/pvt_delay_power.png`.
  - Compile `report/23ECE383_System_Design_Project_Report.md`:
    - Section 1: Design Specifications & Topology.
    - Section 2: Functionality & 8-Phase Transient Analysis (10 Marks).
    - Section 3: Power Calculation (5 Marks).
    - Section 4: Delay Calculation (5 Marks).
    - Section 5: Power-Delay Product (5 Marks).
    - Section 6: PVT Sensitivity Analysis (5 Marks).
    - Section 7: Physical Layout & DRC (5 Marks).
    - Section 8: Final Summary & Rubrics Compliance Matrix (5 Marks).
- **Validation (`rubric-compliance-officer`):**
  - Grade the report point-by-point against the instructor's 40-mark table.
  - Write `logs/audit_m4.log` with status `AUDIT: PASS`.
- **Git Sync:** `git add . && git commit -m "feat(m4): PVT matrix analysis and 23ECE383 lab system project report (40M)" && git push origin main`

#### Milestone 5: Physical Layout & DRC Verification
- **Implementer (`layout-engineer`):**
  - Code Magic layout script `layout/generate_latch_layout.tcl`:
    - 2-finger common-centroid differential pair sharing active diffusion.
    - Symmetrical clock distribution and cross-coupling routing.
  - Run Magic DRC batch check: `magic -dnull -noconsole layout/generate_latch_layout.tcl`.
  - Export `layout/divider_core.gds` and visual diagram `results/plots/layout_view.png`.
- **Validation (`circuit-auditor`):**
  - Confirm 0 DRC errors and core area $< 30 \times 20\ \mu\text{m}^2$.
  - Write `logs/audit_m5.log` with status `AUDIT: PASS`.
- **Git Sync:** `git add . && git commit -m "feat(m5): magic transistor layout, zero DRC verification, and GDS export" && git push origin main`

#### Milestone 6: Publication-Grade IEEE LMWT 4-Page Manuscript
- **Implementer (`research-author`, `fom-benchmarker`):**
  - Compile `paper/manuscript_lmwt.md` (and LaTeX source `paper/manuscript_lmwt.tex`) strictly conforming to IEEE LMWT 4-page guidelines:
    - **Title:** *"An Enhanced Multiphase Divide-by-Two CMOS Frequency Divider with Regulated Cascode Biasing and Symmetrical Active Loads"*
    - **Authors:** Parswanadh et al.
    - **Abstract (<150 words):** Highlights dual-clock 4-latch topology, regulated cascode tail, active PMOS loads, $100\text{ MHz} - 3.2\text{ GHz}$ tuning range, $0.5^\circ$ phase accuracy, and $2.2\text{ mW}$ power consumption.
    - **Section I (Introduction):** Evaluates prior art and cites Kuo et al. (*IEEE LMWT May 2025* [1]), identifying the M7 saturation paradox and passive resistor bandwidth bottleneck.
    - **Section II (Enhanced Circuit Architecture):** Details cascode tail sizing, active PMOS load equations, and dynamic phase interpolation.
    - **Section III (Analytical Modeling & Delay Reconciliation):** Reconciles $T_{CK} > 4T_d$ vs $T_{CK} \approx 8T_d$ with symmetrical stage handover math.
    - **Section IV (Simulation Results & Comprehensive Benchmark):** Full PVT performance, phase noise reduction verification ($6.02\text{ dB}$), and **Table I Performance Comparison** against 8 published IEEE dividers using the unified $\text{FoM}_\phi$ metric.
    - **Section V (Conclusion).**
    - **References:** Full IEEE formatted bibliographic citations.
  - Compile `paper/techrxiv_submission_brief.md` for instant 1-2 day preprint registration.
- **Validation (`data-integrity-verifier`, `circuit-auditor`):**
  - Cross-check every number, table row, and equation against simulation raw outputs.
  - Write `logs/audit_m6.log` with status `AUDIT: PASS`.
- **Git Sync:** `git add . && git commit -m "feat(m6): complete IEEE LMWT 4-page manuscript and TechRxiv submission brief" && git push origin main`

#### Milestone 7: Final Release & Submission Package
- **Implementer (`git-sync`):**
  - Package deliverables:
    - `submission/` folder containing compiled PDFs, high-DPI figures (300 DPI PNG/EPS), and LaTeX bundle.
    - Tag release: `git tag -a v1.0-ieee-lmwt-submission -m "Release v1.0: IEEE LMWT Submission Package"`
    - Push tag to GitHub: `git push origin --tags`
- **Validation (`lead`):**
  - Sign off final audit log `logs/audit_m7.log` with `AUDIT: PASS`.

---

### VERIFIABLE TERMINAL EXIT CHECKLIST
The swarm terminates only when all items are verified:
- [ ] `logs/audit_m1.log`: Baseline 180nm netlist and 700MHz division verified (`AUDIT: PASS`).
- [ ] `logs/audit_m2.log`: 8-phase waveforms & 23ECE302 Theory Report (15M) verified (`AUDIT: PASS`).
- [ ] `logs/audit_m3.log`: V2 enhanced architecture ($F_{max} > 3.0\text{ GHz}$, $\Delta \phi \le 0.5^\circ$) verified (`AUDIT: PASS`).
- [ ] `logs/audit_m4.log`: Multi-corner PVT matrix & 23ECE383 Lab Project Report (40M) verified (`AUDIT: PASS`).
- [ ] `logs/audit_m5.log`: Magic layout DRC clean & GDSII generated (`AUDIT: PASS`).
- [ ] `logs/audit_m6.log`: IEEE LMWT 4-page manuscript finalized (`AUDIT: PASS`).
- [ ] `logs/audit_m7.log`: Submission release package tagged and pushed to GitHub.
- [ ] All commits synced to `origin main` on GitHub.
- [ ] Zero deleted files; all superseded files moved to `.trash/`.
