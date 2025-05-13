#!/bin/bash

counter_i=0.45
counter_j=0.6
DESIGN=gcd
base_config=./designs/nangate45/gcd/config.mk
output_dir=./designs/nangate45/gcd/configs
mkdir -p "$output_dir"

MAX_JOBS=8  # Adjust based on your CPU/core limits
job_count=0

for i in $(seq 1 2); do
        formatted_counter_i=$(printf "%.2f" "$counter_i")
	for j in $(seq 1 2); do
    		formatted_counter_j=$(printf "%.2f" "$counter_j")
    		FLOW_VARIANT="${DESIGN}_run_${i}_${j}"
    		new_config="${output_dir}/config_${i}_${j}.mk"

    # Copy base config and modify clock period
    		cp "$base_config" "$new_config"
    		sed -i "20s/.*/export CORE_UTILIZATION = $formatted_counter_j/" "$new_config"
		sed -i "25s/.*/export CORE_ASPECT_RATIO = $formatted_counter_i/" "$new_config"

    # Launch each make process in the background
   		 (
        	        echo "Starting $FLOW_VARIANT with utilization $formatted_counter_j and aspect ratio $formatted_counter_i"
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
    		counter=$(echo "$counter_j + 0.05" | bc)
	done

        counter=$(echo "$counter_i + 0.05" | bc)
	counter_j=0.6
done
wait  # Wait for any remaining jobs
echo "All placement runs completed."
