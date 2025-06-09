import os
import re

raw_graph_dir = "./raw_graph_clustered"
logs_root = "./logs"

for filename in os.listdir(raw_graph_dir):
    if not filename.endswith("_formatted.txt"):
        continue

    # Parse DESIGN, TECH, FLOW
    parts = filename.replace("_formatted.txt", "").split("_")
    if len(parts) < 3:
        print(f"⚠️  Invalid file name format: {filename}")
        continue

    design = parts[0]
    tech = parts[1]
    flow = "_".join(parts[2:])  # In case flow name contains underscores

    # Locate the log file
    log_path = os.path.join(logs_root, tech, design, flow, "3_3_place_gp.log")
    if not os.path.exists(log_path):
        print(f"⚠️  Log not found: {log_path}")
        continue

    # Extract density value from log
    density = None
    with open(log_path, "r") as log_file:
        for line in log_file:
            match = re.search(r"global_placement\s+-density\s+([0-9.]+)", line)
            if match:
                density = match.group(1)
                break

    if not density:
        print(f"⚠️  No density value found in: {log_path}")
        continue

    # Update line 13 in the raw graph file
    formatted_path = os.path.join(raw_graph_dir, filename)
    with open(formatted_path, "r") as f:
        lines = f.readlines()

    if len(lines) < 13:
        print(f"⚠️  {filename} has less than 13 lines.")
        continue

    if "Place Density" in lines[12]:
        lines[12] = f"Place Density = {density}\n"
        with open(formatted_path, "w") as f:
            f.writelines(lines)
        print(f"✅ Updated {filename} with density = {density}")
    else:
        print(f"⚠️  Line 13 in {filename} does not contain 'Place Density'")