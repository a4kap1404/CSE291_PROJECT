def extract_sections_from_file(file_path):
    pins = []
    instances = []
    nets = []

    with open(file_path, 'r') as f:
        lines = f.readlines()[9:]  # Skip the first 4 header lines

    in_instance_section = False
    in_net_section = False

    for line in lines:
        line = line.strip()
        tokens = line.split()

        if not tokens or tokens[0].startswith('*'):
            continue

        # Check for section headers
        if "Instance information" in line:
            in_instance_section = True
            in_net_section = False
            continue

        if "Nets information" in line:
            in_instance_section = False
            in_net_section = True
            continue

        # Pin section (before instance info)
        if not in_instance_section and not in_net_section and len(tokens) == 5:
             vertex_id, name, direction, x, y = tokens
             pins.append({
                "vertex_id": int(vertex_id),
                "name": name,
                "direction": direction,
                "x": int(x),
                "y": int(y)
            })

        # Instance section
        elif in_instance_section and len(tokens) >= 10:
            vertex_id, instance_name, cell_name, _, _, is_fixed, x, y, width, height = tokens[:10]
            instances.append({
                "vertex_id": int(vertex_id),
                "name": instance_name,
                "cell_type": cell_name,
                "is_fixed": is_fixed == "True",
                "x": int(x),
                "y": int(y),
                "area": int(width) * int(height)
            })

        # Nets section (driver + sinks)
        elif in_net_section:
            net_nodes = list(map(int, tokens))
            if len(net_nodes) >= 1:
                driver = net_nodes[0]
                sinks = net_nodes[1:]
                nets.append({
                    "driver": driver,
                    "sinks": sinks
                })

    return pins, instances, nets


pins, instances, nets = extract_sections_from_file("gcd_nangate45.txt")

print("Total Pins:", len(pins))
print("Total Instances:", len(instances))
print("Total Nets:", len(nets))

print("\nFirst Pin:", pins[0])
print("\nFirst Instance:", instances[0])
print("\nFirst Net:", nets[0])

# assign list

def get_node_features(pins, instances, nets):
    # Build quick lookup dictionaries for fast access
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
                    "x": pin['x'],
                    "y": pin['y'],
                    "is_fixed": True,  # Pins are always fixed
                    "area": 0          # Pins don't have area
                }
            elif node_id in instance_dict:
                inst = instance_dict[node_id]
                feature = {
                    "id": node_id, 
                    "x": inst['x'],
                    "y": inst['y'],
                    "is_fixed": inst['is_fixed'],
                    "area": inst['area']
                }
            else:
                # If node_id is not found in either, skip or raise an error
                continue

            if role == 'driver':
                net_data['driver'] = feature
            else:
                net_data['sinks'].append(feature)

        net_features.append(net_data)

    return net_features


net_features = get_node_features(pins, instances, nets)

# Example: print first net's node features
from pprint import pprint
pprint(net_features[0])
# open file
with open('nets.txt', 'w+') as f:
    count = 0 
    # write elements of list
    for items in net_features:
        f.write('%s\n' %items)
    
    print("File written successfully")


# close the file
f.close()    

