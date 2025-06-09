
#!/bin/bash

time_to_seconds() {
    local t=$1
    local m=${t%%:*}
    local s=${t#*:}
    echo "$(awk -v m=$m -v s=$s 'BEGIN { print m*60 + s }')"
}







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

    local elapsed_time_line
    elapsed_time_line=$(grep 'Elapsed time:' "$file" | tail -1)
    local elapsed_time="-"
    
    if [[ -n "$elapsed_time_line" ]]; then
        elapsed_time=$(echo "$elapsed_time_line" | grep -oP 'Elapsed time:\s*\K[\d:.]+' || echo "-")
    fi

    echo "$iter $overflow $hpwl $elapsed_time"
}

# Get filenames based on mode
if [[ "$mode" == "1" ]]; then
    file1="$log_dir1/$tech/$design/${design}_test/3_3_place_gp.log"
    file2="$log_dir2/$tech/$design/${design}_test.log"
    echo $file2
else
    file1="$log_dir1/$tech/$design/${design}_run_${flow}/3_3_place_gp.log"
    file2="$log_dir2/$tech/$design/${design}_${flow}.log"
fi

# Extract metrics
read -r iter1 of1 hpwl1 time1 <<< $(extract_info "$file1" "log1")
read -r iter2 of2 hpwl2 time2 <<< $(extract_info "$file2" "log2")

sec1=$(time_to_seconds "$time1")
sec2=$(time_to_seconds "$time2")


# Compute improvements (fallback to "-" if any input is invalid)
hpwl_improvement="-"
time_improvement="-"
iter_improvement="-"

if [[ "$hpwl1" =~ ^[0-9]+$ && "$hpwl2" =~ ^[0-9]+$ && "$hpwl1" -ne 0 ]]; then
    hpwl_improvement_percent=$(awk "BEGIN { printf \"%.2f\", (($hpwl1 - $hpwl2) / $hpwl1) * 100 }")
else
    hpwl_improvement_percent="N/A"
fi

if [[ "$sec1" =~ ^[0-9]+(\.[0-9]+)?$ && "$sec2" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
    not_zero=$(awk "BEGIN {print ($sec1 != 0) ? 1 : 0}")
    if [[ "$not_zero" -eq 1 ]]; then
        time_improvement_percent=$(awk "BEGIN { printf \"%.2f\", (($sec1 - $sec2) / $sec1) * 100 }")
    else
        time_improvement_percent="N/A"
    fi
else
    time_improvement_percent="N/A"
fi

if [[ "$iter1" =~ ^[0-9]+$ && "$iter2" =~ ^[0-9]+$ && "$iter1" -ne 0 ]]; then
    iter_improvement_percent=$(awk "BEGIN { printf \"%.2f\", ($iter1 - $iter2)  }")
else
    iter_improvement_percent="N/A"
fi



if [[ ! -s "$output_file" ]]; then
    printf "%-12s | %10s %10s %12s %10s || %10s %10s %12s %10s || %10s %10s %10s\n" \
      "Design" "Def_Iter" "Def_OF" "Def_HPWL" "Def_Time(s)" \
      "New_Iter" "New_OF" "New_HPWL" "New_Time(s)" \
      "HPWL_Imp(%%)" "Time_Imp(%%)" "Iter_Imp" > "$output_file"
fi

# Append formatted result row
printf "%-12s | %10s %10s %12s %10s || %10s %10s %12s %10s || %10s%% %10s%% %10s\n" \
  "$design $tech" "$iter1" "$of1" "$hpwl1" "$sec1" \
  "$iter2" "$of2" "$hpwl2" "$sec2" \
  "$hpwl_improvement_percent" "$time_improvement_percent" "$iter_improvement_percent" >> "$output_file"

echo "✓ Comparison written to $output_file"
