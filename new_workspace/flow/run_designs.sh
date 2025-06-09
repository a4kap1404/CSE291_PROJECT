

#!/bin/bash

PREDICTION_DIR="${1:-./sample_predictions_new}"  # default to ./sample_predictions_new if not passed
MODE="${2:-0}" 
LOG_BASE_DIR="./logs_actual"


mkdir -p "$LOG_BASE_DIR"

for pred_file in "$PREDICTION_DIR"/*_predictions.txt; do
    filename=$(basename "$pred_file")
    echo "Checking file: $filename"
    if [[ "$MODE" -eq 1 ]]; then
        # Test mode: expect filenames like gcd_nangate45_test_predictions.txt
        if [[ "$filename" =~ ^([^_]+)_([^_]+)_.*predictions ]]; then

            design="${BASH_REMATCH[1]}"
            tech="${BASH_REMATCH[2]}"
            flow=""
            FLOW_VARIANT="${design}_test"

            config_path="./designs/$tech/$design/config.mk"
        else
            echo "❌ Filename does not match expected test mode pattern: $filename"
            continue
        fi
    else
        # Normal mode: expect filenames like gcd_nangate45_gcd_run_1_2_4_predictions.txt
        if [[ "$filename" =~ ^([^_]+)_([^_]+)_.+_run_([0-9]+_[0-9]+_[0-9]+)_predictions\.txt$ ]]; then
            design="${BASH_REMATCH[1]}"
            tech="${BASH_REMATCH[2]}"
            flow="${BASH_REMATCH[3]}"
            FLOW_VARIANT="${design}_run_${flow}"

            config_path="./designs/$tech/$design/configs/config_${flow}.mk"
        else
            echo "❌ Filename does not match expected pattern: $filename"
            continue
        fi
    fi

    if [[ ! -f "$config_path" ]]; then
        echo "❌ Config not found for design=$design, tech=$tech, flow=$flow at $config_path"
        continue
    fi

    # Prepare log directory and path
    log_dir="$LOG_BASE_DIR/$tech/$design"
    mkdir -p "$log_dir"

    if [[ "$MODE" -eq 1 ]]; then
        log_path="$log_dir/${design}_test.log"
    else
        log_path="$log_dir/${design}_run_${flow}.log"
    fi
    

    echo "▶ Running placement for $FLOW_VARIANT using config $config_path"
    
    export FLOW_VARIANT=$FLOW_VARIANT

    DESIGN_CONFIG="$config_path" make place > "$log_path" 2>&1

    echo "✔ Finished $FLOW_VARIANT, log saved to $log_path"
    echo
done
