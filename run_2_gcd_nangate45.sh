#!/bin/bash

counter=0.40
DESIGN=gcd
base_config=./designs/nangate45/gcd/config.mk
output_dir=./designs/nangate45/gcd/configs
mkdir -p "$output_dir"

MAX_JOBS=8  # Adjust based on your CPU/core limits
job_count=0

for i in $(seq 1 100); do
    formatted_counter=$(printf "%.2f" "$counter")
    FLOW_VARIANT="${DESIGN}_run_${i}"
    new_config="${output_dir}/config_${i}.mk"

    # Copy base config and modify clock period
    cp "$base_config" "$new_config"
    sed -i "7s/.*/export ABC_CLOCK_PERIOD_IN_PS = $formatted_counter/" "$new_config"

    # Launch each make process in the background
    (
        echo "Starting $FLOW_VARIANT with clock period $formatted_counter"
        export FLOW_VARIANT="$FLOW_VARIANT"
        DESIGN_CONFIG="$new_config" make place > "logs/${FLOW_VARIANT}.log" 2>&1
        echo "Finished $FLOW_VARIANT"
    ) &

    # Limit number of concurrent jobs
    ((job_count++))
    if [[ $((job_count % MAX_JOBS)) -eq 0 ]]; then
        wait  # Wait for all background jobs to finish before continuing
    fi

    # Increment counter
    counter=$(echo "$counter + 0.01" | bc)
done

wait  # Wait for any remaining jobs
echo "All placement runs completed."
