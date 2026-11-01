# Legacy: early local ngspice study

This folder keeps the first phase of the project, before any run in Cadence.

- It uses a generic LEVEL=1 180 nm model deck and ngspice, not the GPDK045 process kit.
- The numbers here are not the results of the final report and must not be quoted as GPDK045 results.
- The final results, report and scripts are in `results/gpdk045`, `report/gpdk045`, `cadence/` and `scripts/`.

Scripts in `ngspice/scripts` expect to be run from `legacy/ngspice` (they resolve paths relative to it).
