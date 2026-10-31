# Multiphase Divider v2: Cadence GPDK045 Implementation

Reproducible Cadence Virtuoso, Spectre, and Assura verification flow for the 8-phase divide-by-two frequency divider proposed by Kuo et al. (IEEE LMWT, May 2025), implemented in Cadence gpdk045 (45 nm CMOS).

## Headline Results

Simulated with Cadence Spectre in gpdk045 (typical-typical corner, 27 °C, VDD = 1.0 V). Values are read directly from `report/gpdk045/report_data.json` and `results/gpdk045/final/analysis.json`.

| Metric | Kuo et al. (180 nm) | Paper Sizing (45 nm) | Baseline U8k | Design D (Nominal) | Design B (6 GHz) |
|---|---|---|---|---|---|
| Topology | Unit (180 nm) | m=1, R=1.15 kΩ | m=1, R=8 kΩ | m=4, R=3 kΩ | m=4, R=2 kΩ |
| Input Clock ($f_{in}$) | 1.4 GHz | 1.4 GHz | 1.4 GHz | 1.4 GHz | 6.0 GHz |
| Output Clock ($f_{out}$) | 700 MHz | 2799.8 MHz (fail) | 700.0 MHz | 700.0 MHz | 3000.0 MHz |
| Supply Voltage (VDD) | 1.8 V | 1.0 V | 1.0 V | 1.0 V | 1.0 V |
| Output Swing (pk-pk) | - | 0.0153 V | 0.2289 V | 0.4344 V | 0.1349 V |
| Total Power | 2.34 mW | 0.1652 mW | 0.1375 mW | 0.5413 mW | 0.4929 mW |
| Delay (CK-to-Q) | - | n/a | 62.21 ps | 25.99 ps | 27.94 ps |
| Power-Delay Product | - | n/a | 8.557 fJ | 14.067 fJ | 13.768 fJ |
| Max Phase-Step Error | 3.75° | n/a | 26.42° | 38.46° | 3.78° |
| PVT Pass Rate | - | - | - | 41 / 45 corners | 21 / 45 corners |

*Direct application of the paper sizing rule ($R = R_{on}/2 = 1.15\text{ k}\Omega$) fails to divide in 45 nm because the three-stacked NMOS branch requires $R \ge 7.59\text{ k}\Omega$ for regenerative latching.*

## Repository Map

- `cadence/skill/`: Virtuoso SKILL scripts for schematic generation (`build_schematic_v2.il`) and layout placement (`build_layout_v2.il`).
- `cadence/skill/auto/`: Layout XL generation (`lxl_flow.il`) and Chip Assembly Router automation (`route_dlatch.il`).
- `cadence/skill/verify/`: Assura DRC and LVS automation script (`run_verify.sh`) and verification templates.
- `cadence/ocean/`: OCEAN scripts (`run_schematic_tb_param.ocn`) for schematic-driven Spectre runs.
- `cadence/vm/`: Guest-side standalone Spectre sweep script (`run_gpdk045.sh`) and measurement extraction (`measure_guest.py`).
- `spectre/`: Standalone Spectre netlist (`divider_gpdk45.scs`) for headless simulation.
- `scripts/`: Data consolidation, plotting, and report generation (`make_report_data.py`, `build_academic_docx.py`).
- `results/gpdk045/`: Raw logs, DRC/LVS error reports, and processed TSV/JSON metrics (`final/analysis.json`).
- `report/gpdk045/`: Structured report data (`report_data.json`), figures, and compiled PDF/DOCX reports.

## Cadence Tool Flow

1. **Virtuoso Schematic Generation (SKILL)**
   - Invocation: `virtuoso -nograph -replay cadence/skill/build_schematic_v2.il` (executes `buildAll()`)
   - Produces: `divider_lib` views `DLATCH` (schematic, symbol), `divider_core` (schematic, symbol), and `tb_divider` (schematic). Verifications saved to `results/gpdk045/core_connectivity_virtuoso.txt` and `results/gpdk045/virtuoso_dlatch_params_designD.txt`.
2. **Schematic-Driven Simulation (OCEAN / Spectre)**
   - Command: `cd ~/cds_work && ocean -nograph < cadence/ocean/run_schematic_tb_param.ocn`
   - Produces: Virtuoso netlist `results/gpdk045/virtuoso_netlist_tb_divider.scs` and simulation measurements `results/gpdk045/ocean_schematic_run_1p4GHz_D.txt` (700 MHz division, 0.455 mW power, 26.66 ps delay).
