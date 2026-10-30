# Cadence Spectre / OCEAN flow for the divider

**UNTESTED. These files were written without access to Cadence, Spectre or gpdk045.**
Every line marked `VERIFY` is an assumption to check on your install before trusting any number.

The flow produces `waveforms.txt` in the same format the local ngspice runs produce, so the
existing `scripts/measure_tran.py` analyses it unchanged.

## Files

| File | Role |
|---|---|
| `run_spectre.sh` | Runs Spectre, then OCEAN export and measurement. Exits nonzero on failure. |
| `export_waveforms.ocn` | Reads the tran results and writes `waveforms.txt` on a uniform 5 ps grid. |
| `measure_divider.ocn` | Prints frequency, division ratio, power, delay and PDP from the same results. |
| `../../spectre/divider_gpdk45.scs` | The standalone netlist (not modified here). |

## Step by step (CentOS Cadence machine)

1. Open a terminal and load the Cadence environment. VERIFY the command your site uses
   (often `source /path/to/cadence/setup.sh` or `module load cadence`). Check with
   `which spectre ocean`.

2. Create a work directory and copy the netlist and scripts into it:
   ```bash
   mkdir -p ~/divider_run && cd ~/divider_run
   cp /path/to/multiphase-divider-v2/spectre/divider_gpdk45.scs .
   cp /path/to/multiphase-divider-v2/cadence/ocean/*.ocn /path/to/multiphase-divider-v2/cadence/ocean/run_spectre.sh .
   chmod +x run_spectre.sh
   ```

3. Edit the model include in `divider_gpdk45.scs`, line 10:
   ```
   include "/path/to/gpdk045/models/spectre/gpdk045.scs" section=typical   // VERIFY
   ```
   Replace the path with your gpdk045 Spectre model file. VERIFY that the section name
   `typical` exists in that file. The device name `nmos1v` (line 24 onward) also needs
   checking against your PDK.

4. Run the flow:
   ```bash
   ./run_spectre.sh
   ```
   Runtime is not measured yet (the export makes about 80k point evaluations). Watch the terminal for:
   - `resolved as ...` lines, one per signal. If the script stops with
     "a signal did not resolve", the names in `export_waveforms.ocn` do not match your netlist.
     Add the correct name to the `nm*` list and run again.
   - `raw mean i(VDD:p) ... sign factor applied`. Normally the factor is `1`, meaning Spectre already
     reports the supply current as negative. A `-1` means the sign was flipped (VERIFY that this is
     the correct result for your run).

5. Check the outputs:
   - `waveforms.txt`: first line `time v(ck) v(q1) ... i(vdd)`, then numeric rows.
   - `measure_ocean.log`: the OCEAN measurement report.
   - `run.log`: the Spectre log. Look for the summary line; VERIFY its wording.

6. Copy `waveforms.txt` to the host (repository machine) and analyse it with the existing script:
   ```bash
   # on the CentOS machine
   scp waveforms.txt you@yourhost:/home/parshu/projects/multiphase-divider-v2/
   # on the host
   cd /home/parshu/projects/multiphase-divider-v2
   python3 scripts/measure_tran.py waveforms.txt 1.0 10
   ```
   The arguments are: file, VDD in volts (`1.0`), and settle time in ns (`10`). The script prints a
   report and exits with status 1 if the output does not divide by 2.

## Changing the run

Settings come from environment variables, so you do not need to edit the `.ocn` files:

| Variable | Default | Meaning |
|---|---|---|
| `FIN` | `1e9` | Input clock frequency in Hz. Must match `fin` in the netlist. |
| `VDD` | `1.0` | Supply voltage in V. Must match `vdd` in the netlist. |
| `T_STOP` | `40e-9` | Export stop time in s. Must not exceed the netlist `stop`. |
| `DT` | `5e-12` | Uniform export step in s. |
| `WIN_START` / `WIN_STOP` | `10e-9` / `40e-9` | Settled measurement window in s. |
| `RAW` | `rawdir` | Spectre result directory. |

Example: `FIN=2e9 WIN_STOP=40e-9 ./run_spectre.sh`. Change the netlist `fin` to match.

## What the output numbers mean

The OCEAN report (`measure_ocean.log`) and the Python report (`measure_tran.py` on the host)
compute the same quantities. Small differences are expected, as noted in the last column.

| Printed name | Unit | Meaning | Difference from Python |
|---|---|---|---|
| `f_in measured` | GHz | Input clock frequency from the mean period of CK rising edges in the window. | Same method. |
| `f_out measured` | MHz | Output frequency from the mean period of the differential Q1 − Q1b rising through 0 V. | Python uses single-ended Q1 at its mid-swing. Expect a small difference. |
| `division ratio` | - | f_in / f_out. Should be 2.0000 for a divide-by-2. | Same meaning. |
| `sign factor` | - | Multiplies the raw `i(VDD:p)` so the file has negative supply current. Normally `1`. | Python assumes the file sign is already correct. |
| `periods averaged` | - | Number of whole output periods used for the power average. | Python starts at the third Q1 edge and ends at the end of the sim. Counts may differ by 1. |
| `i_avg` | mA | Time-averaged supply current. Negative means the supply is delivering current. | Same sign convention. |
| `P_avg` | mW | Average power, `-VDD × i_avg`. | Same as Python `power_mw`. |
| `CK->any-output delay` | ps | Mean time from each CK rising edge to the next rising edge on any of the 8 outputs. | Same definition as Python `ck_to_q_delay_ps`. Thresholds: OCEAN uses each signal's mid-swing. |
| `CK->Q1 delay` | ps | Mean time from CK rising to the next Q1 rising edge. | Only in OCEAN. |
| `PDP (any-output)` | fJ | `P_avg × CK->any-output delay`. mW × ps = fJ. | Same as Python `pdp_fj`. |
| `PDP (CK->Q1)` | fJ | `P_avg × CK->Q1 delay`. | Only in OCEAN. |

## Known limits and what to check first

- The standalone netlist has no initial-condition or convergence checks beyond `ic` on line 51.
  If Q1 does not toggle, check the `ic` statement and the bias (`vb`) before anything else.
- Frequencies and delays use `cross()` edge lists, matching `measure_tran.py`. Power uses
  `integ(wave from to)` as a definite integral, with `average(clip())` printed as a cross-check.
  `delay()` appears only as a labelled single-edge cross-check, and its argument form is unverified.
  If `cross`, `integ` or `delay` report an error, check the signatures for your OCEAN version
  (the `cross`, `integ` and `delay` lines are the places to change).
- Missing signal names and calculator errors are caught with `errset`, so the script reports which
  candidate failed instead of aborting on the first one.
- The `nm*` name lists are the most likely failure. The standalone netlist uses `/ck`, `/Q1` ... `/VDD:p`.
  Schematic (ADE) netlists add hierarchy, so the names change.
- The `grep` for `0 errors` and the `tran.tran.tran` file name are guesses. Check them against your
  Spectre `run.log` and `rawdir/` listing on the first run.
