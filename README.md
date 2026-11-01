# Multiphase Divide-by-Two CMOS Frequency Divider (Cadence GPDK045)

This repository contains the Cadence GPDK045 (45 nm CMOS) re-implementation of the compact 8-phase divide-by-two frequency divider by Kuo et al. (IEEE MWTL, May 2025). The circuit uses four differential D-latches in a ring with alternating clock connections to produce eight uniformly spaced clock phases at 1.0 V nominal supply. Schematics were constructed in Virtuoso with SKILL, transient and PVT sweeps were evaluated with Spectre and OCEAN, and layout placement was verified using Assura DRC.

## Stable Baseline

The v1.0 baseline is complete and frozen. Refer to [STABLE.md](STABLE.md) for details, checksums, and restoration commands.

- Git tag: `v1.0-stable`
- Git branch: `stable/v1`
- VM snapshot: `stable-v1` (VirtualBox VM `CadenceVM`, powered off)
- Report file: [report/gpdk045/System_Design_Project_Report_gpdk045.pdf](report/gpdk045/System_Design_Project_Report_gpdk045.pdf)

## Results

Metrics were simulated with Cadence Spectre at typical conditions (tt corner, 27 °C, VDD = 1.0 V) unless specified. Values are recorded in [report/gpdk045/report_data.json](report/gpdk045/report_data.json) and [results/gpdk045/final/analysis.json](results/gpdk045/final/analysis.json).

| Circuit | Input Freq. | Output Freq. | Power | Delay | PDP | Phase Error | PVT Pass Rate |
|---|---|---|---|---|---|---|---|
| Unsized baseline (m=1, R=8 kΩ) | 1.4 GHz | 700.0 MHz | 0.1375 mW | 62.21 ps | 8.557 fJ | 26.42° | Not swept |
| Design D (m=4, R=3 kΩ) | 1.4 GHz | 700.0 MHz | 0.5413 mW | 25.99 ps | 14.067 fJ | 38.46° | 41 / 45 (91.1%) |
| Design B (m=4, R=2 kΩ) | 6.0 GHz | 3000.0 MHz | 0.4929 mW | 27.94 ps | 13.768 fJ | 3.78° | 21 / 45 (46.7%) |
| Paper-rule circuit (m=1, R=1.15 kΩ) | 1.4 GHz | Fails (2799.8 MHz) | 0.1652 mW | Undefined | Undefined | Undefined | 0 / 1 (fails nominal) |

The paper sizing rule (R = Ron / 2 = 1.15 kΩ) fails to divide in 45 nm. The pull-down stack has three NMOS devices in series. Latch regeneration requires R >= 1.1 x 3Ron / m = 7.59 kΩ for m = 1.

## What Is and Is Not Done

- Layout is placement only for DLATCH and divider_core (2x2 cell array).
- Placement Assura DRC reports 21 errors across 3 rules (substrate stamps and Metal1 minimum area).
- No LVS-clean layout exists. Automatic routing finished 136 of 137 nets but caused 134 DRC errors and LVS mismatches.
- No extraction or post-layout simulation was done because the PDK copy lacks Assura RCX files.
- Virtuoso schCheck passes with zero errors. One warning remains on tb_divider because the voltage source instance and net are both named VDD.

## Repository Map

| Directory | Description |
|---|---|
| [cadence/](cadence/) | Virtuoso SKILL builders, OCEAN scripts, and Assura verification setups |
| [spectre/](spectre/) | Standalone Spectre netlist (`divider_gpdk45.scs`) for headless runs |
| [scripts/](scripts/) | Python scripts for data consolidation, waveform plotting, and report generation |
| [results/gpdk045/](results/gpdk045/) | Simulation measurements, raw logs, DRC/LVS reports, and analysis JSON |
| [report/gpdk045/](report/gpdk045/) | Report source data, generated figures, and final PDF/DOCX documents |
| [presentation/](presentation/) | Interactive HTML explainer and project glossary |
| [guide/](guide/) | Cadence GPDK045 student lab manual and walk-throughs |
| [vm/](vm/) | VirtualBox management scripts and VM setup documentation |
| [v2/](v2/) | Project planning documents, requirements, and second-phase roadmaps |
| [legacy/](legacy/) | Early 180 nm ngspice simulation decks and initial experiments |
| [reference/](reference/) | Local reference copies of papers and datasheets (local, git-ignored) |

