import sys
import os
import argparse
import time
from pathlib import Path

def one_hot_encoding(file_path): 
    cell_types_set = set()
    in_instance_section = False
    in_net_section = False

    with open(file_path, 'r') as f:
        for _ in range(9):
            next(f)
    
        for line in f:
            tokens = line.strip().split()

            if "Instance information" in line:
                in_instance_section = True
                in_net_section = False
                continue

            if "Nets information" in line:
                in_instance_section = False
                in_net_section = True
                continue

            if in_instance_section and len(tokens) >= 10:
                cell_name = tokens[2]
                cell_types_set.add(cell_name)
    f.close()


    cell_types_set.add('pin') 

    # Create one-hot encoding mapping
    cell_types = sorted(list(cell_types_set))

    with open("cell_types.txt", "w") as f:
        f.write("Cell types found:\n")
        for cell_type in cell_types:
            f.write(f"{cell_type}\n")
    f.close()

    cell_type_to_onehot = {}
    for i, cell_type in enumerate(cell_types):
        one_hot = [0] * len(cell_types)
        one_hot[i] = 1
        cell_type_to_onehot[cell_type] = one_hot

    return cell_type_to_onehot


#def extract_sections_from_file(file_path, cell_type_to_onehot):
def extract_sections_from_file(file_path):
    pins = []
    instances = []
    nets = []

    with open(file_path, 'r') as f:
        lines = f.readlines()[9:]  # Skip header lines
    f.close()

    in_instance_section = False
    in_net_section = False

    for line in lines:
        tokens = line.strip().split()

        if not tokens or tokens[0].startswith('*'):
            continue 

        if "Instance information" in line:
            in_instance_section = True
            in_net_section = False
            continue

        if "Nets information" in line:
            in_instance_section = False
            in_net_section = True
            continue

        if not in_instance_section and not in_net_section and len(tokens) == 5:
            vertex_id, name, direction, x, y = tokens
            #one_hot = cell_type_to_onehot.get('pin', [])
            pins.append({
                "vertex_id": int(vertex_id),
                "name": name,
                #"cell_type":'pin',
                #"cell_type_onehot": one_hot,
                "direction": direction,
                "x": int(x),
                "y": int(y)
            })

        elif in_instance_section and len(tokens) >= 10:
            vertex_id, instance_name, cell_name, isMacro, isSeq, is_fixed, x, y, width, height = tokens[:10]
            #one_hot = cell_type_to_onehot.get(cell_name, [])
            instances.append({
                "vertex_id": int(vertex_id),
                "name": instance_name,
                #"cell_type": cell_name,
                #"cell_type_onehot": one_hot,
                "is_macro": isMacro == "True",
                "is_seq": isSeq == "True",
                "is_fixed": is_fixed == "True",
                "x": int(x),
                "y": int(y),
                "area": int(width) * int(height)
            })

        elif in_net_section:
            net_nodes = list(map(int, tokens))
            if len(net_nodes) >= 1:
                nets.append({
                    "driver": net_nodes[0],
                    "sinks": net_nodes[1:]
                })

    return pins, instances, nets


def get_node_features(pins, instances, nets):
    pin_dict = {pin['vertex_id']: pin for pin in pins}
    instance_dict = {inst['vertex_id']: inst for inst in instances}

    net_features = []

    for net in nets:
        net_data = {"driver": {}, "sinks": []}

        for role, node_id in [('driver', net['driver'])] + [('sink', sid) for sid in net['sinks']]:
            if node_id in pin_dict:
                pin = pin_dict[node_id]
                feature = {
                    "id": node_id,
                    "name": pin['name'],
                    "direction": pin['direction'],
                    #"cell_type": 'pin',
                    #"cell_type_onehot": pin['cell_type_onehot'],
                    "is_macro": False,
                    "is_seq": False,
                    "x": pin['x'],
                    "y": pin['y'],
                    "is_fixed": True,
                    "area": 0
                }
            elif node_id in instance_dict:
                inst = instance_dict[node_id]
                feature = {
                    "id": node_id,
                    "name": inst["name"],
                    "direction": 'false',
                    #"cell_type": inst["cell_type"],
                    #"cell_type_onehot": inst["cell_type_onehot"],
                    "is_macro": inst['is_macro'],
                    "is_seq": inst['is_seq'],
                    #"x": core_x_center,
                    "x": inst['x'],
                    #"y": core_y_center,
                    "y": inst['y'],
                    "is_fixed": inst['is_fixed'],
                    "area": inst['area']
                }
            else:
                continue

            if role == 'driver':
                net_data['driver'] = feature
            else:
                net_data['sinks'].append(feature)

        net_features.append(net_data)

    return net_features

