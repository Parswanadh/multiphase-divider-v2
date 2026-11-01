# Digilent Basys 3 FPGA Demonstrator: 8-Phase Divide-by-2 Frequency Divider

Teaching and lab demonstrator for the 8-phase divide-by-2 CMOS divider circuit topology described in Kuo et al. (*IEEE Microwave and Wireless Technology Letters*, May 2025) and analyzed in Cadence GPDK045 (`spectre/divider_gpdk45.scs`).

Target Platform: **Digilent Basys 3** (Xilinx Artix-7 XC7A35T-1CPG236C)

---

## 1. Important Scientific Disclaimer

> [!CAUTION]
> **This FPGA implementation is a functional teaching demonstrator, NOT evidence for the analog integrated circuit.**
> It must never be presented as physical experimental proof of the GPDK045 analog divider. All metrics claimed in the manuscript are based exclusively on Cadence Spectre simulations in GPDK045 recorded in `plan/claims_register.csv`.

### What This Demonstrator Demonstrates:
1. **Circuit Logical Functionality:** Confirms the 4-stage D-latch ring architecture with alternating clock polarities (latches 1 and 4 on `CK`, latches 2 and 3 on `CKb`) and cyclic cross-coupling.
2. **Frequency Division by Two:** Realizes exact divide-by-2 operation ($f_{\text{out}} = f_{\text{in}} / 2$).
3. **Multiphase Generation & Human-Visible Viva UI:** Displays the sequential rotating 8 phases on the 16 Basys 3 LEDs at 2 Hz ($125\text{ ms}$ per 45° step), allowing immediate visual verification in a viva or demonstration.
4. **Frequency Agility:** Generates 8 software/switch-selectable clock rates (2 Hz, 10 Hz, 100 Hz, 1 kHz, 100 kHz, 1 MHz, 10 MHz, 100 MHz) with direct scope probe access on Pmod JA and JB.
5. **Startup & Reset Behavior:** Illustrates the start-up kick mechanism and digital ring behavior.

### What This Demonstrator Does NOT Demonstrate:
1. **No CML Stack Physics:** The FPGA uses standard digital CMOS logic cells (Xilinx `LDCE` and `LDPE` primitives) with rail-to-rail ($0\text{ V}$ to $3.3\text{ V}$) switching. The analog circuit uses Current-Mode Logic (CML) differential pairs operating with small analog swings ($\approx 430\text{ mV}_{\text{p-p}}$) over an NMOS tail current source ($M_7$).
2. **No Resistive Loads:** The FPGA fabric uses active CMOS pull-up PMOS transistors, not passive resistive loads ($R_L \approx 2\text{ k}\Omega - 3\text{ k}\Omega$).
3. **No Process, Voltage, or Temperature (PVT) Sensitivity:** The FPGA will not demonstrate the high-temperature / low-voltage analog regeneration failures documented in `pvt_D.tsv` and `pvt_B.tsv`.
4. **No Analog Phase-Step Error:** In an analog CML circuit, the 8-phase step accuracy depends directly on matching the latch intrinsic propagation delay $T_d$ to exactly one quarter of the input clock period ($T_{\text{in}}/4 = T_{\text{out}}/8$). In GPDK045 Design D at 1.4 GHz ($T_{\text{in}} = 714.3\text{ ps}$), $T_d \approx 26.0\text{ ps}$, resulting in severe step mismatch ($83.5^\circ$ and $6.5^\circ$, step error $38.5^\circ$). In zero-delay digital simulation, transitions collapse to simultaneous pairs at clock edges ($90^\circ$ and $0^\circ$).

---

## 2. Circuit Architecture and Interconnect

The divider consists of four level-sensitive differential latches configured in a closed ring:

```
           +---------------------------------------------+
           |                                             |
           |   +----------+   +----------+   +---------+ | +---------+
           +-->| Latch 1  |-->| Latch 2  |-->| Latch 3 |-+>| Latch 4 |---+
               | (CK)     |   | (CKb)    |   | (CKb)   |   | (CK)    |   |
               +----------+   +----------+   +---------+   +---------+   |
                    ^                                                    |
                    +----------------------------------------------------+
```

### Signal Interconnect Table (Matches `spectre/divider_gpdk45.scs`):

| Latch Stage | Clock Gate | Data Input ($D$) | Complement ($D_b$) | Normal Output ($Q$) | Inverted Output ($Q_b$) | Hardware Primitive | Reset / Kick State |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Latch 1** | `CK`  | $Q_{4b}$ ($\overline{Q_4}$) | $Q_4$  | $Q_1$ | $Q_{1b}$ | Xilinx `LDPE` | Preset to `1` |
| **Latch 2** | `CKb` | $Q_{1b}$ ($\overline{Q_1}$) | $Q_1$  | $Q_2$ | $Q_{2b}$ | Xilinx `LDPE` | Preset to `1` |
| **Latch 3** | `CKb` | $Q_2$  | $Q_{2b}$ | $Q_3$ | $Q_{3b}$ | Xilinx `LDCE` | Clear to `0`  |
| **Latch 4** | `CK`  | $Q_{3b}$ ($\overline{Q_3}$) | $Q_3$  | $Q_4$ | $Q_{4b}$ | Xilinx `LDCE` | Clear to `0`  |