## How to Reproduce

### Rebuild the Report

From the repository root on the host:

```bash
python3 scripts/make_report_data.py
```

This updates [report/gpdk045/report_data.json](report/gpdk045/report_data.json) from `results/gpdk045/final/` and compiles the final report PDF and DOCX.

### Cadence Simulation and Verification Flow

1. Start the VM:
   ```bash
   vm/start_vm_gui.sh
   ```
2. Start Virtuoso inside the guest:
   ```bash
   cd ~/cds_work && virtuoso &
   ```
3. Build schematics from SKILL:
   ```lisp
   load("cadence/skill/build_schematic_v2.il")
   ```
4. Run schematic-driven Spectre simulation via OCEAN:
   ```bash
   cd ~/cds_work && ocean -nograph < cadence/ocean/run_schematic_tb_param.ocn
   ```
5. Run standalone Spectre sweeps:
   ```bash
   cd ~/gpdk_run && ./run_gpdk045.sh . pvt
   ```
6. Run Assura DRC and LVS checks:
   ```bash
   cadence/skill/verify/run_verify.sh DLATCH drc
   cadence/skill/verify/run_verify.sh DLATCH lvs
   ```

### VM Lock Protocol and Concurrency

The Cadence VM runs CentOS 6.5 in VirtualBox without network sharing. Host scripts send guest commands through a virtual serial port (`/dev/ttyS0`) using `VBoxManage controlvm CadenceVM keyboardputstring`, and monitor `/home/parshu/vm/serial.txt` for completion tokens. Because there is only one virtual keyboard channel, simultaneous commands corrupt input. All host jobs must run under the lock:

```bash
flock /home/parshu/vm/vm.lock <command>
```

## Documents to Read

- [Final Project Report (PDF)](report/gpdk045/System_Design_Project_Report_gpdk045.pdf): comprehensive 24-page report with sizing analysis, circuit schematics, and PVT data.
- [Presentation Explainer](presentation/explainer.html): interactive web document detailing circuit operation, latch theory, and simulation results.
- [Project Glossary](presentation/glossary.html): glossary of design metrics, simulation parameters, and Cadence tools.
- [v2 Plan](v2/PLAN.md): engineering roadmap, stage gates, and decisions for the next project phase.

## v2 Direction

1. v2 focuses on a peer-reviewed letter on the 45 nm divider re-implementation and one measured enhancement.
2. The recommended path in [v2/PLAN.md](v2/PLAN.md) is a systematic sizing exploration rather than complex topology changes.
3. Every reported metric must trace directly to an automated, rerunnable Spectre or Assura artifact.
4. The early draft in [v2/legacy_draft/](v2/legacy_draft/) contains speculative, unmeasured numbers and is unverified.
5. Next steps will proceed only after deciding on the enhancement path, publication venue, and extraction files.

## Tools and Versions

- Cadence Virtuoso IC615 (version 6.1.5)
- Cadence Spectre Circuit Simulator (MMSIM 12.1)
- Cadence Assura Physical Verification (version 4.1)
- Cadence GPDK045 Process Design Kit (version 6.0)
- Oracle VirtualBox with CentOS 6.5 x86 guest (VM name `CadenceVM`)
- Python 3 with `numpy`, `matplotlib`, `python-docx`, and `Pillow`
- LibreOffice (used for PDF export)

## Licence and Credit

The frequency divider architecture is from:
Yue-Fang Kuo, Shih-Hung Lin, Bo-Yi Chen, and Liang-Chen Liu, "A Compact Multiphase Divide-by-Two CMOS Frequency Divider," *IEEE Microwave and Wireless Technology Letters*, vol. 35, no. 5, pp. 617-620, May 2025, doi: 10.1109/LMWT.2025.3528863.

The original paper PDF is copyrighted by IEEE and is not distributed in this repository.
