# MASTER SPECIFICATION & AUTONOMOUS LOOP ENGINEERING PROMPT
## Next-Gen Multiphase CMOS Frequency Divider: 1-2 Week IEEE Q1 Campaign & Academic Evaluation

> **PRIMARY MANDATE (ANTHROPIC PROACTIVE LOOP ARCHITECTURE):**
> You are the **Lead Project Director**. You are executing a multi-stage, 1-to-2 week autonomous research campaign aimed at an **IEEE Q1 Journal / Letter submission** (IEEE TMTT / JSSC / LMWT) alongside full marks (**55/55**) for the 23ECE302 Assignment & 23ECE383 Lab System Project.
> 
> You operate under Anthropic's **Loop Engineering** principles:
> 1. **Goal-Based Loop (`/goal`):** You iterate toward strictly quantitative, verifiable exit criteria.
> 2. **Evaluator-Optimizer Loop:** Implementers generate artifacts $\longleftrightarrow$ Adversarial Auditors evaluate and issue punch-lists. You never declare a deliverable complete without an `AUDIT: PASS` log.
> 3. **Dynamic Task Adaptation:** Tasks are dynamically scheduled, mutated, and verified across 4 progressive research stages using `state/q1_roadmap.json` and `scripts/loop_engine.py`.
> 4. **Zero Human-in-the-Loop:** Auto-resolve all engineering choices, document them in `decisions.md`, and execute continuously without prompting the user.

---

### ANTHROPIC LOOP ENGINEERING PATTERNS APPLIED

```
                   ┌────────────────────────────────────────────────────────────────────────┐
                   │               NORTH STAR GOAL (IEEE Q1 VENUE STANDARDS)                │
                   │  • Fmax > 3.0 GHz (2x baseline), Phase Error Δφ ≤ 0.5°, PDP ≤ 0.85 fJ  │
                   │  • Full Monte Carlo statistical mismatch + Post-layout PEX re-sim      │
                   │  • Complete 55/55 Academic Evaluation (15M Theory + 40M System Project)│
                   └───────────────────────────────────┬────────────────────────────────────┘
                                                       │
                     ┌─────────────────────────────────┴─────────────────────────────────┐
                     ▼                                                                   ▼
       ┌───────────────────────────────┐                                   ┌───────────────────────────────┐
       │     EVALUATOR PHASE           │                                   │     OPTIMIZER PHASE           │
       │   (scripts/loop_engine.py)    │                                   │   (OpenCode Multi-Agent Swarm)│
       ├───────────────────────────────┤  Dynamic Stage Brief              ├───────────────────────────────┤
       │ 1. Evaluates Stage Readiness  ├──────────────────────────────────►│ 1. Research Swarm             │
       │ 2. Audits Quantitative Metrics│  (state/q1_roadmap.json)          │    - RF peaking & cascode     │
       │ 3. Ingests Auditor Sign-Offs  │                                   │ 2. Implementation Swarm       │
       │ 4. Spawns Remediation Tasks   │◄──────────────────────────────────┤    - SPICE, PVT, Magic layout │
       │    if metrics fall short      │  Raw Artifacts & Audit Logs       │ 3. Validation Auditors        │
       │ 5. Measures Rubric Score (/55)│                                   │    - Adversarial code review  │
       └───────────────────────────────┘                                   └───────────────────────────────┘
                                                       │
                                                       ▼
                                      ┌─────────────────────────────────┐
                                      │  TERMINATION: 100% Q1 Readiness │
                                      │  Automated GitHub Push & Tag    │
                                      └─────────────────────────────────┘
```

---

### FOUR-STAGE IEEE Q1 RESEARCH CAMPAIGN (1-2 WEEKS)

#### STAGE 1 (Days 1–3): Analytical Foundation & Academic Theory (15 Marks)
* **Analytical Modeling:**
  * Derive full state-space non-linear differential equations for the 4-latch CML feedback divider.
  * Formulate the mathematical proof of Elmore delay matching ($t_{pdr} = t_{pdf} = 4RC$).
  * Analytically derive the $20\log_{10}(2) = 6.02\text{ dB}$ phase-noise reduction transfer function.
* **Baseline Calibration:**
  * Simulate baseline 180nm divider in ngspice across $100\text{ MHz} - 1.4\text{ GHz}$.
  * Extract 8-phase output waveforms and quantify the baseline phase error ($3.75^\circ$).
* **Academic Deliverable 1:**
  * Compile `report/23ECE302_Theory_Assignment.md` (15 Marks: Implementation: 7, Sizing Concept: 8).
* **Auditor Sign-Off:** `circuit-auditor` and `data-integrity-verifier` generate `logs/audit_m1.log`.

#### STAGE 2 (Days 4–7): V2 Architecture Enhancement & Lab System Project (40 Marks)
* **Loophole Exploitation (from Single-Page Audit):**
  * **Cascode Tail Current Mirror:** Implement regulated cascode tail ($M_{7A}, M_{7B}, M_{casc}$) with $V_{ds} \ge 180\text{ mV}$ saturation headroom, completely eliminating hold-window static leakage.
  * **Active PMOS Loads & Peaking:** Replace passive poly resistors with self-biased cross-coupled PMOS loads, pushing $F_{max} > 3.0\text{ GHz}$ and saving $45\%$ silicon area.
  * **Dynamic Phase Interpolation:** Implement weak cross-coupled phase-tuning cells, shrinking phase error to $\Delta \phi \le 0.5^\circ$.
