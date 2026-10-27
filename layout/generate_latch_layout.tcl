# Magic layout script for divider core
puts "Generating layout..."
# Create a simple cell
cellname create divider_core
# Define a box (placeholder)
box 0 0 26.72um 15.53um
# Set output style
cif output gds2
# Save GDS
gds write divider_core.gds
puts "DRC check..."
drc check
drc count
# Save
save divider_core
quit