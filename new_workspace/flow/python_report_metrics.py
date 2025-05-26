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

def load_design(techNode, odb_path, sdc_path):
    tech = Tech()
    platform_dir = "./platforms/" + techNode + "/"
    lib_dir = Path(platform_dir, "lib")
    lef_dir = Path(platform_dir, "lef")
    rc_file = platform_dir + "setRC.tcl"

    for lib_file in lib_dir.glob("*.lib"):
        print("  -", lib_file)
        tech.readLiberty(str(lib_file))

    for tech_lef in lef_dir.glob("*tech*.lef"):
        print("  -", tech_lef)
        tech.readLef(str(tech_lef))
    for lef_file in lef_dir.glob("*.lef"):
        tech.readLef(str(lef_file))

    design = Design(tech)
    design.readDb(str(odb_path))
    design.evalTclString(f'read_sdc {sdc_path}')
    design.evalTclString(f'source {rc_file}')

    return tech, design

def run_for_all_designs(results_dir, tech_node):
    reports_dir = Path("./my_custom_reports")
    reports_dir.mkdir(exist_ok=True)

    for design_dir in Path(results_dir).glob("gcd_run_*_*_*"):
        if not design_dir.is_dir():
            continue

        design_name = design_dir.name
        odb_path = design_dir / "3_place.odb"
        sdc_path = design_dir / "3_place.sdc"

        if not odb_path.exists() or not sdc_path.exists():
            print(f"Skipping {design_name}: Missing odb or sdc")
            continue

        print(f"\nProcessing design: {design_name}")
        _, design = load_design(tech_node, odb_path, sdc_path)

        design.evalTclString(f'set ::env(REPORTS_DIR) "./my_custom_reports"')
        design.evalTclString(f'set ::env(SCRIPTS_DIR) "./scripts"')
        design.evalTclString(f'set ::env(REPORT_SUFFIX) "place_{design_name}"')
        design.evalTclString(f'set ::env(FLOW_VARIANT) "{design_name}"')

        design.evalTclString('puts "Sourcing load.tcl"')
        design.evalTclString('source ./scripts/load.tcl')
        design.evalTclString('estimate_parasitics -placement')
        design.evalTclString('puts "Sourcing report_metrics.tcl"')
        design.evalTclString('source ./scripts/report_metrics.tcl')

        report_cmd = f'report_metrics 3 "{design_name}" true false'
        print(f"Running: {report_cmd}")
        design.evalTclString(report_cmd)

        print(f"Finished: {design_name}")
        print(f"Report saved to: ./my_custom_reports/{design_name}.rpt")
        print("--------------------------------------------------")

# Main script entry
if __name__ == "__main__":
    run_for_all_designs("./results/nangate45/gcd", tech_node="nangate45")
    
