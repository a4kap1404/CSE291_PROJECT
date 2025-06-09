
#!/bin/bash

log_dir1="$1"
log_dir2="$2"
mode="$3"
tech="$4"
design="$5"
flow="$6"
output_file="$7"

extract_info() {
    local file="$1"
    local log_type="$2"  # "log1" or "log2"

    if [[ ! -f "$file" ]]; then
        echo "-1 -1 -1 -"
        return
    fi

    local last_line
    last_line=$(grep "\[NesterovSolve\] Iter:" "$file" | tail -1)
    local iter
    iter=$(echo "$last_line" | grep -oP 'Iter:\s*\K\d+' || echo "-1")
    local overflow
    overflow=$(echo "$last_line" | grep -oP 'overflow:\s*\K[\d\.]+' || echo "-1")
    local hpwl
    hpwl=$(echo "$last_line" | grep -oP 'HPWL:\s*\K[\d]+' || echo "-1")

    local cpu_time_line
    cpu_time_line=$(grep -oP 'CPU time:.*' "$file" | tail -1 || echo "-")

    local user_cpu_time="-"
    if [[ "$log_type" == "log1" ]]; then
        user_cpu_time=$(echo "$cpu_time_line" | grep -oP 'user\s*\K[\d\.]+' || echo "-")
    else
        user_cpu_time=$(echo "$cpu_time_line" | grep -oP 'user\s*\K[\d\.]+' || echo "-")
    fi

    echo "$iter $overflow $hpwl $user_cpu_time"
}

# Get filenames based on mode
if [[ "$mode" == "1" ]]; then
    file1="$log_dir1/$tech/$design/${design}_test.log"
    file2="$log_dir2/$tech/$design/${design}_test.log"
else
    file1="$log_dir1/$tech/$design/${design}_${flow}.log"
    file2="$log_dir2/$tech/$design/${design}_${flow}.log"
fi

# Extract metrics
read -r iter1 of1 hpwl1 time1 <<< $(extract_info "$file1" "log1")
read -r iter2 of2 hpwl2 time2 <<< $(extract_info "$file2" "log2")

# Compute improvements (fallback to "-" if any input is invalid)
hpwl_improvement="-"
time_improvement="-"
iter_improvement="-"

if [[ "$hpwl1" =~ ^[0-9]+$ && "$hpwl2" =~ ^[0-9]+$ ]]; then
    hpwl_improvement=$((hpwl1 - hpwl2))
fi

if [[ "$time1" =~ ^[0-9.]+$ && "$time2" =~ ^[0-9.]+$ ]]; then
    time_improvement=$(awk "BEGIN { printf \"%.2f\", $time1 - $time2 }")
fi

if [[ "$iter1" =~ ^[0-9]+$ && "$iter2" =~ ^[0-9]+$ ]]; then
    iter_improvement=$((iter1 - iter2))
fi

# Write header if file is empty
if [[ ! -s "$output_file" ]]; then
    printf "%-18s %10s %10s %12s %10s || %10s %10s %12s %10s || %10s %12s %10s\n" \
      "Design" "Default_Iter" "Default_OF" "Default_HPWL" "Default_Time" \
      "New_Iter" "New_OF" "New_HPWL" "New_Time" \
      "HPWL_Imp" "Time_Imp" "Iter_Imp" > "$output_file"
fi

# Append line
printf "%-18s %10s %10s %12s %10s || %10s %10s %12s %10s || %10s %12s %10s\n" \
  "$design" "$iter1" "$of1" "$hpwl1" "$time1" \
  "$iter2" "$of2" "$hpwl2" "$time2" \
  "$hpwl_improvement" "$time_improvement" "$iter_improvement" >> "$output_file"

echo "✅ Comparison written to $output_file"