3. **Standalone Spectre PVT Sweeps**
   - Command: `bash cadence/vm/run_gpdk045.sh <workdir> pvt` (with parameters `FIN=1.4G RL=3k VB=1.0 CL=10f MULT=4`)
   - Produces: `results/gpdk045/final/D_1p4.tsv`, `results/gpdk045/final/pvt_D.tsv`, and `results/gpdk045/final/analysis.json`.
4. **Layout XL Generate-from-Source**
   - Invocation: `virtuoso -nograph -replay cadence/skill/auto/lxl_flow.il` (calls `lxGenFromSource`)
   - Produces: Connectivity-bound view `DLATCH/layout_lxl` (28 NMOS instances, 9 pins); logs saved in `results/gpdk045/lxl_flow_log.txt` and `results/gpdk045/lxl_dlatch_readback.txt`.
5. **Chip Assembly Router (vcar)**
   - Invocation: Function `routeDlatchMain()` in `cadence/skill/auto/route_dlatch.il` (invokes standalone `vcar` with `groute`, `troute`, `route`, `save_oa as layout_routed`)
   - Produces: View `DLATCH/layout_routed`; log saved to `results/gpdk045/route_dlatch_log.txt` (136 of 137 connections routed, 1 unroute on net `xs`).
6. **Physical Verification (Assura DRC and LVS)**
   - Commands:
     - Baseline placement DRC: `cadence/skill/verify/run_verify.sh DLATCH drc`
     - Baseline placement LVS: `cadence/skill/verify/run_verify.sh DLATCH lvs`
     - Auto-routed layout DRC: `VIEW=layout_routed RUNTAG=_routed cadence/skill/verify/run_verify.sh DLATCH drc`
     - Auto-routed layout LVS: `VIEW=layout_routed RUNTAG=_routed cadence/skill/verify/run_verify.sh DLATCH lvs`
   - Produces: `results/gpdk045/assura_drc_dlatch_summary.txt` (placement DRC), `results/gpdk045/assura_lvs_dlatch_baseline.txt` (placement LVS), `results/gpdk045/assura_drc_dlatch_routed.txt` (routed DRC), and `results/gpdk045/assura_lvs_dlatch_routed.txt` (routed LVS).

## VM Automation Architecture

Cadence tools execute inside a headless VirtualBox virtual machine (`CadenceVM`, CentOS 6.5) driven from the host environment:

- **Virtual Serial Port (`vmx.sh`)**: Host sends guest commands via `VBoxManage controlvm CadenceVM keyboardputstring`, redirecting output to `/dev/ttyS0` with completion marker `echo __DONE_$n > /dev/ttyS0`. Host monitors `/home/parshu/vm/serial.txt` until the token appears.
- **ISO Transfer (`skill_run.sh`, `run_verify.sh`)**: Host generates temporary ISO9660 file systems containing replay scripts and RSF templates via `xorriso -as mkisofs`, attaches the medium via `VBoxManage storageattach`, and guest mounts `/dev/sr0` at `/mnt/r` read-only.
- **Flock Lock**: Concurrency across host processes is serialized using `flock /home/parshu/vm/vm.lock`.

## Known Limitations

- **Layout Placement Only**: The primary layout (`DLATCH/layout`, `divider_core/layout`) contains placed PCells and pins without intra-cell metal routing. Assura DRC on this placement yields 21 errors across 3 rules (substrate stamp and Metal1 minimum area).
- **Auto-Routed Attempt**: The Chip Assembly Router attempt on `DLATCH/layout_lxl` leaves 1 open connection (net `xs`) and produces 134 DRC errors across 17 rules (primarily latchup distance, implant overlap, and contact spacing).
- **No Extraction or Post-Layout Simulation**: gpdk045 lacks the QRC technology directory (`qrcSetupDir /home/buet/pdk/gpdk045_v_6_0/qrc` is absent), preventing parasitic RCX extraction. LVS does not match due to 2-terminal schematic resistors (`analogLib/res`) versus 3-terminal layout resistors (`g45rnsnp` with substrate bulk pin) and open nets.

## Report Reproduction

Rebuild `report/gpdk045/report_data.json` and generate the final report document (.docx and .pdf):

```bash
python3 scripts/make_report_data.py
```
