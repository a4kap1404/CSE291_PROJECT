








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


    cell_types_set.add('pin') 

    # Create one-hot encoding mapping
    cell_types = sorted(list(cell_types_set))

    with open("cell_types.txt", "w") as f:
        f.write("Cell types found:\n")
        for cell_type in cell_types:
            f.write(f"{cell_type}\n")

    cell_type_to_onehot = {}
    for i, cell_type in enumerate(cell_types):
        one_hot = [0] * len(cell_types)
        one_hot[i] = 1
        cell_type_to_onehot[cell_type] = one_hot

    return cell_type_to_onehot


def extract_sections_from_file(file_path, cell_type_to_onehot):
    pins = []
    instances = []
    nets = []

    with open(file_path, 'r') as f:
        lines = f.readlines()[9:]  # Skip header lines

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
            one_hot = cell_type_to_onehot.get('pin', [])
            pins.append({
                "vertex_id": int(vertex_id),
                "name": name,
                "cell_type":'pin',
                "cell_type_onehot": one_hot,
                "direction": direction,
                "x": int(x),
                "y": int(y)
            })

        elif in_instance_section and len(tokens) >= 10:
            vertex_id, instance_name, cell_name, _, _, is_fixed, x, y, width, height = tokens[:10]
            one_hot = cell_type_to_onehot.get(cell_name, [])
            instances.append({
                "vertex_id": int(vertex_id),
                "name": instance_name,
                "cell_type": cell_name,
                "cell_type_onehot": one_hot,
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
                    "cell_type": 'pin',
                    "cell_type_onehot": pin['cell_type_onehot'],
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
                    "cell_type": inst["cell_type"],
                    "cell_type_onehot": inst["cell_type_onehot"],
                    "x": inst['x'],
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
    return area_info


# Extract area info
area_info = extract_area_info("gcd_nangate45.txt")

# Prepare string to prepend
area_info_str = "### Design Area Information ###\n"
for key, val in area_info.items():
    area_info_str += f"{key} = {val}\n"
area_info_str += "\n"

# Prepend to nets.txt
with open("nets.txt", "r") as f:
    original_content = f.read()

with open("nets.txt", "w") as f:
    f.write(area_info_str + original_content)

print("Full area info prepended to nets.txt")



# === Main Usage ===
file_path = "gcd_nangate45.txt"
cell_type_to_onehot = one_hot_encoding(file_path)
pins, instances, nets = extract_sections_from_file(file_path, cell_type_to_onehot)
net_features = get_node_features(pins, instances, nets)

# Print sample output
from pprint import pprint
pprint(net_features[0])

# Write to file
with open('nets.txt', 'w') as f:
    for items in net_features:
        f.write('%s\n' % items)

area_info_str = "### Design Area Information ###\n"
for key, val in area_info.items():
    area_info_str += f"{key} = {val}\n"
area_info_str += "\n"

# Prepend to nets.txt
with open("nets.txt", "r") as f:
    original_content = f.read()

with open("nets.txt", "w") as f:
    f.write(area_info_str + original_content)

print("Full area info prepended to nets.txt")

print("File written successfully.")