def extract_area_info(file_path):
    area_info = {}
    with open(file_path, "r") as f:
        for line in f:
            if "Die width" in line:
                area_info["die_width"] = int(line.strip().split(":")[1].split()[0])
            elif "Die height" in line:
                area_info["die_height"] = int(line.strip().split(":")[1].split()[0])
            elif "Core width" in line:
                area_info["core_width"] = int(line.strip().split(":")[1].split()[0])
            elif "Core height" in line:
                area_info["core_height"] = int(line.strip().split(":")[1].split()[0])
            elif "Core region" in line:
                coords = line.strip().split(":")[1].split(",")
                for c in coords:
                    key, val = c.strip().split("=")
                    area_info[key.strip()] = int(val.strip())
    f.close()
     
    return area_info

if __name__ == "__main__":

    # You can run this script in this manner:  openroad -python python_read_design.py
    parser = argparse.ArgumentParser(description="Example script to extract input features.")
    parser.add_argument("-d", default="ibex", help="Give the design name")
    parser.add_argument("-t", default="nangate45", help="Give the technology node")
    parser.add_argument("-p", default="nangate45", help="Give the result_path")
    parser.add_argument("-f", default="nangate45", help="Give the flow variant")
    parser.add_argument("-i", default="0.5", help="Give the core aspect ratio")
    parser.add_argument("-j", default="40", help="Give the utilization")
    parser.add_argument("-k", default="0.4", help="Give the place density")
    parser.add_argument("-large_net_threshold", default="1000", help="Large net threshold. We should remove global nets like reset.")
    
    args = parser.parse_args()

    tech_node = args.t
    design = args.d
    path = args.p
    flow = args.f
    aspect_ratio = float(args.i)
    util = float(args.j)
    place_density = float(args.k)
    large_net_threshold = int(args.large_net_threshold)
    file_path = path + "/raw_graph/" + str(design) + "_" + str(tech_node) + "_" + str(flow) + ".txt"
    hg_file_name = "./raw_graph/" + str(design) + "_" + str(tech_node) + "_" + str(flow) + "_formatted.txt"
    os.makedirs(os.path.dirname(hg_file_name), exist_ok=True)
    f = open(hg_file_name, "w")
    f.close()

    # === Main Usage ===
    #file_path = "gcd_nangate45.txt"
    #cell_type_to_onehot = one_hot_encoding(file_path)
    #pins, instances, nets = extract_sections_from_file(file_path, cell_type_to_onehot)
    pins, instances, nets = extract_sections_from_file(file_path)
    net_features = get_node_features(pins, instances, nets)

    # Extract area info
    area_info = extract_area_info(file_path)
    #core_x_center = (area_info["lx"] + area_info["ux"]) // 2
    #core_y_center = (area_info["ly"] + area_info["uy"]) // 2

    area_info_str = "### Design Area Information ###\n"
    for key, val in area_info.items():
        area_info_str += f"{key} = {val}\n"
    area_info_str += "\n"

    # Print sample output
    from pprint import pprint
    pprint(net_features[0])

    # Write to file
    with open(hg_file_name, 'a') as f:
        f.write(area_info_str)
        f.write(f"Core Aspect Ratio = " + str(aspect_ratio) + "\n") 
        f.write("Utilization = " + str(util) + "\n")
        f.write("Place Density = " + str(place_density) + "\n\n")  
        for items in net_features:
            f.write('%s\n' % items)
    f.close()

    # Prepend to nets.txt
    #with open("nets.txt", "r") as f:
    #    original_content = f.read()

    #with open("nets.txt", "w") as f:
    #    f.write(area_info_str + original_content)

    print("Full area info prepended to nets.txt")
    print("File written successfully.")
