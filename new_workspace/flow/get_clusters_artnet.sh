#!/bin/bash

source ./set_variables.sh

base_config=./designs/$tech_node/$DESIGN/config.mk
output_dir=./designs/$tech_node/$DESIGN/configs
results_dir=./results/$tech_node/$DESIGN/
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
    python python_format_inputs.py -d "$DESIGN" -t "$tech_node" -p "$new_results_path" -f "$FLOW_VARIANT" -c "1" -large_net_threshold "$threshold"
    python python_cluster_graph.py -d "$DESIGN" -t "$tech_node" -p "$new_results_path" -f "$FLOW_VARIANT" -m "0" > ./check
    echo "Finished $FLOW_VARIANT"
else
    echo "Running bulk data generation"
    for file in ./raw_graph_artnet/artnet_design_*_asap7_formatted.txt; do
        filename=$(basename "$file")
        FLOW_VARIANT=$(echo "$filename" | sed -E 's/artnet_design_([^_]+_[^_]+)_asap7_formatted.txt/\1/')
        echo "$FLOW_VARIANT"
        new_results_path="${results_dir}/$FLOW_VARIANT"    
        (
            echo "Starting $FLOW_VARIANT graph and label extraction"
            export FLOW_VARIANT=$FLOW_VARIANT
            python python_format_inputs_artnet.py -d "$DESIGN" -t "$tech_node" -p "$new_results_path" -f "$FLOW_VARIANT" -c "1" -large_net_threshold "$threshold"
            python python_cluster_graph_artnet.py -d "$DESIGN" -t "$tech_node" -p "$new_results_path" -f "$FLOW_VARIANT" -m "0" > ./check
            echo "Finished $FLOW_VARIANT"
        ) &
        
        ((job_count++))
        if [[ $((job_count % MAX_JOBS)) -eq 0 ]]; then
            wait
        fi
    done
fi

wait
echo "All data generation runs completed."