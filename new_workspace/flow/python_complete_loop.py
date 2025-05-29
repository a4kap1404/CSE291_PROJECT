### This script is just for Project #2 in CSE291A class
### It reads the sdc file and 3_2_place_iop.odb file
### Then convert the design into a hypergraph
### Then read global placement solution back and run the global placement incrementally
### Then perform legalization and detailed placement
# You can run this script in this manner:  openroad -python python_read_design.py

import sys
import os
import argparse
import pdn, odb, utl
from openroad import Tech, Design, Timing
import openroad as ord
import time
from pathlib import Path

import time
import resource


def load_design(techNode, floorplanOdbFile, sdcFile):
  tech = Tech()
  platform_dir = "./platforms/" + techNode + "/"
  libDir = Path(platform_dir + "lib/NLDM")
  lefDir = Path(platform_dir + "lef/")
  rcFile = platform_dir + "setRC.tcl"

  print("libDir: ", libDir)
  print("lefDir: ", lefDir)
  print("rcFile: ", rcFile)

  # Read technology files
  libFiles = libDir.glob('*.lib*')
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


def load_init_placement(file_name):
  with open(file_name, "r") as f:
    content = f.read().splitlines()
  f.close()

  block = ord.get_db_block()
  content = content[1:]
  for line in content:
    items = line.split(" ")
    if len(items) < 3:
      continue

    instName = items[0]
    x = int(float(items[1]))
    y = int(float(items[2]))

    # Set the position of the instance    
    inst = block.findInst(instName)
    inst.setLocation(x, y)

    '''
    to check in CLI:
    block = design.getBlock()
    insts = block.getInsts()
    inst_0 = insts[0]
    inst_0.getName()
    inst_0.getLocation()
    '''


def run_incremental_placement(design):
  # Configure and run global placement
  print("Running global placement")
  PLACE_DENSITY_LB_ADDON = lb_addon
  #os.environ["PLACE_DENSITY_LB_ADDON"] = "0.20"
  #place_density_lb = design.evalTclString(f"gpl::get_global_placement_uniform_density -pad_left {pad} -pad_right {pad}")
  place_density_lb = design.evalTclString(f"gpl::get_global_placement_uniform_density")
  #print(place_density_lb)
  place_density = float(place_density_lb) + ((1.0 - float(place_density_lb)) * float(PLACE_DENSITY_LB_ADDON)) + 0.01
  #print(place_density)

  start_time = time.time()
  start_usage = resource.getrusage(resource.RUSAGE_SELF)

  design.evalTclString("estimate_parasitics -placement")
  
  print(f"global_placement -density {place_density} -routability_driven -timing_driven -skip_initial_place -incremental")
  #design.evalTclString(f"global_placement -routability_driven -timing_driven -skip_initial_place -incremental")
  design.evalTclString(f"global_placement -density {place_density} -skip_initial_place -incremental")
  
  end_time = time.time()
  end_usage = resource.getrusage(resource.RUSAGE_SELF)

  elapsed_time = end_time - start_time
  user_cpu = end_usage.ru_utime - start_usage.ru_utime
  sys_cpu = end_usage.ru_stime - start_usage.ru_stime
  total_cpu = user_cpu + sys_cpu

  cpu_percent = (total_cpu / elapsed_time * 100) if elapsed_time > 0 else 0
  peak_mem_kb = int(end_usage.ru_maxrss if os.uname().sysname == "Linux" else end_usage.ru_maxrss / 1024)

  minutes, seconds = divmod(elapsed_time, 60)
  hours, minutes = divmod(int(minutes), 60)
  elapsed_str = f"{hours}:{minutes:02d}:{seconds:05.2f}" if hours else f"{minutes}:{seconds:05.2f}"

  print(f"Elapsed time: {elapsed_str}[h:]min:sec. "
    f"CPU time: user {user_cpu:.2f} sys {sys_cpu:.2f} ({int(cpu_percent)}%). "
    f"Peak memory: {peak_mem_kb}KB.")

  design.writeDef(results_path + "3_3_place_gp.def")
  design.writeDb(results_path + "3_3_place_gp.odb")


  # Run initial detailed placement
  site = design.getBlock().getRows()[0].getSite()
  max_disp_x = int((design.getBlock().getBBox().xMax() - design.getBlock().getBBox().xMin()) / site.getWidth())
  max_disp_y = int((design.getBlock().getBBox().yMax() - design.getBlock().getBBox().yMin()) / site.getHeight())
  print("Running intial Detailed Placement")
  design.getOpendp().detailedPlacement(max_disp_x, max_disp_y, "")
  
  design.writeDef(results_path + "3_5_place_dp.def")
  design.writeDb(results_path + "3_5_place_dp.odb")


if __name__ == "__main__":
    # You can run this script in this manner:  openroad -python python_read_design.py
    parser = argparse.ArgumentParser(description="Example script to perform global placement initialization using OpenROAD.")
    parser.add_argument("-d", default="ibex", help="Give the design name")
    parser.add_argument("-t", default="nangate45", help="Give the technology node")
    parser.add_argument("-p", default="./", help="Give the result path")
    parser.add_argument("-f", default="gcd_run_1_1_1", help="Give the flow variant")
    parser.add_argument("-b", default="0.2", help="Give the place density lb addon")
    parser.add_argument("-large_net_threshold", default="1000", help="Large net threshold. We should remove global nets like reset.")
    
    args = parser.parse_args()

    tech_node = args.t
    design = args.d
    path = args.p
    flow = args.f
    lb_addon = args.b
    large_net_threshold = int(args.large_net_threshold)

    results_path = path + "/new_output/"
    os.makedirs(os.path.dirname(results_path), exist_ok=True)

    #pred_file_path = "./pred/" + str(design) + "_" + str(tech_node) + "_" + str(flow) + "_predictions.txt"
    pred_file_path = "./pred_exp/" + str(design) + "_" + str(tech_node) + "_" + str(flow) + "_predictions.txt"

    floorplan_odb_file = path + "/3_2_place_iop.odb"
    sdc_file = path + "/2_floorplan.sdc"
    
    # Load the design
    tech, design = load_design(tech_node, floorplan_odb_file, sdc_file)

    # Load the initial placement and run incremental placement    
    load_init_placement(pred_file_path)
    run_incremental_placement(design)

    print("Finished running global placement and detailed placement.")
    print("\n")
    #print("*************************************************************************************************")
    #print("Please use the generated 3_3_place_gp.def and 3_3_place_gp.odb files for remaining flows.")
    #print("You can use OpenROAD GUI to visualize the placement: openroad -gui")
    #print("After opening the OpenROAD GUI, then go to File -> Open DB and select the 3_3_place_gp.odb file.")
    #print("*************************************************************************************************")
    #print("Good luck with your project!")
    #print("*************************************************************************************************")
