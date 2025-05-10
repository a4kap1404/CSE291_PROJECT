#!/bin/bash


counter=0.4
DESIGN=gcd
file=./designs/nangate45/gcd/config.mk
file2=Makefile

# Loop to run 3 iterations
for i in {1..2}
do
    # Update line 7 in config.mk file with the current counter value
    sed -i "7s/.*/export ABC_CLOCK_PERIOD_IN_PS = $counter/" $file

    export FLOW_VARIANT="${DESIGN}_run_${i}"
    
    # Update line 97 in Makefile with the current FLOW_VARIANT value
    #sed -i "50s/.*/export FLOW_VARIANT ?=${DESIGN}_run_${i}/" $file2
    
    # Set the FLOW_VARIANT and run floorplan
   # FLOW_VARIANT="${DESIGN}_run"
    DESIGN_CONFIG=$file make place
    
    #source ./scripts/global_place_skip_io.tcl 
    #source ./scripts/io_placement.tcl 


    # Increment counter by 0.01 using bc for floating-point arithmetic
    counter=$(echo "$counter + 0.01" | bc)

    # Optional: Debug output to check the values
    echo "Iteration $i - Counter: $counter"
done
