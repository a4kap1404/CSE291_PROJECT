export DESIGN_NAME = swerv_wrapper
export PLATFORM    = nangate45

# RTL_MP Settings
export RTLMP_MAX_INST = 30000
export RTLMP_MIN_INST = 5000
export RTLMP_MAX_MACRO = 12
export RTLMP_MIN_MACRO = 4 

export CORE_UTILIZATION = 40.00
export PLACE_DENSITY_LB_ADDON = 0.20

export ADDITIONAL_LEFS = $(PLATFORM_DIR)/lef/fakeram45_2048x39.lef $(PLATFORM_DIR)/lef/fakeram45_256x34.lef $(PLATFORM_DIR)/lef/fakeram45_64x21.lef
export CORE_ASPECT_RATIO = 0.50

#export DIE_AREA    = 0 0 1100 1000
#export CORE_AREA   = 10.07 11.2 1090 990 

export IO_CONSTRAINTS = $(DESIGN_HOME)/$(PLATFORM)/$(DESIGN_NAME)/io.tcl

export MACRO_PLACE_HALO = 10 10

export PLACE_DENSITY_LB_ADDON = 0.10
export TNS_END_PERCENT        = 100

export FASTROUTE_TCL = $(DESIGN_HOME)/$(PLATFORM)/$(DESIGN_NAME)/fastroute.tcl

export GPL_KEEP_OVERFLOW = 0

export CORE_UTILIZATION ?= 55
export CORE_ASPECT_RATIO = 0.50
