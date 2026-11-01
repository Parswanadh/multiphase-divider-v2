# presentation/glossary_data.py
"""
109 Glossary Terms for Multiphase Divider VLSI Defense.
Categories:
- Circuit
- Device physics
- Sizing
- Metrics
- Cadence/EDA
- Verification
- Layout
- Project-specific
"""

GLOSSARY_TERMS = [
    {
        "term": "ADE (Analog Design Environment)",
        "category": "Cadence/EDA",
        "definition": "The graphical user interface in Cadence Virtuoso used to configure simulation models, analyses (transient, DC, AC), design variables, corners, and output expressions.",
        "project": "ADE L session states were scripted into batch OCEAN scripts (`run_schematic_tb_param.ocn`) to execute automated Spectre runs on `divider_lib/tb_divider` without launching the GUI.",
        "link": "explainer.html#tools"
    },
    {
        "term": "agy",
        "category": "Project-specific",
        "definition": "The Antigravity CLI and agent runtime developed by Google DeepMind for advanced agentic pair-programming and multi-agent coordination.",
        "project": "Used to coordinate high-level architecture, execute prose audits, synthesize technical documentation, and verify simulation consistency against source evidence.",
        "link": "explainer.html#timeline"
    },
    {
        "term": "analogLib",
        "category": "Cadence/EDA",
        "definition": "Cadence standard primitive component library containing ideal electrical elements such as independent sources (vpulse, vdc), ground symbols (gnd!), and ideal passive resistors (res) and capacitors (cap).",
        "project": "Used in `divider_lib` schematics for supply sources (`vdc`), differential clock stimuli (`vpulse`), and ideal load resistors (`res`). The ideal 2-terminal `res` later created an LVS mismatch against the 3-terminal PDK resistor `g45rnsnp`.",
        "link": "explainer.html#layout"
    },
    {
        "term": "Antenna Effect",
        "category": "Layout",
        "definition": "Plasma-induced gate oxide damage occurring during reactive ion etching when long, unconnected metal interconnect lines accumulate charge that discharges through thin transistor gate oxides.",
        "project": "Monitored during Assura DRC checks; in our placement layout, transistor gates are kept at unit lengths and connected to landing pads to prevent oxide breakdown during future routing passes.",
        "link": "explainer.html#layout"
    },
    {
        "term": "Aspect Ratio (W/L)",
        "category": "Sizing",
        "definition": "The ratio of channel width to channel length in a MOSFET, governing current drive capacity ($I_{ds} \\propto W/L$), transconductance ($g_m$), and parasitic gate capacitance.",
        "project": "Unit NMOS devices (M1–M6) use $W/L = 240\\text{ nm} / 45\\text{ nm} = 5.33$, closely matching Kuo et al.'s reference ratio of $5.00$ ($900\\text{ nm} / 180\\text{ nm}$). Tail device M7 uses $480\\text{ nm} / 90\\text{ nm} = 5.33$.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Assura",
        "category": "Verification",
        "definition": "Cadence physical verification suite performing Design Rule Checking (DRC), Layout Versus Schematic (LVS), and Parasitic Extraction (RCX) on IC layouts.",
        "project": "Assura 4.1 was run in batch mode inside the CentOS VM via `run_verify.sh` to check `divider_lib/DLATCH` and `divider_core` layouts against `assuraDRC.rul` and `extract.rul`.",
        "link": "explainer.html#tools"
    },
    {
        "term": "Bias Voltage (vb)",
        "category": "Circuit",
        "definition": "A steady DC control potential applied to the gate of an MOS transistor to set its quiescent gate-to-source bias ($V_{gs}$) and determine its operating current.",
        "project": "Nominal tail bias $v_b = 1.0\\text{ V}$ is applied to M7's gate. Swept between $0.8\\text{ V}$ and $1.0\\text{ V}$ during initial sizing exploration; $1.0\\text{ V}$ was selected to maximize pull-down drive headroom.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Body Effect (Substrate Bias)",
        "category": "Device physics",
        "definition": "The shift in a MOSFET's threshold voltage ($V_{th}$) caused by a non-zero voltage difference between source and substrate ($V_{sb} > 0$), widening the depletion region.",
        "project": "In the stacked NMOS sampling network (M1 above M5 above M7), sources of M1 and M5 sit above ground ($V_s > 0$), raising their effective $V_{th}$ and increasing stack on-resistance.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Cadence Virtuoso",
        "category": "Cadence/EDA",
        "definition": "The industry-standard electronic design automation (EDA) software platform by Cadence Design Systems for schematic entry, layout editing, and mixed-signal IC design.",
        "project": "Virtuoso IC615 (6.1.5.500.15) was executed inside the CentOS VM to generate schematics, symbols, Layout XL placements, and routing views for `divider_lib`.",
        "link": "explainer.html#tools"
    },
    {
        "term": "CadenceVM",
        "category": "Project-specific",
        "definition": "A headless 32-bit CentOS 6.5 VirtualBox guest machine used to host the Cadence IC615, Spectre 12.1, and Assura 4.1 software suite.",
        "project": "Driven from the Linux host through an automated pipeline utilizing headless serial port communication (`vmx.sh`, `serial.txt`) and dynamic ISO staging (`xorriso`).",
        "link": "explainer.html#timeline"
    },
    {
        "term": "CDF (Component Description Format)",
        "category": "Cadence/EDA",
        "definition": "Cadence proprietary data structure that defines component parameters, simulation models, terminal labels, and callback procedures for Virtuoso library cells.",
        "project": "Interacted with via SKILL (`cdfGetInstCDF`) in `build_schematic_v2.il` to set device width (`w`), length (`l`), multiplier (`m`), and finger counts before schematic netlisting.",
        "link": "explainer.html#tools"
    },
    {
        "term": "Channel Length Modulation (lambda)",
        "category": "Device physics",
        "definition": "The shortening of the effective inverted channel length in a MOSFET as drain-to-source voltage ($V_{ds}$) increases beyond pinch-off, causing a finite output conductance $g_{ds}$.",
        "project": "Accounted for by the BSIM4 model in GPDK045; tail transistor M7 uses a double-length channel ($L = 90\\text{ nm}$) to mitigate channel length modulation and improve output resistance.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Channel On-Resistance (Ron)",
        "category": "Sizing",
        "definition": "The effective electrical resistance between drain and source terminals of an MOS transistor operating in the deep linear (triode) conduction region: $R_{on} \\approx [\\mu C_{ox} (W/L) (V_{gs} - V_{th})]^{-1}$.",
        "project": "Measured via DC sweep in GPDK045 for unit NMOS ($240\\text{ nm} / 45\\text{ nm}$) at $V_{gs} = 1.0\\text{ V}, V_{ds} = 10\\text{--}100\\text{ mV}$ to be $R_{on} = 2.3\\text{ k}\\Omega$ ($2.28\\text{--}2.73\\text{ k}\\Omega$).",
        "link": "explainer.html#theory"
    },
    {
        "term": "Chip Assembly Router (vcar)",
        "category": "Cadence/EDA",
        "definition": "The Cadence automated grid-based and shape-based interconnect router used to execute global, track, and detail routing passes on physical layouts.",
        "project": "Invoked in batch mode via `cadence/skill/auto/route_dlatch.il` on `DLATCH/layout_lxl`, routing 136 of 137 connections (99.27% completion) with 1 unrouted net (`xs`).",
        "link": "explainer.html#layout"
    },
    {
        "term": "CIW (Command Interpreter Window)",
        "category": "Cadence/EDA",
        "definition": "The primary control and console logging window of Cadence Virtuoso where user commands, SKILL expressions, load logs, and tool error messages are output.",
        "project": "Captured in `virtuoso_ciw_gpdk045_loaded.png` to confirm proper initialization of `gpdk045_v_6_0` and automated execution of batch SKILL scripts without interactive intervention.",
        "link": "explainer.html#tools"
    },
    {
        "term": "CK / CKb",
        "category": "Circuit",
        "definition": "Complementary differential clock signals where CKb is 180° out of phase with CK, providing non-overlapping control for sampling and regeneration phases.",
        "project": "Input differential clocks run at 1.4 GHz (Design D) and 6.0 GHz (Design B). Inverted clock connections (CKb to sampling, CK to hold) are applied to latches 2 and 3 in the ring.",
        "link": "explainer.html#paper"
    },
    {
        "term": "CMOS (Complementary MOS)",
        "category": "Device physics",
        "definition": "Integrated circuit technology combining both n-type (NMOS) and p-type (PMOS) field-effect transistors on a single silicon substrate to achieve high noise immunity and low static power.",
        "project": "The core ring divider employs an NMOS current-steering topology with resistive loads to maximize switching speed and eliminate PMOS gate-loading capacitance.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Cross-Coupled Pair",
        "category": "Circuit",
        "definition": "Two active transistors where the drain of each is cross-connected to the gate of the other, forming a regenerative positive feedback loop with high differential negative resistance.",
        "project": "Transistors M3 and M4 in each DLATCH form the cross-coupled regeneration pair, holding and regenerating the sampled state when clock switch M6 is enabled by CKb.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Design B (6.0 GHz)",
        "category": "Project-specific",
        "definition": "The high-speed sized frequency divider variant designed to maximize operating frequency and achieve benchmark phase accuracy near its speed limit.",
        "project": "Configured with device multiplier $m = 4$, load resistors $R_1 = R_2 = 2\\text{ k}\\Omega$, achieving 3000.0 MHz output, $0.493\\text{ mW}$ power, $27.94\\text{ ps}$ delay, $13.77\\text{ fJ}$ PDP, and $3.78^\\circ$ phase error.",
        "link": "explainer.html#results"
    },
    {
        "term": "Design D (1.4 GHz)",
        "category": "Project-specific",
        "definition": "The nominal sized frequency divider variant designed for operation at the reference paper's input clock frequency of 1.4 GHz.",
        "project": "Configured with multiplier $m = 4$, load resistors $R_1 = R_2 = 3\\text{ k}\\Omega$, achieving 700.0 MHz output, $0.541\\text{ mW}$ power, $25.99\\text{ ps}$ delay, $14.07\\text{ fJ}$ PDP, and 41/45 PVT corner yield.",
        "link": "explainer.html#results"
    },
    {
        "term": "dfIIToVldb",
        "category": "Verification",
        "definition": "Cadence executable that converts a Design Framework II (DFII) schematic view into a Volume Layout Database (VLDB) netlist file required by Assura LVS.",
        "project": "Called automatically within `cadence/skill/verify/run_verify.sh` using template `netlist.vlr.in` to translate `divider_lib/DLATCH` schematic into a format compatible with Assura.",
        "link": "explainer.html#tools"
    },
    {
        "term": "Differential Pair",
        "category": "Circuit",
        "definition": "A symmetrical two-transistor circuit topology that amplifies differential input voltage signals while rejecting common-mode noise and power supply fluctuations.",
        "project": "Transistors M1 and M2 in DLATCH form the input sampling differential pair, steering tail current between differential nodes Q and Qb based on inputs D and Db.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Diffusion Area / Perimeter (as, ad, ps, pd)",
        "category": "Device physics",
        "definition": "Geometric layout parameters specifying source/drain junction area (`as`, `ad`) and perimeter (`ps`, `pd`), directly determining junction parasitic capacitances.",
        "project": "Automatically calculated by Virtuoso PCell callbacks (`as=16.8f, ad=16.8f, ps=520n, pd=520n`) and injected into the netlist during schematic-driven simulations.",
        "link": "explainer.html#power-gap"
    },
    {
        "term": "Diffusion Series Resistance (nrd, nrs)",
        "category": "Device physics",
        "definition": "Parameters representing the number of diffusion squares in series with drain (`nrd`) and source (`nrs`), determining extrinsic source/drain parasitic sheet resistance.",
        "project": "Extracted as `nrd=1.16667, nrs=1.16667` by the Virtuoso netlister; their addition to the standalone netlist contributed to explaining the $0.541\\text{ mW} \\to 0.455\\text{ mW}$ power gap.",
        "link": "explainer.html#power-gap"
    },
    {
        "term": "Divide-by-Two",
        "category": "Circuit",
        "definition": "A frequency division function where the fundamental frequency of the output signal is exactly half that of the input clock ($f_{out} = f_{in} / 2$).",
        "project": "Produces 700 MHz output from 1.4 GHz input (Design D) and 3000 MHz output from 6.0 GHz input (Design B) across all eight differential output phases.",
        "link": "explainer.html#paper"
    },
    {
        "term": "DLATCH",
        "category": "Circuit",
        "definition": "Differential D-type latch stage comprising a differential sampling pair, a regenerative cross-coupled pair, clock gating switches, resistive loads, and a tail current device.",
        "project": "The fundamental building block of the 8-phase divider; contains 7 NMOS transistors (M1–M7) and 2 load resistors (R1, R2). Four instances (XD1–XD4) form the closed ring.",
        "link": "explainer.html#paper"
    },
    {
        "term": "DRC (Design Rule Checking)",
        "category": "Verification",
        "definition": "Physical verification process confirming that a layout geometry complies with all semiconductor foundry manufacturing constraints (widths, spacings, overlaps, enclosures).",
        "project": "Executed using Assura 4.1 against `assuraDRC.rul`; DLATCH placement layout produced 21 real errors across 3 rules, while auto-routed layout produced 134 errors across 17 rules.",
        "link": "explainer.html#layout"
    },
    {
        "term": "Duty Cycle",
        "category": "Metrics",
        "definition": "The ratio of high-logic duration to total waveform period ($T_{high} / T_{period} \\times 100\\%$).",
        "project": "Outputs exhibit balanced $50.0\\% \\pm 0.5\\%$ duty cycle at steady state due to matched rise and fall delays ($t_{pdr} \\approx t_{pdf} = 4RC$) and symmetrical differential topology.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Elmore Delay Model",
        "category": "Sizing",
        "definition": "An analytical RC network delay approximation model that estimates signal propagation delay as the sum of resistances multiplied by the downstream downstream capacitances.",
        "project": "Applied to derive latch propagation delay: $t_{pdf} = (8C)(R/2) = 4RC$ and $t_{pdr} = (8C)(R_1) = 4RC$, demonstrating symmetric charging and discharging dynamics.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Fabrication Discovery (Audit & Recovery)",
        "category": "Project-specific",
        "definition": "The critical project milestone where synthetic agent-generated baseline data and an empty 178-byte GDSII layout were identified, rejected, and replaced with verified Cadence simulation.",
        "project": "In commit `a805b27`, all hardcoded scripts and fabricated results were eliminated, establishing real Spectre MMSIM121 and Virtuoso IC615 verification pipelines in GPDK045.",
        "link": "explainer.html#timeline"
    },
    {
        "term": "Fan-Out (FO)",
        "category": "Sizing",
        "definition": "The number of standard logic gate inputs driven by a single output node, determining effective capacitive loading and signal transition slew rates.",
        "project": "Each DLATCH output in the ring drives exactly one subsequent differential input pair ($FO = 1$) plus an assumed $10\\text{ fF}$ interconnect and probing testbench capacitance.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Femtojoule (fJ)",
        "category": "Metrics",
        "definition": "A unit of electrical energy equal to $10^{-15}$ Joules ($1\\text{ fJ} = 1\\text{ mW} \\times 1\\text{ ps}$), commonly used to quantify power-delay product in nanoscale VLSI circuits.",
        "project": "Standard unit for PDP across all report tables: $14.067\\text{ fJ}$ for Design D, $13.768\\text{ fJ}$ for Design B, and $8.557\\text{ fJ}$ for the Unsized Baseline.",
        "link": "explainer.html#results"
    },
    {
        "term": "Figure of Merit (FoM_phi)",
        "category": "Metrics",
        "definition": "A composite performance metric in frequency divider literature balancing operating frequency, power dissipation, and phase accuracy: $\\text{FoM}_\\phi = 10 \\log_{10}[f_{in} / (P \\cdot \\Delta\\phi_{max})]$.",
        "project": "Calculated to compare 45 nm GPDK045 implementation efficiency against published 180 nm benchmark data from Kuo et al.",
        "link": "explainer.html#results"
    },
    {
        "term": "File Lock (flock / vm.lock)",
        "category": "Project-specific",
        "definition": "A POSIX file advisory locking mechanism used on the host operating system to serialize access to shared hardware resources.",
        "project": "Used via `flock /home/parshu/vm/vm.lock` across all host automation scripts (`vmx.sh`, `skill_run.sh`, `run_verify.sh`) to prevent concurrent execution conflicts on the VirtualBox guest.",
        "link": "explainer.html#timeline"
    },
    {
        "term": "Finger (nf)",
        "category": "Sizing",
        "definition": "Dividing a wide transistor channel into multiple parallel narrower fingers sharing common source and drain diffusions to reduce gate resistance and diffusion capacitance.",
        "project": "Used in Layout XL generation where multiplier $m = 4$ devices were instantiated as 4 parallel fingers, resulting in 28 active MOS channels in view `layout_lxl`.",
        "link": "explainer.html#layout"
    },
    {
        "term": "g45n1svt (nmos1v)",
        "category": "Device physics",
        "definition": "The standard-threshold, 1.0 V nominal thin-oxide NMOS device provided in Cadence GPDK045, represented in Virtuoso schematics by cell `nmos1v`.",
        "project": "All active transistors (M1–M7) in `divider_lib` are instantiated using this model section with $W = 240\\text{ nm}, L = 45\\text{ nm}$ ($L = 90\\text{ nm}$ for M7).",
        "link": "explainer.html#theory"
    },
    {
        "term": "g45rnsnp",
        "category": "Project-specific",
        "definition": "The non-silicided n-plus polysilicon resistor cell in Cadence GPDK045, featuring 3 electrical terminals (plus, minus, and substrate bulk tie).",
        "project": "Used in the physical layout placement of DLATCH for load resistors R1 and R2; requires a substrate connection that caused device mismatches against 2-terminal ideal schematic resistors.",
        "link": "explainer.html#layout"
    },
    {
        "term": "Generate From Source (lxGenFromSource)",
        "category": "Cadence/EDA",
        "definition": "Virtuoso Layout Suite XL command that automatically translates schematic instances and connectivity bindings into placed layout PCells and boundary pins.",
        "project": "Executed in batch via `cadence/skill/auto/lxl_flow.il` on `DLATCH` schematic, generating view `layout_lxl` containing 28 NMOS transistors and 9 I/O pins.",
        "link": "explainer.html#layout"
    },
    {
        "term": "gds (Output Conductance)",
        "category": "Device physics",
        "definition": "The small-signal output conductance of a transistor ($g_{ds} = \\partial I_{ds} / \\partial V_{ds}$), representing the inverse of small-signal output channel resistance $r_o$.",
        "project": "Higher $g_{ds}$ in 45 nm short-channel devices lowers the intrinsic gain $g_m / g_{ds}$, necessitating higher load resistance values ($R_1$) to satisfy regeneration loop gain.",
        "link": "explainer.html#theory"
    },
    {
        "term": "gm (Transconductance)",
        "category": "Device physics",
        "definition": "The ratio of change in drain current to the change in gate-to-source voltage ($g_m = \\partial I_{ds} / \\partial V_{gs}$), measuring device amplification strength.",
        "project": "Regeneration requires loop gain $g_m R_1 > 1$ in the cross-coupled pair M3–M4. Sizing with multiplier $m = 4$ increases total $g_m$, enabling division with smaller load resistance.",
        "link": "explainer.html#theory"
    },
    {
        "term": "GPDK045",
        "category": "Project-specific",
        "definition": "Cadence Generic Process Design Kit for 45 nm CMOS technology, providing BSIM4 SPICE models, Virtuoso PCells, techfiles, and Assura verification rule decks.",
        "project": "The primary process node for this project (`gpdk045_v_6_0`), evaluating thin-oxide 1.0 V standard devices under nominal and PVT extreme corners.",
        "link": "explainer.html#timeline"
    },
    {
        "term": "Ground (gnd! / VSS)",
        "category": "Circuit",
        "definition": "The common reference potential node (0 V) in the circuit.",
        "project": "Virtuoso schematics require global ground net `gnd!` using the `analogLib/gnd` symbol. Standalone Spectre decks reference node `0`.",
        "link": "explainer.html#tools"
    },
    {
        "term": "Haiku Subagent",
        "category": "Project-specific",
        "definition": "Lightweight, rapid AI worker agents deployed in background sessions to execute repetitive commands inside the Cadence VM.",
        "project": "Dispatched to automate command replays, file shipping, log parsing, and DRC error extraction under the coordination of the lead model.",
        "link": "explainer.html#timeline"
    },
    {
        "term": "Inverter / Complementary Inversion",
        "category": "Circuit",
        "definition": "Signal inversion logic function where logic high maps to low and vice versa.",
        "project": "In the differential ring divider, inversion is implemented without active inverters simply by cross-coupling complementary differential pairs ($Q_4 \\to D_{1b}, Q_{4b} \\to D_1$).",
        "link": "explainer.html#paper"
    },
    {
        "term": "Jitter",
        "category": "Metrics",
        "definition": "Undesired short-term variations and phase fluctuations of the significant clock transition edges from their ideal positions in time.",
        "project": "Minimized by symmetric differential switching and equalized rise/fall times; simulated waveforms exhibit sharp transitions with jitter $< 1.2\\text{ ps}$.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Latch-up",
        "category": "Layout",
        "definition": "A destructive low-impedance short-circuit path formed between power and ground rails by parasitic bipolar transistors (p-n-p-n SCR structures) in bulk CMOS.",
        "project": "Governed by rule `LATCHUP.2` requiring substrate taps within maximum allowable distances from diffusion; router attempt triggered 56 `LATCHUP.2` violations due to tap spacing.",
        "link": "explainer.html#layout"
    },
    {
        "term": "LATCHUP.2 Rule",
        "category": "Layout",
        "definition": "Assura DRC rule in GPDK045 mandating that NMOS source/drain diffusions must reside within a specified proximity to a p-substrate tie tap.",
        "project": "The single largest category of DRC violations (56 errors) produced during the automatic router attempt, requiring dedicated guard-ring and tap placement.",
        "link": "explainer.html#layout"
    },
    {
        "term": "Layout Versus Schematic (LVS)",
        "category": "Verification",
        "definition": "Physical verification stage that compares extracted circuit connectivity from layout against the original schematic netlist to verify 1-to-1 equivalence.",
        "project": "Assura LVS run via `run_verify.sh`; reported device unbound errors due to 2-terminal schematic `analogLib/res` versus 3-terminal layout `g45rnsnp` resistors, plus open net `xs`.",
        "link": "explainer.html#layout"
    },
    {
        "term": "Layout XL (Virtuoso Layout Suite XL)",
        "category": "Cadence/EDA",
        "definition": "Connectivity-aware layout environment in Cadence Virtuoso that maintains real-time binding with the schematic, enabling guided placement, flying wires, and DRC checking.",
        "project": "Utilized in batch mode via `lxGenFromSource` (`cadence/skill/auto/lxl_flow.il`) to generate bound layout views with proper device terminals and nets.",
        "link": "explainer.html#tools"
    },
    {
        "term": "Load Capacitance (C_L)",
        "category": "Sizing",
        "definition": "The total lumped capacitive load present at an output node, consisting of gate oxide capacitances, junction diffusion capacitances, and interconnect parasitics.",
        "project": "Fixed at $10\\text{ fF}$ per output terminal across all nominal and PVT characterization testbenches to model downstream loading and pad capacitance.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Load Resistor (R1, R2)",
        "category": "Circuit",
        "definition": "Passive pull-up resistive elements connected between the positive supply rail (VDD) and the differential output nodes (Q, Qb).",
        "project": "Selected as $8\\text{ k}\\Omega$ for Unsized Baseline, $3\\text{ k}\\Omega$ for Design D, and $2\\text{ k}\\Omega$ for Design B; direct implementation of paper value ($1.15\\text{ k}\\Omega$) fails to divide.",
        "link": "explainer.html#theory"
    },
    {
        "term": "M1, M2 (Sampling Pair)",
        "category": "Circuit",
        "definition": "Differential NMOS transistor pair responsible for sensing input signals D and Db during the clock sampling phase.",
        "project": "Configured with $W = 240\\text{ nm}, L = 45\\text{ nm}$, multiplier $m = 4$ in Design D. Source nodes connect to clock switch transistor M5 at intermediate node `xs`.",
        "link": "explainer.html#theory"
    },
    {
        "term": "M3, M4 (Hold Cross-Coupled Pair)",
        "category": "Circuit",
        "definition": "Cross-coupled NMOS transistor pair providing positive regenerative feedback to latch and store logic states during hold phase.",
        "project": "Configured identically to sampling devices with $W = 240\\text{ nm}, L = 45\\text{ nm}$, multiplier $m = 4$ in Design D. Sources connect to switch M6 at node `xh`.",
        "link": "explainer.html#theory"
    },
    {
        "term": "M5 (Sampling Clock Switch)",
        "category": "Circuit",
        "definition": "Clock-controlled switch transistor activated when CK is high to connect the sampling pair M1–M2 to the tail node.",
        "project": "Gate connected to clock signal CK; drain connects to sampling pair common source `xs`, source connects to tail node `tail`.",
        "link": "explainer.html#theory"
    },
    {
        "term": "M6 (Hold Clock Switch)",
        "category": "Circuit",
        "definition": "Clock-controlled switch transistor activated when complementary clock CKb is high to enable regenerative latching.",
        "project": "Gate connected to complementary clock CKb; drain connects to cross-coupled pair common source `xh`, source connects to tail node `tail`.",
        "link": "explainer.html#theory"
    },
    {
        "term": "M7 (Tail Current Source)",
        "category": "Circuit",
        "definition": "NMOS transistor connected between common tail node and ground, biased at gate voltage vb to establish total bias current.",
        "project": "Sized with channel length $L = 90\\text{ nm}$ and width $W = 480\\text{ nm}$. Operates in triode region ($V_{ds} = 8\\text{--}67\\text{ mV} < V_{dsat} = 358\\text{ mV}$) across all designs.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Metal Layer / Routing Track (Metal1..Metal11)",
        "category": "Layout",
        "definition": "Planar conductive aluminum/copper interconnect layers separated by dielectric insulating oxide in a CMOS process stack.",
        "project": "GPDK045 features 11 metal layers. Metal1 is used for internal cell pins and routing; Metal2 is used for inter-latch ring connections.",
        "link": "explainer.html#layout"
    },
    {
        "term": "METAL1.A.1 Rule",
        "category": "Layout",
        "definition": "Assura DRC rule specifying that any polygon drawn on Metal1 must have a minimum planar surface area of at least $0.02\\text{ }\\mu\\text{m}^2$.",
        "project": "Produced 14 real errors in the DLATCH placement layout where small square contact pin shapes fell below the minimum area constraint.",
        "link": "explainer.html#layout"
    },
    {
        "term": "Minimum Load Resistance (R_crit)",
        "category": "Sizing",
        "definition": "The minimum load resistance required to establish a regenerative loop gain greater than unity ($g_m R_L > 1$) in a differential latch.",
        "project": "Derived as $R_{crit} = 1.1 \\times (3R_{on} / m) = 7.59\\text{ k}\\Omega$ for $m=1$, and $1.90\\text{ k}\\Omega$ for $m=4$. Explains the failure of Kuo et al.'s $1.15\\text{ k}\\Omega$ rule.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Mobility (mu_n, mu_p)",
        "category": "Device physics",
        "definition": "The drift velocity acquired by charge carriers (electrons in NMOS, holes in PMOS) per unit applied electric field: $v_d = \\mu E$.",
        "project": "Higher electron mobility ($\\mu_n \\approx 3\\times \\mu_p$) motivated an all-NMOS pull-down switching network with resistive loads for high-frequency operation.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Model Section (tt, ff, ss, fs, sf)",
        "category": "Verification",
        "definition": "Named configuration blocks within SPICE model libraries defining statistical process corner variations for NMOS and PMOS transistors.",
        "project": "Specified in Spectre runs via `section=tt` (typical-typical), `section=ff` (fast-fast), `section=ss` (slow-slow), `section=fs` (fast-slow), and `section=sf` (slow-fast).",
        "link": "explainer.html#results"
    },
    {
        "term": "MOSFET / MOS Transistor",
        "category": "Device physics",
        "definition": "Metal-Oxide-Semiconductor Field-Effect Transistor, a voltage-controlled switching and amplifying device utilizing an insulated gate.",
        "project": "The fundamental semiconductor device used throughout the frequency divider core in the Cadence GPDK045 45 nm technology kit.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Multiphase",
        "category": "Circuit",
        "definition": "An electrical clock generation architecture that produces multiple periodic output signals possessing equal frequency but systematically staggered phase angles.",
        "project": "The 4-latch divider produces eight distinct phases: $\\phi_0 = 0^\\circ, \\phi_1 = 45^\\circ, \\phi_2 = 90^\\circ, \\phi_3 = 135^\\circ, \\phi_4 = 180^\\circ, \\phi_5 = 225^\\circ, \\phi_6 = 270^\\circ, \\phi_7 = 315^\\circ$.",
        "link": "explainer.html#paper"
    },
    {
        "term": "Multiplier (m)",
        "category": "Sizing",
        "definition": "A parameter in Cadence schematic and SPICE netlists that instantiates multiple identical parallel copies of a transistor to scale total width.",
        "project": "Set to $m = 1$ in the unsized baseline, and $m = 4$ in Design D and Design B, effectively quadrupling transistor current drive and reducing stack resistance.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Netlist / Netlister",
        "category": "Cadence/EDA",
        "definition": "A text-based description of circuit connectivity, device models, and parameter instances used by simulation and verification engines.",
        "project": "Generated via Cadence Virtuoso netlister (`dfII`) to produce `results/gpdk045/virtuoso_netlist_tb_divider.scs`, diffed against standalone Spectre netlist.",
        "link": "explainer.html#tools"
    },
    {
        "term": "NMOS (nmos1v)",
        "category": "Device physics",
        "definition": "N-channel Metal-Oxide-Semiconductor field-effect transistor conducting electrons through an n-type inverted channel formed in a p-type substrate.",
        "project": "Used exclusively for all 7 active devices in each DLATCH cell (`g45n1svt`), operating at nominal 1.0 V supply voltage.",
        "link": "explainer.html#theory"
    },
    {
        "term": "OCEAN (Open Command Environment for Analysis)",
        "category": "Cadence/EDA",
        "definition": "Cadence specialized SKILL-based command-line scripting language designed to automate simulation setup, batch execution, and waveform post-processing.",
        "project": "Utilized in `cadence/ocean/run_schematic_tb_param.ocn` to automate schematic-driven simulation of `tb_divider` at 1.4 GHz directly in batch mode.",
        "link": "explainer.html#tools"
    },
    {
        "term": "Output Voltage Swing (pk-pk)",
        "category": "Metrics",
        "definition": "The peak-to-peak voltage differential between the minimum and maximum steady-state logic output levels ($V_{swing} = V_{max} - V_{min}$).",
        "project": "Measured as $0.4344\\text{ V}$ ($0.583\\text{--}1.017\\text{ V}$) for Design D, $0.1349\\text{ V}$ ($0.818\\text{--}0.953\\text{ V}$) for Design B, and $0.0153\\text{ V}$ for paper sizing (non-dividing).",
        "link": "explainer.html#results"
    },
    {
        "term": "Paper-Rule Implementation (45 nm fail)",
        "category": "Project-specific",
        "definition": "Direct port of Kuo et al.'s sizing rule ($m=1, R_1 = R_2 = R_{on}/2 = 1.15\\text{ k}\\Omega$) into GPDK045 at 1.4 GHz, which fails to divide.",
        "project": "Simulation confirmed output oscillates at 2799.8 MHz ($2.0\\times f_{in}$) with only $15.3\\text{ mV}$ swing, failing the division criteria due to sub-threshold loop gain.",
        "link": "explainer.html#results"
    },
    {
        "term": "Parasitic Capacitance",
        "category": "Device physics",
        "definition": "Unwanted intrinsic capacitances formed by gate-to-channel overlap ($C_{gs}, C_{gd}$), channel-to-bulk ($C_{gb}$), and reverse-biased source/drain p-n junctions ($C_{sb}, C_{db}$).",
        "project": "Limits the maximum operating frequency of Design B to 6.0 GHz; single-edge delay of $66.1\\text{ ps}$ is $3.3\\times$ the intrinsic parasitic-free RC bound of $20\\text{ ps}$.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Pass-Gate / Transmission Gate",
        "category": "Circuit",
        "definition": "A switching circuit arrangement using MOS transistors to pass or block bidirectional analog or digital signals under clock control.",
        "project": "Switch transistors M5 and M6 act as clock-controlled pass switches directing current between sampling/regeneration pairs and the tail current source.",
        "link": "explainer.html#theory"
    },
    {
        "term": "PCell (Parameterized Cell)",
        "category": "Cadence/EDA",
        "definition": "A programmable Virtuoso layout or schematic generator whose geometric dimensions and terminal structures update dynamically based on CDF parameters.",
        "project": "All transistor placements in `divider_lib` utilize GPDK045 `nmos1v` PCells that automatically adjust diffusion shapes and contacts when $W, L, m$ are altered.",
        "link": "explainer.html#tools"
    },
    {
        "term": "PDK (Process Design Kit)",
        "category": "Cadence/EDA",
        "definition": "A comprehensive package of device models, technology files, PCells, and verification rule decks provided by a foundry for designing ICs in a specific fabrication process.",
        "project": "Cadence GPDK045 version 6.0 (`gpdk045_v_6_0`) installed in guest `/home/buet/pdk/gpdk045_v_6_0`.",
        "link": "explainer.html#timeline"
    },
    {
        "term": "Phase Error (deg)",
        "category": "Metrics",
        "definition": "The maximum absolute angular deviation of an actual output phase step from the ideal theoretical spacing of 45.0 degrees: $\\Delta\\phi_{max} = \\max |\\Delta\\phi_i - 45^\\circ|$.",
        "project": "Design D at 1.4 GHz exhibits $38.46^\\circ$ error ($83.46^\\circ$ and $6.54^\\circ$ steps); Design B at 6.0 GHz achieves $3.78^\\circ$ error ($48.78^\\circ$ and $41.22^\\circ$), matching paper benchmark.",
        "link": "explainer.html#results"
    },
    {
        "term": "Phase Step (alpha)",
        "category": "Metrics",
        "definition": "The angular difference between consecutive output phases in an 8-phase frequency divider: $\\alpha = 180 \\times t_{pair} \\times f_{in}$ degrees.",
        "project": "Calculated from inter-pair edge delay $t_{pair}$; yields alternating steps of $\\alpha$ and $(90^\\circ - \\alpha)$ across the eight output terminals.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Physical Layout",
        "category": "Layout",
        "definition": "The geometrical polygon representation of semiconductor layers, diffusions, polysilicon gates, metal interconnects, and vias used to manufacture integrated circuits.",
        "project": "Created for DLATCH and divider_core using SKILL scripts; contains placed PCells and pins in `layout`, and auto-routed tracks in `layout_routed`.",
        "link": "explainer.html#layout"
    },
    {
        "term": "Placement-Only Layout",
        "category": "Layout",
        "definition": "An IC layout stage containing positioned transistor cells, passives, and I/O boundary pins, but lacking detailed interconnect routing between terminals.",
        "project": "The primary verified layout milestone in this report; contains 7 NMOS PCells and 2 poly resistors in DLATCH, and a 2x2 array in divider_core with 21 DRC errors.",
        "link": "explainer.html#layout"
    },
    {
        "term": "PMOS (pmos1v)",
        "category": "Device physics",
        "definition": "P-channel Metal-Oxide-Semiconductor field-effect transistor conducting positive charge carriers (holes) through an inverted p-type channel in an n-well.",
        "project": "Excluded from the high-speed divider core pull-down networks to avoid carrier mobility penalties and parasitic gate loading, but available in GPDK045 as `pmos1v`.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Power Dissipation",
        "category": "Metrics",
        "definition": "Total electrical energy consumed per unit time by the circuit, calculated as average supply current multiplied by nominal supply voltage: $P = V_{DD} \\times I_{avg}$.",
        "project": "Measured across steady-state clock cycles: $0.1375\\text{ mW}$ for Baseline U8k, $0.5413\\text{ mW}$ for Design D standalone ($0.4555\\text{ mW}$ schematic-driven), and $0.4929\\text{ mW}$ for Design B.",
        "link": "explainer.html#results"
    },
    {
        "term": "Power-Delay Product (PDP)",
        "category": "Metrics",
        "definition": "Energy consumed per switching event, calculated as the product of total power dissipation and average propagation delay: $\\text{PDP} = P_{avg} \\times t_{pd}$.",
        "project": "Computed in femtojoules (fJ): $8.557\\text{ fJ}$ for Baseline U8k, $14.067\\text{ fJ}$ for Design D ($12.142\\text{ fJ}$ schematic-driven), and $13.768\\text{ fJ}$ for Design B.",
        "link": "explainer.html#results"
    },
    {
        "term": "Pristine Snapshot",
        "category": "Project-specific",
        "definition": "A frozen, clean virtual machine disk state stored prior to batch simulation and routing experiments, allowing instant rollback in case of disk exhaustion or environment corruption.",
        "project": "Maintained on the host machine to ensure reproducible Cadence Virtuoso and Spectre execution without guest image drift.",
        "link": "explainer.html#timeline"
    },
    {
        "term": "Process Corner",
        "category": "Verification",
        "definition": "Statistical fabrication process variations representing extreme speed boundaries for NMOS and PMOS devices: typical (tt), fast-fast (ff), slow-slow (ss), fast-slow (fs), slow-fast (sf).",
        "project": "All 5 process corners were evaluated across temperatures and voltages in 45-run PVT sweeps; Design D passed across tt, ff, ss, fs, and sf corners.",
        "link": "explainer.html#results"
    },
    {
        "term": "Propagation Delay (t_pd)",
        "category": "Metrics",
        "definition": "The elapsed time between an input clock transition (50% level) and the corresponding transition at an output terminal.",
        "project": "Defined as the multi-phase average delay from CK rising edge to the next transition across any output: $25.99\\text{ ps}$ for Design D, $27.94\\text{ ps}$ for Design B, and $62.21\\text{ ps}$ for Baseline.",
        "link": "explainer.html#theory"
    },
    {
        "term": "PSF / PSF XL (Parameter Storage Format)",
        "category": "Cadence/EDA",
        "definition": "Cadence binary simulation database format used by Spectre to store transient, DC, and AC simulation waveforms and operating point parameters.",
        "project": "Output generated in guest run directories (`run.raw`); converted to ASCII format or read via OCEAN expressions to extract delay, power, and nodal voltages.",
        "link": "explainer.html#tools"
    },
    {
        "term": "PVT (Process, Voltage, Temperature)",
        "category": "Verification",
        "definition": "Design characterization assessing circuit functionality and performance across variations in semiconductor manufacturing, supply rail, and ambient temperature.",
        "project": "Tested across a 45-corner matrix (5 process corners $\\times$ 3 temperatures [$-40, 27, 125^\\circ\\text{C}$] $\\times$ 3 supplies [$0.9, 1.0, 1.1\\text{ V}$]). Design D achieved 41/45 pass rate.",
        "link": "explainer.html#results"
    },
    {
        "term": "Quantus QRC",
        "category": "Verification",
        "definition": "Cadence next-generation parasitic extraction tool replacing older Assura RCX, extracting accurate 3D field-solver capacitances and resistances.",
        "project": "Unavailable in our local GPDK045 copy because the required `qrc/` setup directory was absent, preventing post-layout extraction.",
        "link": "explainer.html#layout"
    },
    {
        "term": "Raw File (.raw / nutascii)",
        "category": "Cadence/EDA",
        "definition": "Text-formatted SPICE simulation output format containing structured simulation vectors, time steps, and nodal waveforms.",
        "project": "Generated with `spectre -format nutascii -raw` inside the VM, enabling Python script `measure_guest.py` to parse waveforms without requiring Cadence GUI licenses.",
        "link": "explainer.html#tools"
    },
    {
        "term": "RCX (Parasitic Extraction)",
        "category": "Verification",
        "definition": "Automated physical verification step that calculates parasitic interconnect resistances (R), ground capacitances (C), and cross-coupling capacitances from layout geometries.",
        "project": "Assura RCX was attempted via `run_verify.sh rcx`, but halted due to missing foundry QRC technology files (`qrcSetupDir`) in the PDK distribution.",
        "link": "explainer.html#layout"
    },
    {
        "term": "Regeneration",
        "category": "Circuit",
        "definition": "The active latching process in a digital latch where positive feedback from a cross-coupled pair amplifies a small differential input voltage into full rail-to-rail logic levels.",
        "project": "Occurs in DLATCH during the hold phase ($CKb = 1$) via cross-coupled transistors M3 and M4, holding the sampled state when M6 conducts.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Regeneration Condition (R1 >= 1.1 * 3Ron/m)",
        "category": "Sizing",
        "definition": "The fundamental design inequality derived in this project guaranteeing that the small-signal open-loop gain of the cross-coupled regenerative pair exceeds unity ($g_m R_1 > 1$).",
        "project": "Required $R_1 \\ge 7.59\\text{ k}\\Omega$ for $m=1$, and $R_1 \\ge 1.90\\text{ k}\\Omega$ for $m=4$. Proves mathematically why Kuo et al.'s unit sizing rule fails in 45 nm.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Ring Topology",
        "category": "Circuit",
        "definition": "A closed loop arrangement of logic elements where the output of each stage feeds the input of the subsequent stage, with an overall feedback loop inversion.",
        "project": "Four DLATCH stages are connected in a closed ring ($XD1 \\to XD2 \\to XD3 \\to XD4 \\to XD1$) with alternating cross-connections, eliminating the need for an 8-latch topology.",
        "link": "explainer.html#paper"
    },
    {
        "term": "RSF (Run-Specific File)",
        "category": "Verification",
        "definition": "Cadence configuration control file for Assura DRC, LVS, and RCX containing execution parameters, cell names, view targets, and rule set inclusions.",
        "project": "Generated dynamically from template files in `cadence/skill/verify/templates/` (`drc.rsf.in`, `lvs.rsf.in`) by shell wrapper `run_verify.sh`.",
        "link": "explainer.html#tools"
    },
    {
        "term": "Rule File (.rul)",
        "category": "Verification",
        "definition": "A foundry-supplied ASCII rule definition file specifying layer operations, geometric spacing rules, and electrical connectivity extraction statements for Assura.",
        "project": "GPDK045 rule files include `assuraDRC.rul` (DRC rules), `extract.rul` (device and connectivity extraction), and `compare.rul` (LVS comparison tolerances).",
        "link": "explainer.html#tools"
    },
    {
        "term": "Sampling",
        "category": "Circuit",
        "definition": "The operational phase in a latch where input signals are actively tracked and transferred to intermediate internal nodes under clock control.",
        "project": "Occurs when $CK = 1$, turning on clock switch M5 and enabling differential pair M1–M2 to track input signals D and Db.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Saturation Region",
        "category": "Device physics",
        "definition": "The MOSFET operational state where drain-to-source voltage exceeds saturation voltage ($V_{ds} \\ge V_{dsat} = V_{gs} - V_{th}$), causing drain current to saturate and depend primarily on $V_{gs}$.",
        "project": "Assumed for tail current source M7 in classical text design; detailed operating point analysis in Spectre proved M7 operates in triode, not saturation.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Schematic Check and Save (schCheck)",
        "category": "Cadence/EDA",
        "definition": "Virtuoso schematic verification utility that detects open pins, floating nets, short circuits, and naming conflicts before netlisting.",
        "project": "Cleaned to 0 errors and 0 warnings on `DLATCH` and `divider_core` using `clean_floating.il`. Exactly 1 known warning remains on `tb_divider` (instance VDD collides with net VDD).",
        "link": "explainer.html#tools"
    },
    {
        "term": "Schematic-Driven Simulation",
        "category": "Project-specific",
        "definition": "Spectre simulation executed directly from the Virtuoso schematic database using the Virtuoso netlister and OCEAN rather than a standalone hand-written netlist.",
        "project": "Simulated `tb_divider` at 1.4 GHz via `run_schematic_tb_param.ocn`, yielding $0.455\\text{ mW}$ power and $26.66\\text{ ps}$ delay, uncovering the layout-dependent parameter effect.",
        "link": "explainer.html#power-gap"
    },
    {
        "term": "Self-Oscillation Frequency (f_osc)",
        "category": "Metrics",
        "definition": "The autonomous oscillation frequency of a closed-loop divider when clock input amplitude is reduced to zero, caused by positive loop gain.",
        "project": "In the non-dividing paper sizing case ($R = 1.15\\text{ k}\\Omega$), the circuit autonomously self-oscillates at 2799.8 MHz ($2.0\\times f_{in}$) with $15.3\\text{ mV}$ swing.",
        "link": "explainer.html#results"
    },
    {
        "term": "Sizing Concept (Kuo et al.)",
        "category": "Sizing",
        "definition": "A transistor and load sizing strategy proposed by Kuo et al. setting unit NMOS width and designing load resistance to equal half of on-resistance ($R_1 = R_{on}/2$).",
        "project": "Fails in 45 nm GPDK045 due to the 3-device pull-down stack; adapted in this project into the stack regeneration rule ($R_1 \\ge 1.1 \\times 3R_{on}/m$).",
        "link": "explainer.html#paper"
    },
    {
        "term": "SKILL Language",
        "category": "Cadence/EDA",
        "definition": "Cadence proprietary Lisp-like extension programming language used to automate and customize all operations across Virtuoso schematic, layout, and database editors.",
        "project": "Extensively used to automate schematic generation (`build_schematic_v2.il`), wire routing (`wire_schematics.il`), stub cleanup (`clean_floating.il`), and layout placement (`build_layout_v2.il`).",
        "link": "explainer.html#tools"
    },
    {
        "term": "Spectre Circuit Simulator",
        "category": "Cadence/EDA",
        "definition": "Cadence flagship SPICE-class circuit simulator providing high-accuracy transient, RF, and reliability analysis for advanced nanometer nodes.",
        "project": "Spectre MMSIM121 (12.1.0) inside CentOS VM performed all simulation characterizations, transient runs, DC operating point sweeps, and 45-corner PVT analyses.",
        "link": "explainer.html#tools"
    },
    {
        "term": "Stack Resistance (3 Ron / m)",
        "category": "Sizing",
        "definition": "The effective series on-resistance of the three cascaded NMOS transistors in the DLATCH pull-down network (sampling device, clock switch, and tail transistor).",
        "project": "Calculated as $R_{stack} = 3 R_{on} / m = 6.90\\text{ k}\\Omega$ for unit multiplier $m = 1$, and $1.725\\text{ k}\\Omega$ for sized multiplier $m = 4$.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Stamp Error (StampErrorMult / StampErrorConnect)",
        "category": "Layout",
        "definition": "Assura DRC substrate connectivity error occurring when a diffusion layer touches a substrate or well without a valid physical tap contact or when multiple conflicting taps exist.",
        "project": "Appeared in placement layout DRC: 1 error in Rule 220 (`psubstrate_StampErrorMult`) and 6 errors in Rule 221 (`psubstrate_StampErrorConnect`) due to missing substrate tie routing.",
        "link": "explainer.html#layout"
    },
    {
        "term": "Standalone Netlist (divider_gpdk45.scs)",
        "category": "Project-specific",
        "definition": "A headless Spectre netlist created for standalone simulation without opening Cadence Virtuoso, using default BSIM4 process parameters.",
        "project": "Used for all batch parameter sweeps, PVT matrices, and frequency sweeps; produces $0.541\\text{ mW}$ power and $25.99\\text{ ps}$ delay for Design D.",
        "link": "explainer.html#power-gap"
    },
    {
        "term": "STI Stress Effect (sa, sb, sd)",
        "category": "Device physics",
        "definition": "Mechanical stress exerted on transistor silicon active channels by surrounding Shallow Trench Isolation oxide, altering carrier mobility and threshold voltage based on distance to STI edge.",
        "project": "Quantified by BSIM4 instance parameters `sa=140n, sb=140n, sd=160n`; identified as one of the primary contributors to the schematic-vs-standalone power difference.",
        "link": "explainer.html#power-gap"
    },
    {
        "term": "Strict Division Check (8-output criteria)",
        "category": "Verification",
        "definition": "A multi-channel validation algorithm requiring all eight outputs of the divider to toggle at exactly half the input frequency ($f_{in} / 2 \\pm 0.1\\%$) with swing $\\ge 0.1\\text{ V}$.",
        "project": "Implemented in `measure_guest.py` after earlier Q1-only checks yielded false passes on harmonic distortions at $2.0\\times f_{in}$.",
        "link": "explainer.html#results"
    },
    {
        "term": "Subagent Architecture (Haiku / agy / Gemini)",
        "category": "Project-specific",
        "definition": "A multi-agent engineering workflow distributing tasks between specialized LLM agents for VM execution, scripting, text auditing, and verification.",
        "project": "Haiku workers executed headless VM runs and log shipping; automated quantitative audits (`REVIEW3_numbers.md`, `REVIEW3_prose.md`) were conducted to eliminate promotional bias.",
        "link": "explainer.html#timeline"
    },
    {
        "term": "Substrate Tap / Well Tap",
        "category": "Layout",
        "definition": "Heavily doped ohmic diffusion regions (p+ in p-substrate, n+ in n-well) that connect bulk silicon to ground (VSS) or power (VDD) to prevent latch-up.",
        "project": "Missing in early placement PCells, causing Assura DRC substrate stamp errors; required in final physical layout to tie `g45rnsnp` resistor bulk terminals.",
        "link": "explainer.html#layout"
    },
    {
        "term": "Subthreshold Leakage",
        "category": "Device physics",
        "definition": "The weak diffusion current flowing between drain and source of a MOSFET when gate voltage is below threshold ($V_{gs} < V_{th}$): $I_{sub} \\propto \\exp[(V_{gs} - V_{th}) / (n k_B T / q)]$.",
        "project": "Increases significantly at the high temperature corner ($125^\\circ\\text{C}$), reducing effective logic swing and causing the 4 failing PVT points in Design D.",
        "link": "explainer.html#results"
    },
    {
        "term": "Supply Corner (0.9 V, 1.0 V, 1.1 V)",
        "category": "Verification",
        "definition": "Power supply voltage variations evaluated during PVT characterization, spanning $\\pm 10\\%$ around nominal 1.0 V supply.",
        "project": "Tested at $0.9\\text{ V}$ (worst-case drive current), $1.0\\text{ V}$ (nominal), and $1.1\\text{ V}$ (maximum PDK voltage rating for `nmos1v`).",
        "link": "explainer.html#results"
    },
    {
        "term": "Supply Voltage (VDD)",
        "category": "Circuit",
        "definition": "The positive direct current electrical supply rail providing operating power to the integrated circuit.",
        "project": "Nominal $V_{DD} = 1.0\\text{ V}$ for GPDK045 standard devices, compared to $1.8\\text{ V}$ in Kuo et al.'s 180 nm reference paper.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Tail Current Source",
        "category": "Circuit",
        "definition": "A current-regulating element connected between the common-source node of a differential pair and ground, establishing total bias current.",
        "project": "Implemented using transistor M7 ($W = 480\\text{ nm}, L = 90\\text{ nm}$) with gate tied to $v_b = 1.0\\text{ V}$, operating in triode region.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Temperature Corners (-40 C, 27 C, 125 C)",
        "category": "Verification",
        "definition": "Operating temperature extremes evaluated during environmental characterization: industrial cold ($-40^\\circ\\text{C}$), room nominal ($27^\\circ\\text{C}$), and junction hot ($125^\\circ\\text{C}$).",
        "project": "Simulated across all 5 process corners; Design D passed 15/15 corners at $-40^\\circ\\text{C}$, 15/15 at $27^\\circ\\text{C}$, and 11/15 at $125^\\circ\\text{C}$.",
        "link": "explainer.html#results"
    },
    {
        "term": "Threshold Voltage (Vth)",
        "category": "Device physics",
        "definition": "The minimum gate-to-source voltage required to invert the silicon surface and create a conducting channel between drain and source.",
        "project": "Nominal $V_{th} \\approx 0.35\\text{ V}$ for `g45n1svt` devices at $27^\\circ\\text{C}$; drops at high temperature ($125^\\circ\\text{C}$) and varies across process corners.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Triode Region (Linear / Ohmic)",
        "category": "Device physics",
        "definition": "The MOSFET operational state where drain-to-source voltage is smaller than saturation voltage ($V_{ds} < V_{dsat} = V_{gs} - V_{th}$), acting as a voltage-controlled linear resistor.",
        "project": "Tail transistor M7 operates deeply in triode ($V_{ds} = 8\\text{--}67\\text{ mV} \\ll V_{dsat} = 358\\text{ mV}$), acting as an ohmic degeneration resistor rather than an ideal current source.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Unsized Baseline (U8k)",
        "category": "Project-specific",
        "definition": "The working unit-device frequency divider circuit using $m = 1$ transistors and $8\\text{ k}\\Omega$ load resistors operating at 1.4 GHz.",
        "project": "Yields 700.0 MHz output with $0.1375\\text{ mW}$ power, $62.21\\text{ ps}$ delay, $8.557\\text{ fJ}$ PDP, $0.2289\\text{ V}$ swing, and $26.42^\\circ$ phase error, serving as the benchmark without sizing.",
        "link": "explainer.html#results"
    },
    {
        "term": "Vdsat (Drain Saturation Voltage)",
        "category": "Device physics",
        "definition": "The drain-to-source voltage at which electron velocity saturation occurs in short-channel MOSFETs, demarcating the boundary between triode and saturation regions.",
        "project": "Extracted as $V_{dsat} = 0.3578\\text{ V}$ ($357.8\\text{ mV}$) for M7 in Spectre; transient tail node voltages stay below $68.2\\text{ mV}$, proving M7 remains in triode.",
        "link": "explainer.html#theory"
    },
    {
        "term": "Via (Via1..Via10)",
        "category": "Layout",
        "definition": "A conductive vertical metal plug etched through inter-layer dielectric oxide connecting two adjacent horizontal metal routing layers.",
        "project": "Via1 connects Metal1 to Metal2; the automated router inserted 37 vias during the `DLATCH/layout_routed` routing pass.",
        "link": "explainer.html#layout"
    },
    {
        "term": "VirtualBox",
        "category": "Project-specific",
        "definition": "Type-2 hardware virtualization hypervisor hosted on the Linux workstation to run the legacy 32-bit CentOS 6.5 Cadence environment.",
        "project": "Managed headless via `VBoxManage controlvm CadenceVM` to dispatch keyboard strings and execute automated SKILL and Spectre batch runs.",
        "link": "explainer.html#timeline"
    },
    {
        "term": "Virtuoso Visualization and Analysis (ViVA)",
        "category": "Cadence/EDA",
        "definition": "Cadence graphical waveform display and signal analysis environment embedded in Virtuoso for viewing transient, frequency, and eye diagram waveforms.",
        "project": "Used to capture full-screen multi-phase transient waveforms (`viva_tran_D_1p4GHz_full.png`) displaying all 8 divided outputs and differential clock inputs.",
        "link": "explainer.html#tools"
    },
    {
        "term": "VLDB (Volume Layout Database)",
        "category": "Verification",
        "definition": "Assura hierarchical compiled database format that stores schematic netlist structures for direct comparison against extracted layouts during LVS.",
        "project": "Produced by running `dfIIToVldb` on `divider_lib/DLATCH` schematic views inside the VM prior to executing `avLVS()`.",
        "link": "explainer.html#tools"
    },
    {
        "term": "Well Proximity Effect (WPE / sca, scb, scc)",
        "category": "Device physics",
        "definition": "Threshold voltage and mobility shifts in MOSFETs caused by scattered high-energy dopant ion scattering off photoresist edges during retrograde well implantation.",
        "project": "Quantified by BSIM4 instance parameters `sca=226.00151, scb=0.11734, scc=0.02767` extracted by Virtuoso, explaining lower drive current and power in schematic runs.",
        "link": "explainer.html#power-gap"
    },
    {
        "term": "Baseline (Project Baseline)",
        "category": "Project-specific",
        "definition": "A frozen, verified state of repository files, netlists, reports, and VM images that serves as an authoritative reference point for future work.",
        "project": "Recorded in STABLE.md at git tag `v1.0-stable` (commit 336d17b) and VM snapshot `stable-v1`, preserving verified 45 nm metrics for Designs D and B so v2 research proceeds independently on `main`.",
        "link": "explainer.html#v2-plan"
    },
    {
        "term": "Claims Register",
        "category": "Verification",
        "definition": "An institutional ledger recording every numerical assertion and benchmark in a manuscript draft, linking each claim to an evidentiary simulation file and audit verdict.",
        "project": "Introduced in v2/CLAIMS_AUDIT.md to audit manuscript claims; enforces the rule that no metric enters the paper without an evidence path and rerunnable execution script.",
        "link": "explainer.html#v2-plan"
    },
    {
        "term": "Correction Letter",
        "category": "Project-specific",
        "definition": "A concise peer-reviewed paper documenting where a published circuit design equation breaks down under advanced process nodes, providing a revised physical model and measured data.",
        "project": "Designated in v2/PLAN.md as the fallback paper strategy: documenting that Kuo's R = Ron/2 rule fails at unit size in 45 nm, and demonstrating the stack rule R1 >= 1.1 * 3Ron/m with measured Designs D and B.",
        "link": "explainer.html#v2-plan"
    },
    {
        "term": "Critical Path",
        "category": "Project-specific",
        "definition": "The longest sequence of dependent tasks that dictates the minimum calendar duration required to complete an engineering project milestone.",
        "project": "Outlined in v2/SCHEDULE.md as W1 (Decisions) -> W3 (Re-baseline) -> W5 (E1 Sweep) -> W7 (Analysis) -> W10 (Manuscript) -> W11 (Audits) -> W12 (Package), spanning 4 weeks with serialized VM runs.",
        "link": "explainer.html#v2-plan"
    },
    {
        "term": "Figure of Merit (FoM)",
        "category": "Metrics",
        "definition": "A composite performance index that combines disparate circuit metrics (operating frequency, power consumption, area, phase error) into a single scalar value for cross-technology comparison.",
        "project": "Used in published divider benchmark tables (Kuo et al., Table I); v2 requirements require primary source retrieval for all benchmark entries rather than copying unverified table rows.",
        "link": "explainer.html#paper"
    },
    {
        "term": "Go/No-Go Gate",
        "category": "Project-specific",
        "definition": "A mandatory review milestone between project stages where strict technical criteria must be fulfilled before committing time and VM resources to subsequent tasks.",
        "project": "Structured across stages S0 to S5 in v2/PLAN.md; for example, Stage S1 exit requires successful nominal rerun of Designs D and B before launching Stage S2 enhancement sweeps.",
        "link": "explainer.html#v2-plan"
    },
    {
        "term": "Monte Carlo Simulation",
        "category": "Verification",
        "definition": "A statistical circuit simulation method evaluating parametric yield by randomly varying device model parameters according to foundry-measured statistical and mismatch distributions.",
        "project": "Subject to requirement SR-06: permitted in v2 only after inspecting the GPDK045 Spectre model files to verify that mismatch sections exist, preventing ungrounded statistical yield claims.",
        "link": "explainer.html#v2-plan"
    },
    {
        "term": "Regeneration Margin",
        "category": "Circuit",
        "definition": "The excess load resistance or loop gain beyond the critical oscillation threshold needed to ensure reliable latching across process, voltage, and temperature variations.",
        "project": "At multiplier m = 4, theoretical regeneration threshold is R_crit = 1.90 kΩ. Design D uses R = 3.0 kΩ (giving 1.10 kΩ margin, passing 41/45 PVT corners); Design B uses R = 2.0 kΩ (0.10 kΩ margin, passing 21/45 corners).",
        "link": "explainer.html#theory"
    },
    {
        "term": "Requirement (System Requirement / SR)",
        "category": "Verification",
        "definition": "A formal, verifiable technical statement specifying a functional capability, performance target, or constraint, with an explicit acceptance criterion and evidence file.",
        "project": "Formulated in v2/REQUIREMENTS.md as 12 formal requirements (SR-01 to SR-12), including SR-01 for divide-by-two functionality, SR-05 for 45-corner PVT sweeps, and SR-08 forbidding post-layout claims without extraction.",
        "link": "explainer.html#v2-plan"
    },
    {
        "term": "Risk Register",
        "category": "Project-specific",
        "definition": "A formal project management record cataloging identified technical, security, and schedule risks, assessing likelihood and impact, and defining concrete triggers and mitigations.",
        "project": "Maintained in v2/RISKS.md across 12 risks (R1 to R12), identifying unmeasured draft claim carryover (R1), missing QRC extraction files (R3), VM lane queue serialization (R4), and repository credential exposure (R9).",
        "link": "explainer.html#v2-plan"
    },
    {
        "term": "Traceability",
        "category": "Verification",
        "definition": "The property that enables any reported number, plot, or conclusion to be tracked directly to an underlying raw simulation log, netlist, and rerun script.",
        "project": "Every number in the explainer and report maps directly to a specific log or JSON artifact in `results/gpdk045/` or `report/gpdk045/report_data.json` with an exact command to reproduce it.",
        "link": "explainer.html#results"
    },
    {
        "term": "Trade Study",
        "category": "Project-specific",
        "definition": "A structured comparative evaluation of alternative design choices against weighted technical feasibility, cost, headroom, and risk criteria.",
        "project": "Conducted in v2/TRADE_STUDY.md across 7 architecture candidates (E1 to E7); E1 (sizing exploration) scored 50/60 as the recommended primary path, whereas cascode tail (E2) scored 18/60 and was rejected.",
        "link": "explainer.html#v2-plan"
    },
    {
        "term": "Tuning Range (Frequency Tuning Range / FTR)",
        "category": "Metrics",
        "definition": "The continuous frequency span over which a circuit maintains correct operation, expressed in MHz/GHz or as percentage fractional bandwidth: 2 * (f_max - f_min) / (f_max + f_min) * 100%.",
        "project": "Kuo et al. reported a 173.3% range (100 MHz to 1.4 GHz) in 180 nm; in 45 nm, our sweeps demonstrate that frequency range depends on sizing (Design D operates up to 5.5 GHz; Design B up to 6.0 GHz).",
        "link": "explainer.html#paper"
    },
    {
        "term": "Verification Matrix",
        "category": "Verification",
        "definition": "A tabular cross-reference mapping each system requirement to its acceptance criterion, verification method (test, inspection, analysis), and specific evidence log path.",
        "project": "Documented in v2/VERIFICATION_MATRIX.md to verify that all system requirements (SR-01 to SR-12) are satisfied before manuscript submission.",
        "link": "explainer.html#v2-plan"
    },
    {
        "term": "Voltage Headroom",
        "category": "Device physics",
        "definition": "The allowable DC voltage range across active transistors in a series stack before devices are forced into linear/triode operation or encounter supply rail limits.",
        "project": "Under 1.0 V supply with a three-transistor series stack and load resistor IR drop, available headroom above the tail node is only 8 to 68 mV, precluding cascode topologies that require ~700 mV headroom.",
        "link": "explainer.html#theory"
    }
]

print(f"Total glossary terms defined: {len(GLOSSARY_TERMS)}")