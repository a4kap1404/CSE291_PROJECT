import sys
import argparse
import pdn, odb, utl
from openroad import Tech, Design, Timing
import openroad as ord
import time
from pathlib import Path


def load_design(techNode, floorplanOdbFile, sdcFile):
  tech = Tech()
  platform_dir = "./platforms/" + techNode + "/"
  libDir = Path(platform_dir + "lib/")
  lefDir = Path(platform_dir + "lef/")
  rcFile = platform_dir + "setRC.tcl"

  print("libDir: ", libDir)
  print("lefDir: ", lefDir)
  print("rcFile: ", rcFile)

  # Read technology files
  libFiles = libDir.glob('*.lib')
  lefFiles = lefDir.glob('*.lef')
  for libFile in libFiles:
    print("Reading library file: %s\n" % libFile)
    tech.readLiberty(libFile.as_posix())
  
  techLefFiles = lefDir.glob("*tech*.lef")
  for techLefFile in techLefFiles:
    tech.readLef(techLefFile.as_posix())
  for lefFile in lefFiles:
    tech.readLef(lefFile.as_posix())
  
  design = Design(tech)

  # read the odb file
  design.readDb(floorplanOdbFile)
  design.evalTclString("read_sdc %s"%sdcFile)
  design.evalTclString("source " + rcFile)

  return tech, design


def run_incremental_placement(design):
  # Configure and run global placement
  print("###run global placement###")
  design.evalTclString("global_placement -incremental")

  #print("Please use the generated 3_3_place_gp.def and 3_3_place_gp.odb files for remaining flows.")
  design.writeDef(path + "/3_3_place_gp.def")
  design.writeDb(path + "/3_3_place_gp.odb")

  design.evalTclString("detailed_placement")
  
  design.writeDef(path + "/3_5_place_dp.def")
  design.writeDb(path + "/3_5_place_dp.odb")



if __name__ == "__main__":
    # You can run this script in this manner:  openroad -python python_read_design.py
    parser = argparse.ArgumentParser(description="Script to generate labels.")
    parser.add_argument("-d", default="ibex", help="Give the design name")
    parser.add_argument("-t", default="nangate45", help="Give the technology node")
    parser.add_argument("-p", default="nangate45", help="Give the result_path")
    parser.add_argument("-large_net_threshold", default="1000", help="Large net threshold. We should remove global nets like reset.")
    
    args = parser.parse_args()

    tech_node = args.t
    design = args.d
    path = args.p
    large_net_threshold = int(args.large_net_threshold)

    #path = "./results/" + tech_node + "/" + design + "/base"
    #path = "./results/" + tech_node + "/" + design + "/" + design +"_run_1"

    floorplan_odb_file = path + "/3_2_place_iop.odb"
    sdc_file = path + "/2_floorplan.sdc"

    #floorplan_odb_file = path + "/3_5_place_dp.odb"
    #sdc_file = path + "/3_place.sdc"
    # Load the design
    tech, design = load_design(tech_node, floorplan_odb_file, sdc_file)

    run_incremental_placement(design)