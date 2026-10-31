# Power gap experiment: design D (m=4, R=3k, vb=1.0 V, VDD 1.0 V, 1.4 GHz, tt, 27 C)

Guest: CentOS VM, Spectre MMSIM121, measurement by `measure_guest.py` (copied as `pg_measure_guest.py`).
Runs in `/data/work/pg/{std,params,virt_mc,virt_tt}`, all shipped files tagged `pg_`. Raw files deleted after measuring.

## Commands (host side, each guest call under `flock /home/parshu/vm/vm.lock`)
- Staged `pg_measure_guest.py` (copy of `cadence/vm/measure_guest.py`), `pg_run_gpdk045.sh` (copy of `cadence/vm/run_gpdk045.sh`, names changed to pg_), `pg_divider_std.scs` (copy of `spectre/divider_gpdk45.scs`), `pg_divider_std_params.scs`, `pg_virt_tail.scs`; built ISO and attached it as the guest CD; copied to `/data/work/pg`.
- Params file: `sed '/g45n1svt/ s/multi=mult$/multi=mult as=16.8f ad=16.8f ps=520n pd=520n nrd=1.16667 nrs=1.16667 sa=140n sb=140n sd=160n sca=226.00151 scb=0.11734 scc=0.02767/'` (M1-M7; strings copied from the Virtuoso netlist).

Guest commands:
1. Standalone: `FINS=1.4G RLS=3k VBS=1.0 CLS=10f MULTS=4 ./pg_run_gpdk045.sh /data/work/pg/std grid`
2. Standalone + params: same command in `/data/work/pg/params`.
3. Virtuoso netlist (`section=mc` as found): `sed -e "s/^parameters .*/parameters tbVbias=1.0 VDD=1.0 tbPeriod=7.142857e-10/" .../tb_divider/spectre/schematic/netlist/input.scs > pg_virt_mc.scs`, append `pg_virt_tail.scs` (ic, `tran stop=40n ic=node errpreset=conservative maxstep=5p`, save incl. VDD:p), `spectre pg_virt_mc.scs -format nutascii -raw pg_virt_mc.raw`, then `python pg_measure_guest.py pg_virt_mc.raw 1.0`.
4. Same as 3 with extra `-e "s/section=mc/section=tt/"`: `virt_tt`.

## Results (power_mW, delay_ps as printed by measure_guest.py; all rows divides=1, ratio 2.0000, periods_averaged 18)

| run | power_mW | delay_ps | PDP fJ | max phase-step err deg |
|---|---|---|---|---|
| standalone (baseline, reproduces repo) | 0.541337 | 25.99 | 14.067 | 38.461 |
| standalone + Virtuoso layout params | 0.455402 | 26.66 | 12.142 | 37.900 |
| Virtuoso netlist, section=mc | 0.455402 | 26.66 | 12.142 | 37.900 |
| Virtuoso netlist, section=tt | 0.455402 | 26.66 | 12.142 | 37.900 |

OCEAN (`results/gpdk045/ocean_schematic_run_1p4GHz_D.txt`): 0.4554862 mW, ck-to-q 26.66 ps. Difference from the script row: 0.02 %.

## Verdict
The layout-dependent parameters explain the gap. Adding the as/ad/ps/pd/nrd/nrs/sa/sb/sd/sca/scb/scc values to the standalone M1-M7 devices moves power from 0.541337 to 0.455402 mW (-15.9 %), matching the Virtuoso netlist (0.455402 mW) and OCEAN (0.4554862 mW) to within 0.02 %. The measurement window is not the cause: all runs use the same script, 18 averaged periods and the same settle time. The `section=mc` vs `section=tt` difference in the Virtuoso netlist (the OCEAN script requests tt, the netlist on disk says mc) has no effect on the result. Not separately tested: which individual parameter (STI stress, WPE, or series resistance) causes the change, and the `m=(4)` vs `multi=mult` instance-multiplier difference (the parametrised run uses multi=mult, and it matches the Virtuoso netlist).

## Effect on design D metrics if Virtuoso-parameter numbers were used (numbers only)
- Power 0.541337 -> 0.455402 mW (x0.841).
- Delay 25.99 -> 26.66 ps.
- PDP 14.067 -> 12.142 fJ (-13.7 %).
- Max phase-step error 38.461 -> 37.900 deg (f_out 700 MHz and ratio 2.0000 unchanged).
- Note: `results/gpdk045/virtuoso_netlist_tb_divider.scs` in the repo is an older export (period 1 ns, VB 0.8 V) and was not used.
