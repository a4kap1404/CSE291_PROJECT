     
def extract_ids_and_locations(input_file, output_file):
    in_instance_section = False
    in_net_section = False
    in_pin_section = True  # We're in the pin section until we hit "Instance information"

    extracted = []  # To store all (id, x_center, y_center)

    with open(input_file, 'r') as f:
        for _ in range(9):  # Skip the first 9 header lines
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
                    x_center = float(tokens[6])
                    y_center = float(tokens[7])
                    extracted.append((inst_id, x_center, y_center))
                except ValueError:
                    print(f"Skipping invalid instance line: {line}")
                continue

    # Write output
    with open(output_file, "w") as out_file:
        out_file.write("Instance ID, x_center, y_center\n")
        for inst_id, x, y in extracted:
            out_file.write(f"{inst_id}, {x}, {y}\n")

# Example usage
input_file = 'gcd_nangate45_final.txt'
output_file = 'extracted_locations_gcd_nangate45.txt'
extract_ids_and_locations(input_file, output_file)

print(f"Extracted pins and instances written to {output_file}.")










