#!/bin/bash
design_folder="${1:-./sample_predictions}"
mode="${2:-0}"  # default normal mode
pred_dir="./pred_exp"
config_base_dir="./designs"
log_dir1="./logs_actual"
log_dir2="./logs_predicted"
output_file="./placement_metrics"
> "$output_file"
chmod +x extract_placement_metrics.sh
for file_path in "$design_folder"/*predictions*; do
    filename=$(basename "$file_path")

    if [[ "$mode" -eq 1 ]]; then
        # Expect filenames like gcd_nangate45_test_predictions.txt
        # Extract first two parts as design and tech
        # Use regex to confirm format
        if [[ "$filename" =~ ^([^_]+)_([^_]+)_.*predictions ]]; then
            design="${BASH_REMATCH[1]}"
            tech="${BASH_REMATCH[2]}"
            flow=""  # no flow in test mode
            config_file="$config_base_dir/$tech/$design/config.mk"
        else
            echo "❌ Filename does not match expected test mode format: $filename"
            continue
        fi
    else
        # Normal mode: original regex for design, tech, flow
        if [[ "$filename" =~ ^([^_]+)_([^_]+)_.+_([0-9]+_[0-9]+_[0-9]+)_predictions ]]; then
            design="${BASH_REMATCH[1]}"
            tech="${BASH_REMATCH[2]}"
            flow="${BASH_REMATCH[3]}"
            config_file="$config_base_dir/$tech/$design/configs/config_$flow.mk"
        else
            echo "❌ Filename does not match expected format: $filename"
            continue
        fi
    fi

    if [[ ! -f "$config_file" ]]; then
        echo "❌ Config not found for design=$design, tech=$tech, flow=$flow at $config_file"
        continue
    fi

    # Try to extract PLACE_DENSITY_LB_ADDON
    lb_addon=$(grep -Po '^\s*(export\s+)?PLACE_DENSITY_LB_ADDON\s*=\s*\K\S+' "$config_file")

    flag=2  # default: neither found
    if [[ -n "$lb_addon" ]]; then
        flag=0
    else
        # Try PLACE_DENSITY if LB_ADDON not found
        lb_addon=$(grep -Po '^\s*(export\s+)?PLACE_DENSITY\s*=\s*\K\S+' "$config_file")
        if [[ -n "$lb_addon" ]]; then
            flag=1
        else
            lb_addon=""
        fi
    fi

    # Full path to the prediction file
    pred_file_path="$pred_dir/$filename"

    echo "▶ Running for design=$design, tech=$tech, flow=$flow, lb_addon=$lb_addon, flag=$flag"
    log_dir="logs_predicted"
    mkdir -p "$log_dir"
    if [[ "$mode" -eq 1 ]]; then
        log_path="$log_dir/$tech/$design/${design}_test.log"
        output_dir="./results/$tech/$design/${design}_test"
    else
        log_path="$log_dir/$tech/$design/${design}_${flow}.log"
        output_dir="./results/$tech/$design/${design}_run_${flow}"
    fi


    echo "The output directory is $output_dir"


    # Run OpenROAD with the Python script, passing flag and design_folder as -sp
    openroad -exit -python python_complete_loop.py \
        -d "$design" \
        -t "$tech" \
        -f "$flow" \
        -b "$lb_addon" \
        -flag "$flag" \
        -s "$design_folder" \
        -p "$output_dir" \
        -large_net_threshold 50 \
        > "$log_path" 2>&1


        ./extract_placement_metrics.sh \
        "$log_dir1" \
        "$log_dir2" \
        "$mode" \
        "$tech" \
        "$design" \
        "$flow" \
        "$output_file"

    echo "✔ Finished processing $filename, log saved to $log_path"
    echo
done
