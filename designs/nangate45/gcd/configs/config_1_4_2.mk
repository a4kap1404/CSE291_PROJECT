export DESIGN_NAME = gcd
export PLATFORM    = nangate45

export VERILOG_FILES = $(DESIGN_HOME)/src/$(DESIGN_NAME)/gcd.v
export SDC_FILE      = $(DESIGN_HOME)/$(PLATFORM)/$(DESIGN_NAME)/constraint.sdc
export ABC_AREA      = 1

# Adders degrade GCD
export ADDER_MAP_FILE :=

export CORE_UTILIZATION ?= 55
export CORE_UTILIZATION = 61.00
export PLACE_DENSITY_LB_ADDON = 0.30
export REMOVE_CELLS_FOR_EQY   = TAPCELL*
export CORE_ASPECT_RATIO = 0.50
export CORE_ASPECT_RATIO = 0.50
