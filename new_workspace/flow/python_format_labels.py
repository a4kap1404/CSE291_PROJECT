import sys
import os
import argparse
import time
from pathlib import Path
     
def extract_ids_and_locations(input_file, output_file):
    in_instance_section = False
    in_net_section = False
    in_pin_section = True  # We're in the pin section until we hit "Instance information"

    extracted = []  # To store all (id, x_center, y_center)

    with open(input_file, 'r') as f:
        for _ in range(12):  # Skip the first 9 header lines
            next(f)

        for line in f:
            line = line.strip()
            if not line:
                continue

            if "Instance information" in line:
                in_instance_section = True
                in_net_section = False
                in_pin_section = False
                continue

            if "Nets information" in line:
                in_instance_section = False
                in_net_section = True
                in_pin_section = False
                continue

            tokens = line.split()

            # Collect from pin section (before instance info)
            if in_pin_section and len(tokens) >= 5:
                try:
                    inst_id = tokens[0]
                    x_center = float(tokens[3])
                    y_center = float(tokens[4])
                    extracted.append((inst_id, x_center, y_center))
                except ValueError:
                    print(f"Skipping invalid pin line: {line}")
                continue

            # Collect from instance section
            if in_instance_section and len(tokens) >= 10:
                try:
                    inst_id = tokens[0]
                    inst_type = tokens[2]
                    x_center = float(tokens[6])
                    y_center = float(tokens[7])
                    #if not inst_type.startswith('BUF_'):
                        #extracted.append((inst_id, x_center, y_center))
                    extracted.append((inst_id, x_center, y_center))
                except ValueError:
                    print(f"Skipping invalid instance line: {line}")
                continue
    f.close()

    # Write output
    with open(output_file, "w") as out_file:
        out_file.write("Instance_ID x_center y_center\n")
        for inst_id, x, y in extracted:
            out_file.write(f"{inst_id} {x} {y}\n")
    out_file.close()


if __name__ == "__main__":
    # You can run this script in this manner:  openroad -python python_read_design.py
    parser = argparse.ArgumentParser(description="Example script to perform global placement initialization using OpenROAD.")
    parser.add_argument("-d", default="ibex", help="Give the design name")
    parser.add_argument("-t", default="nangate45", help="Give the technology node")
    parser.add_argument("-p", default="nangate45", help="Give the result_path")
    parser.add_argument("-f", default="nangate45", help="Give the flow variant")
    parser.add_argument("-large_net_threshold", default="50", help="Large net threshold. We should remove global nets like reset.")
    
    args = parser.parse_args()

    tech_node = args.t
    design = args.d
    path = args.p
    flow = args.f
    large_net_threshold = int(args.large_net_threshold)

    # Example usage
    input_file = path + "/raw_graph/" + str(design) + "_" + str(tech_node) + "_" + str(flow) + "_label.txt"
    output_file = "./raw_graph/" + str(design) + "_" + str(tech_node) + "_" + str(flow) + "_label_formatted.txt"

    extract_ids_and_locations(input_file, output_file)

    print(f"Extracted pins and instances written to {output_file}.")