### Sequential 8-Phase Progression:

When each stage propagation delay equals $T_d = T_{\text{in}}/4$, the rising edges occur sequentially every 45° ($T_{\text{out}}/8$):

| Index | Signal Name | Nominal Phase | Time Offset ($T_{\text{in}} = 10\text{ ns}$) | Description |
|:---:|:---:|:---:|:---:|:---|
| **P0** | `q1`  | **0.0°**   | $0.0\text{ ns}$ | Latch 1 rising edge (Reference phase) |
| **P1** | `q2b` | **45.0°**  | $2.5\text{ ns}$ | Latch 2 falling edge ($\overline{Q_2}$ rising) |
| **P2** | `q3b` | **90.0°**  | $5.0\text{ ns}$ | Latch 3 falling edge ($\overline{Q_3}$ rising) |
| **P3** | `q4`  | **135.0°** | $7.5\text{ ns}$ | Latch 4 rising edge |
| **P4** | `q1b` | **180.0°** | $10.0\text{ ns}$| Latch 1 falling edge ($\overline{Q_1}$ rising) |
| **P5** | `q2`  | **225.0°** | $12.5\text{ ns}$| Latch 2 rising edge |
| **P6** | `q3`  | **270.0°** | $15.0\text{ ns}$| Latch 3 rising edge |
| **P7** | `q4b` | **315.0°** | $17.5\text{ ns}$| Latch 4 falling edge ($\overline{Q_4}$ rising) |

---

## 3. Simulation Results (`tb/tb_ring.v`)

Run the testbench with:
```bash
bash tb/run_tb.sh
```

### Verification Findings:
1. **Division Ratio:**
   - Input clock: $100.000\text{ MHz}$ ($T = 10.000\text{ ns}$)
   - Output frequency: $50.000\text{ MHz}$ ($T = 20.000\text{ ns}$)
   - Ratio: **$2.0000$ (PASS)**
2. **Phase Spacing with Ideal Delay ($T_d = 2.5\text{ ns}$):**
   - Each phase step is exactly **$45.00^\circ$**
   - Maximum phase step error: **$0.00^\circ$ (PASS)**
3. **Phase Spacing with Zero-Delay Digital Model ($T_d = 0.0\text{ ns}$):**
   - Phase steps: $[90.0^\circ, 0.0^\circ, 90.0^\circ, 0.0^\circ, 90.0^\circ, 0.0^\circ, 90.0^\circ, 0.0^\circ]$
   - Maximum phase step error: **$45.00^\circ$**
   - Demonstrates that purely digital latches collapse intra-half-clock phase spacing without analog delay lines.
4. **Reset and Lockup Behavior:**
   - **Digital Domain:** Loop contains 3 inversions (odd number). A static digital state requires $Q_1 = \overline{Q_4}$, $Q_2 = \overline{Q_1} = Q_4$, $Q_3 = Q_2 = Q_4$, and $Q_4 = \overline{Q_3} = \overline{Q_4}$, which is a Boolean contradiction ($Q_4 \neq \overline{Q_4}$). Thus, no static digital state exists; the ring self-recovers even from all-zeros or all-ones within 1-2 clock phases.
   - **Analog CML Domain:** In analog differential logic, a symmetric DC bias point exists ($Q = Q_b = V_{dd} - I_{\text{tail}} R / 2$) where differential voltage $\Delta V = 0$. Without an initial condition kick (`ic`), an ideal SPICE simulation remains trapped at $\Delta V = 0$. The FPGA reset button (`btnC`) provides the hardware equivalent of this kick.

---

## 4. Synthesis Check with Yosys (Host Environment)

The host machine lacks Vivado and has no connected FPGA board. To prove synthesizability on open tools, a synthesis run was executed using Yosys (`synth_xilinx -top top`):

```bash
bash build/run_yosys_synth.sh
```

### Synthesis Results Tail (`build/yosys_synth.log`):
```text
=== Top-Level Cell Utilization ===
   BUFG:       3
   IBUF:      18
   OBUF:      32
   INV:        7
   LDCE:       2   (Latches 3 & 4 transparent latches with async clear)
   LDPE:       2   (Latches 1 & 2 transparent latches with async preset)
   FDCE:      53   (Frequency divider counters)
   CARRY4:    19   (High-speed counters)
   LUT2-LUT6: 89   (Clock multiplexing & decode logic)
   Estimated LCs: 69
```
*Vivado and openFPGALoader are not installed on this host, and no board is attached; no bitstream or physical measurement is claimed on this machine.*

