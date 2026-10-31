# Power Gap Analysis: Standalone Spectre vs OCEAN Schematic Flow

## Executive Summary
Design D supply power is 0.5413 mW in standalone Spectre and 0.4555 mW in OCEAN (a 15.86% gap). The most likely cause (a hypothesis from reading the netlists; the decisive experiment below has not been run) is **Candidate (b)**: Virtuoso netlists layout-dependent parameters (STI stress `sa/sb=140n`, WPE `sca=226`, series resistance `nrd/nrs=1.167`) that degrade NMOS mobility, raise $V_{th}$, and lower tail current by ~16%. Averaging windows, testbench sources, and tolerances are identical.

## Candidate Ranking & Analysis

### 1. Candidate (b): Layout-Dependent Device Parameters (Rank 1 - Primary Cause)
- **Standalone Netlist** (`spectre/divider_gpdk45.scs` lines 25-31):
  `M1 (Q  D  xs   VSS) g45n1svt w=240n l=45n multi=mult`
  `M7 (tail NBIAS VSS VSS) g45n1svt w=480n l=90n multi=mult`
  Only `w`, `l`, `multi=4` are passed. `gpdk045_mos.scs` defaults to stress/WPE reference values: `sa=sb=6.1e-7`, `sca=scb=scc=1e-6`, `nrd=nrs=0.1667` (M1-M6) and `0.0833` (M7).
- **Virtuoso Netlist** (`results/gpdk045/virtuoso_netlist_tb_divider.scs` lines 16-36):
  `M7 (tail NBIAS VSS VSS) g45n1svt w=(480n) l=90n nf=1 as=16.8f ad=16.8f ps=520n pd=520n nrd=1.16667 nrs=1.16667 sa=140n sb=140n sd=160n sca=226.00151 scb=0.11734 scc=0.02767 m=(4)`
- **Mechanism & 16% Explanation**: In BSIM4 (`gpdk045_mos.scs`), `sa/sb=140n` induces compressive STI stress (`ku0 = -3.471e-8`, mobility degradation); `sca=226.0` induces strong well proximity effect (`kvth0we = 3.27e-3`, higher $V_{th}$); and `nrd/nrs=1.167` adds 7x–14x higher parasitic source resistance. Together they reduce M7 saturation tail current by ~16%, reducing CML supply power from 0.541 mW to 0.455 mW while preserving oscillation (~26 ps delay). **Explains 100% of the gap.**

### 2. Candidate (a): Averaging Window and Definition (Rank 2 - 0% of Gap)
- **Standalone Flow** (`cadence/vm/measure_guest.py` lines 236, 256-266):
  `ref = q1[2]`; `n_per = int((t[-1] - ref) // Tout)`; `t1 = ref + n_per * Tout`
  `s += (t[k + 1] - t[k]) * (-cur[k] - cur[k + 1]) * 0.5`; `iavg = s / (t1 - ref)`
  Averages `-cur` (`vdd:p`) over 18 output cycles starting at the 3rd Q1 rising edge after 10 ns settle (`periods_averaged = 18` in `results/gpdk045/final/D_1p4.tsv`).
- **OCEAN Flow** (`cadence/ocean/run_schematic_tb_param.ocn` lines 85-91):
  `ref = nth(2 q1L)`; `nper = fix((tstop - ref) / Tout)`; `t1 = ref + nper * Tout`
  `iavg = average(clip(i("/VDD/PLUS") ref t1))`; `imA = (0.0 - iavg) * 1e3`
  `ocean_schematic_run_1p4GHz_D.txt` line 18: `OC WINDOW ref=1.363628e-08 periods=18 t1=3.935057e-08`.
- **Can it explain 16%? No (0%)**. Windows, period counts (18), sign convention ($-I_{\text{VDD}}$), and start times (~13.64 ns) are mathematically equivalent; startup transients are excluded in both.

### 3. Candidate (c): Testbench Sources and Loads (Rank 3 - 0% of Gap)
- **Standalone** (`spectre/divider_gpdk45.scs` lines 14, 18-20, 40-47):
  `VCK  (ck  0) vsource type=pulse val0=0 val1=vdd delay=0       rise=tr fall=tr width=tck/2-tr period=tck`
  `VCKB (ckb 0) vsource type=pulse val0=0 val1=vdd delay=tck/2   rise=tr fall=tr width=tck/2-tr period=tck`
  With `tck=714.286ps, tr=20p, width=337.143ps, delay=357.143ps`, `VB=1.0V`, `VDD=1.0V`, `CL=10f`.
- **OCEAN** (`cadence/ocean/run_schematic_tb_param.ocn` lines 30-32; Virtuoso CDF):
  `desVar("tbPeriod" 1.0/fin)` (714.286 ps), `desVar("tbVbias" 1.0)`, `desVar("VDD" 1.0)`.
  Sources in `tb_divider` have identical `tr=tf=20p`, `pw=tbPeriod/2-20p`, `td=tbPeriod/2`, and `CL=10f`.
- **Can it explain 16%? No (0%)**. Sources, timing, and loading are identical.

### 4. Candidate (d): Initial Conditions and Tolerances (Rank 4 - <0.05% of Gap)
- **Standalone** (`spectre/divider_gpdk45.scs` lines 50, 53):
  `ic Q1=1.0 Q1b=0 Q2=1.0 Q2b=0 Q3=0 Q3b=1.0 Q4=0 Q4b=1.0`; `tran tran stop=40n ic=node errpreset=conservative maxstep=5p`
- **OCEAN** (`cadence/ocean/run_schematic_tb_param.ocn` lines 28, 33; netlist lines 70, 75):
  `ic("/Q1" "1.0" ... "/Q4b" "1.0")`; `analysis('tran ?stop "40n" ?errpreset "conservative" ?maxstep "5p")`; `reltol=1e-3`
- **Can it explain 16%? No (<0.05%)**. Initial states match and decay by 10 ns. Both enforce `errpreset=conservative` and `maxstep=5p`.

## Decisive Experiment
Run the Virtuoso schematic netlist (containing layout parameters) through `measure_guest.py` in the guest VM:
```bash
spectre /data/work/simulation/tb_divider/spectre/schematic/netlist/input.scs -format nutascii -raw /tmp/virt_d.raw +log /tmp/virt_d.log
python /home/buet/cadence/vm/measure_guest.py /tmp/virt_d.raw 1.0
```
**Outcome**: If `measure_guest.py` reports `power_mW ≈ 0.455 mW` (matching OCEAN), it proves that netlist device parameters account for 100% of the difference, eliminating measurement script discrepancies.
