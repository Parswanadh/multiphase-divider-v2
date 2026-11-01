# Stable baseline v1.0

This file records the finished, verified state of the project. Work after this point (v2, layout, extra figures) happens on `main` and must not change this baseline.

| Item | Value |
|---|---|
| Date | 2026-11-01 |
| Git tag | `v1.0-stable` (annotated) |
| Git branch | `stable/v1` (same commit, do not commit to it) |
| Commit | `336d17b` |
| Report | `report/gpdk045/System_Design_Project_Report_gpdk045.pdf` and `.docx`, 24 pages |
| VM snapshot | `stable-v1` in VirtualBox (VM `CadenceVM`), taken with the guest powered off |

## What is in the baseline

- Kuo et al. 8-phase divide-by-two divider ported to Cadence GPDK045 (45 nm), VDD 1.0 V.
- Design D (m = 4, R1 = R2 = 3 kOhm) divides 1.4 GHz to 700 MHz: 0.541 mW, 25.99 ps, PDP 14.07 fJ, 41 of 45 PVT corners pass.
- Design B (m = 4, R1 = R2 = 2 kOhm) divides 6 GHz to 3 GHz with 3.78 degrees phase error, 21 of 45 corners pass.
- Unsized baseline (m = 1, R = 8 kOhm) for the with/without sizing table.
- Virtuoso schematics (DLATCH, divider_core, tb_divider), simulation from the schematic with OCEAN and Spectre, ViVA waveform of design D.
- Placement layout of DLATCH and divider_core with Assura DRC (21 errors in 3 rules).
- The full flow: SKILL builders, OCEAN scripts, PVT sweeps, Layout XL, router and Assura DRC/LVS runs, and the evidence files in `results/gpdk045`.

Known limits of the baseline: the layout is placement only, there is no LVS-clean layout, no extraction and no post-layout simulation (the PDK copy has no Assura extraction files), and one schCheck warning remains on the testbench.

## Checksums (SHA-256)

```
f1a2ae52acbb487b9a1a720c68255c623b5351b9897c799ca439ebc305b6f641  System_Design_Project_Report_gpdk045.pdf
124a2cc614324b878b9fadf1e19ce47e6119216884c9658454637d302c4c5dea  System_Design_Project_Report_gpdk045.docx
```

## Restore

Code and report:

```
git fetch --tags
git checkout v1.0-stable          # detached, read-only baseline
git switch -c my-work v1.0-stable # to work from it
```

Cadence VM (VirtualBox):

```
VBoxManage snapshot CadenceVM restore stable-v1
```

The older tag `v1.0-ieee-lmwt-submission` belongs to the early phase of the project and is superseded by `v1.0-stable`. Its manuscript numbers were never measured.
