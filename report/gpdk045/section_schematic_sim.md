### Simulation driven directly from the Virtuoso schematic (OCEAN)

To evaluate the sized divider circuit (design D) directly from the Cadence schematic environment, the testbench schematic was simulated with Spectre at the nominal typical corner (tt, 27 C, 1.0 V supply, 1.0 V bias) with a 1.4 GHz input clock. The circuit uses load resistors R1 = R2 = 3 kOhm and transistor multiplicity m = 4. All 8 outputs divide to 700 MHz with a frequency division ratio of 2.0.

Propagation delay from the clock to the divider outputs is 26.66 ps, compared with 25.99 ps from the standalone netlist. Average supply power is 0.455 mW, compared with 0.541 mW from the standalone netlist run. The power differs by about 16 percent between the two flows. The cause is under investigation; the averaging window and the device parameters added by the Virtuoso netlister differ; the standalone value is used for the power and PDP tables.

Evidence files: results/gpdk045/ocean_schematic_run_1p4GHz_D.txt, cadence/ocean/run_schematic_tb_param.ocn, results/gpdk045/final/D_1p4.tsv