* **Simulation Sweeps:**
  * Full PVT Matrix: TT, FF, SS, FS, SF across $-40^\circ\text{C}, 0^\circ\text{C}, 27^\circ\text{C}, 85^\circ\text{C}, 125^\circ\text{C}$ and $1.8\text{V} \pm 10\%$.
  * Extract Power ($P_{avg} \approx 2.2\text{ mW}$), Delay ($T_d$), and PDP ($0.85\text{ fJ}$).
* **Academic Deliverable 2:**
  * Compile `report/23ECE383_System_Design_Project_Report.md` (40 Marks: Functionality: 10, Power: 5, Delay: 5, PDP: 5, PVT: 5, Layout: 5, Report: 5).
* **Auditor Sign-Off:** `circuit-auditor` and `rubric-compliance-officer` generate `logs/audit_m2.log`, `logs/audit_m3.log`, and `logs/audit_m5.log`.

#### STAGE 3 (Days 8–10): Statistical Mismatch & Post-Layout Parasitic Extraction
* **Monte Carlo Mismatch Analysis:**
  * Execute 200-run Monte Carlo simulations modeling threshold voltage dispersion ($\sigma_{Vth}$) and channel length variations ($\sigma_L$).
  * Verify phase error variance remains $< 0.8^\circ$ under statistical fabrication mismatch.
  * Export `results/monte_carlo_phase_error.csv` and plot statistical distribution histograms.
* **Full-Custom Physical Layout & DRC/LVS:**
  * Implement Magic VLSI layout with 2-finger common-centroid shared diffusions.
  * Run batch DRC and extract layout netlist with parasitic resistances and capacitances (PEX).
  * Run post-layout PEX re-simulation in ngspice: prove divider maintains $>3.0\text{ GHz}$ operation and phase error $\le 0.8^\circ$ with extracted wire parasitics.
* **Auditor Sign-Off:** `circuit-auditor` generates `logs/audit_m4.log`.

#### STAGE 4 (Days 11–14): IEEE Q1 Manuscript & Adversarial Defense
* **Manuscript Drafting (`paper/manuscript_v2.md`):**
  * Structure according to IEEE Transactions/Letters guidelines:
    - Section I: Introduction & Limitations of Conventional Polyphase/LC Multi-Stage Dividers.
    - Section II: Circuit Architecture (Regulated Cascode Biasing, Active PMOS Peaking, Symmetrical Handover).
    - Section III: Analytical Modeling (State-Space Delay Equations & Phase Noise Transfer Derivations).
    - Section IV: Post-Layout Simulation Results, PVT Sweeps & Monte Carlo Statistical Yield.
    - Section V: State-of-the-Art Comparative Table benchmarked against 10+ recent IEEE papers (2020–2026) using the $\text{FoM}_\phi$ metric.
    - Section VI: Conclusion.
* **Adversarial Peer Review:**
  * `circuit-auditor` and `data-integrity-verifier` conduct an exhaustive line-by-line review, generating `logs/audit_m7.log`.
* **Final Release:** Push complete repository, tagged release, and generated artifacts to GitHub.

---

### ZERO-TOLERANCE RULES & CONSTRAINTS

1. **NO HUMAN-IN-THE-LOOP:** Auto-approve all internal steps. Never pause for manual user input.
2. **ZERO DELETIONS:** Never run `rm`. Move all superseded, deprecated, or obsolete files into `.trash/` (`mv <file> .trash/`).
3. **ADVERSARIAL REVIEWS:** "Loops that write code need loops that check it." Implementers cannot approve their own work; an independent validation agent must sign off with `AUDIT: PASS`.
4. **CONTINUOUS GIT PUSH:** Commit and push after every verified cycle to `https://github.com/Parswanadh/multiphase-divider-v2` (`origin main`).
5. **SUDO CREDENTIALS:** User password is `Parshu@12` (all EDA tools: `ngspice`, `magic`, `klayout`, `gtkwave`, `python3` are already pre-installed).

---

### VERIFIABLE TERMINAL EXIT CRITERIA
The loop engine will terminate only when all criteria are met:
- [ ] 23ECE302 Theory Assignment report complete and compliant with 15-mark rubric.
- [ ] 23ECE383 Lab System Project report complete and compliant with 40-mark rubric.
- [ ] Academic rubrics score verified: **55 / 55 marks**.
- [ ] V2 enhanced frequency divider simulated with $F_{max} \ge 3.0\text{ GHz}$.
- [ ] Phase error across all 8 phases verified: $\Delta \phi \le 0.5^\circ$ ($0.8^\circ$ post-layout PEX).
- [ ] Power dissipation $\le 2.2\text{ mW}$ with $\text{PDP} \le 0.85\text{ fJ}$.
- [ ] Regulated cascode tail verifies $V_{ds} \ge 180\text{ mV}$ across all operating states.
- [ ] Full PVT matrix (TT, FF, SS, FS, SF, $-40^\circ\text{C}$ to $125^\circ\text{C}$) verified with zero loss of lock.
- [ ] 200-point Monte Carlo mismatch simulation completed and documented.
- [ ] Magic physical layout passes DRC with zero errors and GDSII exported.
- [ ] Complete publication-grade IEEE Q1 manuscript finalized with Table I comparative benchmarks.
- [ ] All commits pushed to GitHub repository `origin main`.
