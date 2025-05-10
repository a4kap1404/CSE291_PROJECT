import subprocess

# Define your Make command and environment
design_config_path = "./designs/ihp-sg13g2/gcd/config.mk"
make_target = "floorplan"

# Construct and run the make command
cmd = ["make", f"DESIGN_CONFIG={design_config_path}", make_target]

try:
    result = subprocess.run(cmd, check=True, text=True, capture_output=True)
    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)
except subprocess.CalledProcessError as e:
    print("Error running command:")
    print(e.stdout)
    print(e.stderr)