---

## 5. Basys 3 User Interface and Pinout

### Slide Switch Functions (`sw[15:0]`):
- `sw[2:0]`: Ring Clock Rate Selection
  - `000`: **2 Hz** (LED visual demo: 1 Hz divider output, each 45° step takes 125 ms)
  - `001`: **10 Hz** (Fast rotating LED bar)
  - `010`: **100 Hz**
  - `011`: **1 kHz** (Audio / oscilloscope)
  - `100`: **100 kHz** (Oscilloscope demonstration)
  - `101`: **1 MHz**
  - `110`: **10 MHz** (High-speed scope)
  - `111`: **100 MHz** (Direct oscillator bypass)
- `sw[3]`: LED Display Mode
  - `0`: Sequential rotating phase sequence `phases_rot[7:0]` (LEDs 0-7 light up in a rotating circle)
  - `1`: Direct latch output mode `phases_raw[7:0]` ($Q_1..Q_4, Q_{1b}..Q_{4b}$)
- `sw[15]`: Asynchronous Reset (Alternative to `btnC`)

### LED Indicators (`led[15:0]`):
- `led[7:0]`: Eight phase outputs (selected by `sw[3]`)
- `led[10:8]`: Mirror of active rate selection `sw[2:0]`
- `led[11]`: Ring clock state (`CK`)
- `led[14]`: Heartbeat indicator (1 Hz blink from 100 MHz clock)
- `led[15]`: Reset status indicator (active high)

### Pmod Connections (Oscilloscope Probes):
- **Pmod JA (Raw Differential Outputs):**
  - Pin 1 (J1): $Q_1$ | Pin 2 (L2): $Q_2$ | Pin 3 (J2): $Q_3$ | Pin 4 (G2): $Q_4$
  - Pin 7 (H1): $Q_{1b}$ | Pin 8 (K2): $Q_{2b}$ | Pin 9 (H2): $Q_{3b}$ | Pin 10 (G3): $Q_{4b}$
- **Pmod JB (Rotating 8-Phase Outputs):**
  - Pins 1 to 4: Phases 0° ($Q_1$), 45° ($Q_{2b}$), 90° ($Q_{3b}$), 135° ($Q_4$)
  - Pins 7 to 10: Phases 180° ($Q_{1b}$), 225° ($Q_2$), 270° ($Q_3$), 315° ($Q_{4b}$)

---

## 6. How to Build and Program with Vivado

On a computer with Xilinx Vivado installed:

1. Clone or copy the repository.
2. Connect the Digilent Basys 3 board via USB and set the programming jumper (JP1) to `JTAG` or `USB`.
3. Open a terminal in this directory:
   ```bash
   cd /home/parshu/projects/multiphase-divider-v2/fpga/basys3
   ```
4. Run the batch build script:
   ```bash
   vivado -mode batch -source build/build.tcl
   ```
   This script executes synthesis, placement, routing, generates timing and utilization reports in `build/vivado_out/`, outputs `build/basys3_divider_top.bit`, and automatically programs the attached board.

---

## 7. Short Viva Presentation Script (What to Show)

1. **Introduction (30s):**
   > *"This board demonstrates the digital switching architecture of the Kuo et al. 2025 8-phase divide-by-2 frequency divider. While our paper analyzes the analog CML circuit in Cadence GPDK045, this FPGA demonstrator provides a physical, tangible model of the ring topology."*
2. **Visual LED Demonstration at 2 Hz (45s):**
   > *"Notice switches `sw[2:0]` are set to `000`. The 100 MHz oscillator is divided to a 2 Hz ring clock. The divider outputs a 1 Hz square wave, giving an output period of 1 second. As you can see on LEDs `led[7:0]`, each phase step is separated by exactly 125 ms (45 degrees), forming a continuous, rotating one-hot wave."*
3. **Frequency Agility (30s):**
   > *"By changing `sw[2:0]` from `000` to `001` through `110`, the ring clock frequency scales from 2 Hz to 10 MHz. On an oscilloscope connected to Pmod JA pins 1-4, we observe four quadrature 50% duty-cycle square waves at half the input frequency."*
4. **Startup & Reset Explanation (45s):**
   > *"When I press `btnC`, the hardware forces latches 1 & 2 high and 3 & 4 low using Xilinx `LDPE` and `LDCE` primitives. In digital logic, because the ring contains 3 inversions, no static state can lock the loop. In the analog CML circuit, however, latches can trap in a symmetric common-mode state where differential voltage is zero; that is why Cadence Spectre requires an initial condition `ic`."*
5. **Phase Error & Paper Connection (30s):**
   > *"In an ideal digital simulation, we achieve 45.0° steps by setting per-stage propagation delay to $T_{\text{in}}/4$. In the analog GPDK045 circuit, however, device sizing and load resistors yield a 26 ps stage delay, causing the authentic $38.5^\circ$ step error reported in our manuscript."*
