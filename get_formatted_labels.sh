#!/bin/bash

counter_i=0.5
counter_j=40
counter_k=0.4
DESIGN=ibex
tech_node=nangate45

base_config=./designs/$tech_node/$DESIGN/config.mk
output_dir=./designs/$tech_node/$DESIGN/configs
results_dir=./results/$tech_node/$DESIGN/
mkdir -p "$output_dir"

MAX_JOBS=8  # Adjust based on your CPU/core limits
job_count=0

for i in $(seq 1 5); do #5
    formatted_counter_i=$(printf "%.2f" "$counter_i")
    for j in $(seq 1 5); do #5
        formatted_counter_j=$(printf "%.2f" "$counter_j")
            for k in $(seq 1 4); do #4
                formatted_counter_k=$(printf "%.2f" "$counter_k")
                FLOW_VARIANT="${DESIGN}_run_${i}_${j}_${k}"
                new_config="${output_dir}/config_${i}_${j}_${k}.mk"
                new_results_path="${results_dir}/$FLOW_VARIANT"
                # Launch each make process in the background
                (
                    echo "Starting $FLOW_VARIANT global_place and detailed_place"
                    #export FLOW_VARIANT=$FLOW_VARIANT
                    python python_extract_final_info.py -d "$DESIGN" -t "$tech_node" -p "$new_results_path" -f "$FLOW_VARIANT"
                    #DESIGN_CONFIG="$new_config" make place > "logs/${FLOW_VARIANT}.log" 2>&1
                    echo "Finished $FLOW_VARIANT"
                ) &

                # Limit number of concurrent jobs
                ((job_count++))
                if [[ $((job_count % MAX_JOBS)) -eq 0 ]]; then
                    wait  # Wait for all background jobs to finish before continuing
                fi

                # Increment counter for utilization
                counter_k=$(echo "$counter_k + 0.1" | bc)
            done
            # Increment counter for utilization
            counter_j=$(echo "$counter_j + 7" | bc)
            counter_k=0.4
    done
    # Increment counter for aspect ratio after all inner loop iterations (j)
    counter_i=$(echo "$counter_i + 0.1" | bc)
    counter_j=40  # Reset utilization for the next outer loop iteration
done

wait  # Wait for any remaining jobs
echo "All placement runs completed."