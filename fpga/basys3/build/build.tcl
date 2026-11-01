#==============================================================================
# build.tcl
#
# Vivado Batch Implementation and Hardware Programming Script
# Target: Digilent Basys 3 (XC7A35T-1CPG236C)
#
# How to run on a machine with Vivado installed:
#   vivado -mode batch -source build/build.tcl
#
# Note:
#   This script is intended for execution on a machine with Xilinx Vivado.
#   It reads RTL, constraints, runs full synthesis, place, route, generates
#   timing and utilization reports, writes the bitstream, and attempts to
#   program an attached Basys 3 board via Vivado Hardware Manager.
#==============================================================================

set SCRIPT_DIR [file normalize [file dirname [info script]]]
set BASE_DIR   [file normalize [file join $SCRIPT_DIR ".."]]
set OUTPUT_DIR [file normalize [file join $BASE_DIR "build" "vivado_out"]]

file mkdir $OUTPUT_DIR

puts "========================================================================"
puts "  Starting Vivado Flow for Basys 3 8-Phase CMOS Divider Demonstrator    "
puts "  Target Part: xc7a35tcpg236-1                                          "
puts "========================================================================"

# Step 1: Read Design Sources
puts "\n--> Reading RTL sources..."
read_verilog [file join $BASE_DIR "rtl" "latch_ring.v"]
read_verilog [file join $BASE_DIR "rtl" "top.v"]

# Step 2: Read Constraints
puts "\n--> Reading XDC constraints..."
read_xdc [file join $BASE_DIR "constr" "basys3.xdc"]

# Step 3: Synthesis
puts "\n--> Running Synthesis (top)..."
synth_design -top top -part xc7a35tcpg236-1 -flatten_hierarchy rebuilt
write_checkpoint -force [file join $OUTPUT_DIR "post_synth.dcp"]
report_utilization -file [file join $OUTPUT_DIR "post_synth_utilization.rpt"]

# Step 4: Logic Optimization
puts "\n--> Running Logic Optimization..."
opt_design

# Step 5: Placement
puts "\n--> Running Placement..."
place_design
write_checkpoint -force [file join $OUTPUT_DIR "post_place.dcp"]

# Step 6: Routing
puts "\n--> Running Routing..."
route_design
write_checkpoint -force [file join $OUTPUT_DIR "post_route.dcp"]

# Step 7: Reports
puts "\n--> Generating Implementation Reports..."
report_timing_summary -file [file join $OUTPUT_DIR "timing_summary.rpt"] -max_paths 10
report_utilization -file [file join $OUTPUT_DIR "post_route_utilization.rpt"]
report_drc -file [file join $OUTPUT_DIR "post_route_drc.rpt"]

# Step 8: Bitstream Generation
set BITSTREAM_FILE [file join $BASE_DIR "build" "basys3_divider_top.bit"]
puts "\n--> Writing Bitstream: $BITSTREAM_FILE ..."
write_bitstream -force $BITSTREAM_FILE

puts "\n========================================================================"
puts "  Bitstream generation complete: $BITSTREAM_FILE                        "
puts "========================================================================"

# Step 9: Optional Hardware Manager Programming
# Attempts to program an attached board if connected.
puts "\n--> Checking for connected Basys 3 hardware via Hardware Manager..."
if {[catch {
    open_hw_manager
    connect_hw_server -allow_non_jtag
    open_hw_target
    set dev [get_hw_devices xc7a35t_0]
    if {[llength $dev] > 0} {
        current_hw_device $dev
        set_property PROGRAM.FILE $BITSTREAM_FILE $dev
        puts "Programming hardware device $dev..."
        program_hw_devices $dev
        puts "SUCCESS: Basys 3 programmed successfully!"
    } else {
        puts "INFO: No xc7a35t_0 device detected on JTAG chain."
    }
    close_hw_target
    disconnect_hw_server
    close_hw_manager
} err_msg]} {
    puts "INFO: Hardware programming skipped or hardware not attached: $err_msg"
}

puts "\nVivado batch execution completed successfully."
