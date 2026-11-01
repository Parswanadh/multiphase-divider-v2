##==============================================================================
## basys3.xdc
##
## Physical and Timing Constraints for Digilent Basys 3 FPGA Board
## Part: Xilinx Artix-7 XC7A35T-1CPG236C
##
## Project: Kuo et al. 8-Phase Divide-by-2 Frequency Divider Demonstrator
##
## Note on Pin Verification:
## All pins below are mapped from the official Digilent Basys 3 Master XDC.
## Any pin that requires user confirmation against their specific hardware
## revision is explicitly tagged with [USER_VERIFY].
##==============================================================================

##------------------------------------------------------------------------------
## 1. Primary Clock (100 MHz Oscillator on Pin W5) - Confirmed
##------------------------------------------------------------------------------
set_property PACKAGE_PIN W5 [get_ports clk]
set_property IOSTANDARD LVCMOS33 [get_ports clk]
create_clock -add -name sys_clk_pin -period 10.00 -waveform {0 5} [get_ports clk]

##------------------------------------------------------------------------------
## 2. Slide Switches (sw[15:0]) - Confirmed against Digilent Master
##------------------------------------------------------------------------------
set_property PACKAGE_PIN V17 [get_ports {sw[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[0]}]
set_property PACKAGE_PIN V16 [get_ports {sw[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[1]}]
set_property PACKAGE_PIN W16 [get_ports {sw[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[2]}]
set_property PACKAGE_PIN W17 [get_ports {sw[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[3]}]
set_property PACKAGE_PIN W15 [get_ports {sw[4]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[4]}]
set_property PACKAGE_PIN V15 [get_ports {sw[5]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[5]}]
set_property PACKAGE_PIN W14 [get_ports {sw[6]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[6]}]
set_property PACKAGE_PIN W13 [get_ports {sw[7]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[7]}]
set_property PACKAGE_PIN V2  [get_ports {sw[8]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[8]}]
set_property PACKAGE_PIN T3  [get_ports {sw[9]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[9]}]
set_property PACKAGE_PIN T2  [get_ports {sw[10]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[10]}]
set_property PACKAGE_PIN R3  [get_ports {sw[11]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[11]}]
set_property PACKAGE_PIN W2  [get_ports {sw[12]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[12]}]
set_property PACKAGE_PIN U1  [get_ports {sw[13]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[13]}]
set_property PACKAGE_PIN T1  [get_ports {sw[14]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[14]}]
set_property PACKAGE_PIN R2  [get_ports {sw[15]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[15]}]

##------------------------------------------------------------------------------
## 3. Push Buttons (btnC: Center Button - Reset) - Confirmed
##------------------------------------------------------------------------------
set_property PACKAGE_PIN U18 [get_ports btnC]
set_property IOSTANDARD LVCMOS33 [get_ports btnC]

##------------------------------------------------------------------------------
## 4. User LEDs (led[15:0]) - Confirmed against Digilent Master
##------------------------------------------------------------------------------
set_property PACKAGE_PIN U16 [get_ports {led[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[0]}]
set_property PACKAGE_PIN E19 [get_ports {led[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[1]}]
set_property PACKAGE_PIN U19 [get_ports {led[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[2]}]
set_property PACKAGE_PIN V19 [get_ports {led[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[3]}]
set_property PACKAGE_PIN W18 [get_ports {led[4]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[4]}]
set_property PACKAGE_PIN U15 [get_ports {led[5]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[5]}]
set_property PACKAGE_PIN U14 [get_ports {led[6]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[6]}]
set_property PACKAGE_PIN V14 [get_ports {led[7]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[7]}]
set_property PACKAGE_PIN V13 [get_ports {led[8]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[8]}]
set_property PACKAGE_PIN V3  [get_ports {led[9]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[9]}]
set_property PACKAGE_PIN W3  [get_ports {led[10]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[10]}]
set_property PACKAGE_PIN U3  [get_ports {led[11]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[11]}]
set_property PACKAGE_PIN P3  [get_ports {led[12]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[12]}]
set_property PACKAGE_PIN N3  [get_ports {led[13]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[13]}]
set_property PACKAGE_PIN P1  [get_ports {led[14]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[14]}]
set_property PACKAGE_PIN L1  [get_ports {led[15]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[15]}]

##------------------------------------------------------------------------------
## 5. Pmod Header JA (Pins 1..4, 7..10)
## Standard Digilent JA pinout:
##   Pin 1:  J1  (ja[0] -> Q1)
##   Pin 2:  L2  (ja[1] -> Q2)
##   Pin 3:  J2  (ja[2] -> Q3)
##   Pin 4:  G2  (ja[3] -> Q4)
##   Pin 7:  H1  (ja[4] -> Q1b)
##   Pin 8:  K2  (ja[5] -> Q2b)
##   Pin 9:  H2  (ja[6] -> Q3b)
##   Pin 10: G3  (ja[7] -> Q4b)
## [USER_VERIFY]: Verify JA bottom row pin ordering (pins 7-10 vs H1,K2,H2,G3)
##                on older Basys 3 board revisions.
##------------------------------------------------------------------------------
set_property PACKAGE_PIN J1 [get_ports {ja[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {ja[0]}]
set_property PACKAGE_PIN L2 [get_ports {ja[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {ja[1]}]
set_property PACKAGE_PIN J2 [get_ports {ja[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {ja[2]}]
set_property PACKAGE_PIN G2 [get_ports {ja[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {ja[3]}]
set_property PACKAGE_PIN H1 [get_ports {ja[4]}]
set_property IOSTANDARD LVCMOS33 [get_ports {ja[4]}]
set_property PACKAGE_PIN K2 [get_ports {ja[5]}]
set_property IOSTANDARD LVCMOS33 [get_ports {ja[5]}]
set_property PACKAGE_PIN H2 [get_ports {ja[6]}]
set_property IOSTANDARD LVCMOS33 [get_ports {ja[6]}]
set_property PACKAGE_PIN G3 [get_ports {ja[7]}]
set_property IOSTANDARD LVCMOS33 [get_ports {ja[7]}]

##------------------------------------------------------------------------------
## 6. Pmod Header JB (Pins 1..4, 7..10) - Rotating 8-Phase Outputs
## Standard Digilent JB pinout:
##   Pin 1:  A14 (jb[0] -> P0  0 deg)
##   Pin 2:  A16 (jb[1] -> P1 45 deg)
##   Pin 3:  B15 (jb[2] -> P2 90 deg)
##   Pin 4:  B16 (jb[3] -> P3 135 deg)
##   Pin 7:  A15 (jb[4] -> P4 180 deg)
##   Pin 8:  A17 (jb[5] -> P5 225 deg)
##   Pin 9:  C15 (jb[6] -> P6 270 deg)
##   Pin 10: C16 (jb[7] -> P7 315 deg)
## [USER_VERIFY]: Verify JB bottom row pin ordering (pins 7-10 vs A15,A17,C15,C16).
##------------------------------------------------------------------------------
set_property PACKAGE_PIN A14 [get_ports {jb[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {jb[0]}]
set_property PACKAGE_PIN A16 [get_ports {jb[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {jb[1]}]
set_property PACKAGE_PIN B15 [get_ports {jb[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {jb[2]}]
set_property PACKAGE_PIN B16 [get_ports {jb[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {jb[3]}]
set_property PACKAGE_PIN A15 [get_ports {jb[4]}]
set_property IOSTANDARD LVCMOS33 [get_ports {jb[4]}]
set_property PACKAGE_PIN A17 [get_ports {jb[5]}]
set_property IOSTANDARD LVCMOS33 [get_ports {jb[5]}]
set_property PACKAGE_PIN C15 [get_ports {jb[6]}]
set_property IOSTANDARD LVCMOS33 [get_ports {jb[6]}]
set_property PACKAGE_PIN C16 [get_ports {jb[7]}]
set_property IOSTANDARD LVCMOS33 [get_ports {jb[7]}]

##------------------------------------------------------------------------------
## 7. Device Configuration and Voltage Standards
##------------------------------------------------------------------------------
set_property CFGBVS VCCO [current_design]
set_property CONFIG_VOLTAGE 3.3 [current_design]

## Clock routing rule for fabric-divided clock driving latches:
## Required by Vivado DRC when internal divided clocks drive latch gates.
set_property CLOCK_DEDICATED_ROUTE FALSE [get_nets ck_raw]
