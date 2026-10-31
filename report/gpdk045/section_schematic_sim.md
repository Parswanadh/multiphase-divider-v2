### Simulation driven directly from the Virtuoso schematic (OCEAN)

To evaluate the circuit directly from the schematic environment, an OCEAN script was used to netlist the divider_lib/tb_divider schematic with Virtuoso's netlister and simulate it using Spectre 12.1 under the gpdk045 tt corner at 27 C. Inspection confirms that the devices and values in the Virtuoso-generated netlist match the standalone netlist, specifically M1–M6 (w=240n, l=45n, m=4), M7 (w=480n, l=90n, m=4), and load resistors R1 and R2 (3k).

Transient simulation demonstrates divide-by-2 operation from 1 GHz to 500 MHz, evidenced by Q1 rising edges occurring 2.0 ns apart relative to a 1.0 ns clock period. The Q1 output signal achieves a voltage swing of 0.713–1.006 V. The circuit exhibits an average supply current of 0.39 mA, corresponding to about 0.39 mW of power consumption at a 1.0 V supply. Several caveats apply to this run: the testbench bias was set to 0.8 V rather than 1.0 V, only Q1 was checked in this script, and the verification remains a nominal single-corner check.

Evidence files: results/gpdk045/ocean_schematic_run.txt, cadence/ocean/run_schematic_tb.ocn, results/gpdk045/virtuoso_netlist_tb_divider.scs
