
#!/bin/bash
counter=0.4
DESIGN=gcd
file=./designs/nangate45/gcd/config.mk 
file2=Makefile
for i in {1..3}
do
	sed -i "7s/.*/export ABC_CLOCK_PERIOD_IN_PS = $counter/" $file
	sed -i "97s/.*/export FLOW_VARIANT ?=$(DESIGN)_run_$(counter)/" $file2
	FLOW_VARIANT="${DESIGN}_run"
	DESIGN_CONFIG=$file make floorplan
#counter=counter+0.01
       counter=$((counter + 0.01))


done
	
