def extract_data_from_file(file_path):
    pins = []
    instances = []

    #with open(file_path, 'r') as f:
       # lines = f.readlines()


    with open(file_path, 'r') as f:
        lines = f.readlines()[9:]  # Skip first 4 lines

    for line in lines:
        tokens = line.strip().split()

        if not tokens or tokens[0].startswith('*') or tokens[0].startswith("Instance") or tokens[0].startswith("Input/Output") or tokens[0].startswith("Nets"):
            continue

        # Pin info: vertex_id name direction x y
        if len(tokens) == 5:
             vertex_id, name, direction, x, y = tokens
             pins.append({
                "vertex_id": int(vertex_id),
                "name": name,
                "direction": direction,
                "x": int(x),
                "y": int(y)
            })

        # Instance info: vertex_id, instance_name, cell_name, isMacro, isSeq, isFixed, x, y, width, height
        elif len(tokens) >= 10:
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

    return pins, instances


pins, instances = extract_data_from_file("gcd_nangate45.txt")

print("Total pins:", len(pins))
print("Total instances:", len(instances))
print("First pin:", pins[0])
print("First instance:", instances[0])
print("List of all pins:\n")
for pin in pins:
    print(pin)
