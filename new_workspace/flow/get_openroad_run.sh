#!/bin/bash

source ./set_variables.sh

base_config=./designs/$tech_node/$DESIGN/config.mk
output_dir=./designs/$tech_node/$DESIGN/configs
mkdir -p "./logs"
mkdir -p "$output_dir"

MAX_JOBS=1
job_count=0

if [ "$test_mode" == "1" ]; then
    echo "Test mode"
    FLOW_VARIANT="${DESIGN}_test"
    config="./designs/$tech_node/$DESIGN/config.mk"

    echo "Starting test placement run"
    export FLOW_VARIANT=$FLOW_VARIANT
    DESIGN_CONFIG="$config" make place > "logs/${FLOW_VARIANT}.log" 2>&1
    echo "Finished $FLOW_VARIANT"
else
    echo "Running bulk placement runs"
    for i in $(seq 1 2); do #5
        formatted_counter_i=$(printf "%.2f" "$counter_i")
        for j in $(seq 1 2); do #5
            formatted_counter_j=$(printf "%.2f" "$counter_j")
            for k in $(seq 1 2); do #4
                formatted_counter_k=$(printf "%.2f" "$counter_k")
                FLOW_VARIANT="${DESIGN}_run_${i}_${j}_${k}"
                new_config="${output_dir}/config_${i}_${j}_${k}.mk"

                cp "$base_config" "$new_config"
                sed -i "s/^export CORE_UTILIZATION.*= *.*/export CORE_UTILIZATION = $formatted_counter_j/" "$new_config"
                sed -i "s/^export CORE_ASPECT_RATIO.*= *.*/export CORE_ASPECT_RATIO = $formatted_counter_i/" "$new_config"
                sed -i "s/^export PLACE_DENSITY_LB_ADDON.*= *.*/export PLACE_DENSITY_LB_ADDON = $formatted_counter_k/" "$new_config"

                (
                    echo "Starting $FLOW_VARIANT with utilization $formatted_counter_j, aspect ratio $formatted_counter_i and place density $formatted_counter_k"
                    export FLOW_VARIANT=$FLOW_VARIANT
                    DESIGN_CONFIG="$new_config" make place > "logs/${FLOW_VARIANT}.log" 2>&1
                    echo "Finished $FLOW_VARIANT"
                ) &

                ((job_count++))
                if [[ $((job_count % MAX_JOBS)) -eq 0 ]]; then
                    wait
                fi

                counter_k=$(echo "$counter_k + 0.2" | bc)
                #counter_k=$(echo "$counter_k + 0.1" | bc)
            done
            counter_j=$(echo "$counter_j + 14" | bc)
            #counter_j=$(echo "$counter_j + 7" | bc)
            counter_k=0.2
        done
        counter_i=$(echo "$counter_i + 0.4" | bc)
        #counter_i=$(echo "$counter_i + 0.1" | bc)
        counter_j=40
    done
fi

wait
echo "All placement runs completed."

