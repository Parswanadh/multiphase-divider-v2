### Simulation driven directly from the Virtuoso schematic (OCEAN)

The testbench schematic of the sized divider (design D: R1 = R2 = 3 kOhm, m = 4) was simulated with Spectre directly from Virtuoso at the typical corner (tt, 27 C, VDD = 1.0 V, bias 1.0 V) with a 1.4 GHz input clock. All eight outputs divide to 700 MHz (ratio 2.0). The clock-to-output delay is 26.66 ps and the average supply power is 0.455 mW. Figure 5 shows the corresponding ViVA waveforms.

The standalone netlist of the same circuit gives 0.541 mW and 25.99 ps. The difference comes from the layout-dependent device parameters (stress, well-proximity and series-resistance terms) that the Virtuoso netlister adds to every transistor. Adding the same parameters to the standalone netlist gives 0.455 mW and 26.66 ps, identical to the schematic-driven run. With these parameters the power-delay product of design D is 12.14 fJ instead of 14.07 fJ, and the division is unchanged. The tables in this report use the standalone netlist, which has the default device parameters of the process.

Evidence files: results/gpdk045/ocean_schematic_run_1p4GHz_D.txt, results/gpdk045/power_gap_experiment.md, results/gpdk045/final/D_1p4.tsv
