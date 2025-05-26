import subprocess

# Start both scripts in parallel
p1 = subprocess.Popen(['bash', 'run2_gcd_nangate45.sh'])
p2 = subprocess.Popen(['bash', 'run2_ibex_nangate45.sh'])


# Wait for both to finish
p1.wait()
p2.wait()

print("Both scripts completed.")
