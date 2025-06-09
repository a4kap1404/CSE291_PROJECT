#!/bin/bash

source ./set_variables.sh

base_config=./designs/$tech_node/$DESIGN/config.mk
output_dir=./designs/$tech_node/$DESIGN/configs
results_dir=./results/$tech_node/$DESIGN/
logs_dir=./logs/$tech_node/$DESIGN/
mkdir -p "$output_dir"

MAX_JOBS=1
job_count=0

if [ "$test_mode" == "1" ]; then
    echo "Test mode"
    FLOW_VARIANT="${DESIGN}_test"
    config="./designs/$tech_node/$DESIGN/config.mk"
    new_results_path="${results_dir}/$FLOW_VARIANT"

    echo "Starting test data generation"
    export FLOW_VARIANT=$FLOW_VARIANT
    openroad -python -exit python_get_graph.py -d "$DESIGN" -t "$tech_node" -p "$new_results_path" -f "$FLOW_VARIANT" -m "0" -large_net_threshold "$threshold" -a "$logs_dir"
    python python_format_inputs.py -d "$DESIGN" -t "$tech_node" -p "$new_results_path" -f "$FLOW_VARIANT" -c "0" -large_net_threshold "$threshold"
    openroad -python -exit python_get_graph.py -d "$DESIGN" -t "$tech_node" -p "$new_results_path" -f "$FLOW_VARIANT" -m "1" -large_net_threshold "$threshold" -a "$logs_dir"
    python python_format_labels.py -d "$DESIGN" -t "$tech_node" -p "$new_results_path" -f "$FLOW_VARIANT" -large_net_threshold "$threshold"
    echo "Finished $FLOW_VARIANT"
else
    echo "Running bulk data generation"
    for i in $(seq 1 1); do #5
        formatted_counter_i=$(printf "%.2f" "$counter_i")
        for j in $(seq 5 5); do #5
            formatted_counter_j=$(printf "%.2f" "$counter_j")
            for k in $(seq 3 3); do #4
                formatted_counter_k=$(printf "%.2f" "$counter_k")
                FLOW_VARIANT="${DESIGN}_run_${i}_${j}_${k}_test"
                new_config="${output_dir}/config_${i}_${j}_${k}.mk"
                new_results_path="${results_dir}/$FLOW_VARIANT"
                
                (
                    echo "Starting $FLOW_VARIANT graph and label extraction"
                    export FLOW_VARIANT=$FLOW_VARIANT
                    openroad -python -exit python_get_graph.py -d "$DESIGN" -t "$tech_node" -p "$new_results_path" -f "$FLOW_VARIANT" -m "0" -large_net_threshold "$threshold" -a "$logs_dir"
                    #python python_format_inputs.py -d "$DESIGN" -t "$tech_node" -p "$new_results_path" -f "$FLOW_VARIANT" -i "$counter_i" -j "$counter_j" -k "$counter_k" -c "0" -large_net_threshold "$threshold"
                    python python_format_inputs.py -d "$DESIGN" -t "$tech_node" -p "$new_results_path" -f "$FLOW_VARIANT" -c "0" -large_net_threshold "$threshold"
                    openroad -python -exit python_get_graph.py -d "$DESIGN" -t "$tech_node" -p "$new_results_path" -f "$FLOW_VARIANT" -m "1" -large_net_threshold "$threshold" -a "$logs_dir"
                    python python_format_labels.py -d "$DESIGN" -t "$tech_node" -p "$new_results_path" -f "$FLOW_VARIANT" -large_net_threshold "$threshold"
                    echo "Finished $FLOW_VARIANT"
                ) &

                ((job_count++))
                if [[ $((job_count % MAX_JOBS)) -eq 0 ]]; then
                    wait
                fi

                counter_k=$(echo "$counter_k + 0.2" | bc)
            done
            counter_j=$(echo "$counter_j + 14" | bc)
            counter_k=0.2
        done
        counter_i=$(echo "$counter_i + 0.4" | bc)
        counter_j=40
    done
fi

wait
echo "All data generation runs completed."