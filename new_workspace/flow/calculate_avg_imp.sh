#!/bin/bash
# Usage: ./calculate_avg_imp.sh placement_metrics

if [ $# -ne 1 ]; then
  echo "Usage: $0 <metrics_file>"
  return 1 2>/dev/null || exit 1
fi

file="placement_metrics"

awk -F '\\|\\|' '
NR > 1 {
    # Trim leading/trailing spaces of field 3
    gsub(/^ +| +$/, "", $3)
    n = split($3, arr, /[ \t]+/)
    if (n == 3) {
        hpwl_imp = arr[1]
        time_imp = arr[2]
        iter_imp = arr[3]

        sum_hpwl += hpwl_imp
        sum_time += time_imp
        sum_iter += iter_imp
        count++
    }
}
END {
    if(count > 0) {
        printf "Average HPWL_Imp: %.6f%%\n", sum_hpwl/count
        printf "Average Time_Imp: %.6f%%\n", sum_time/count
        printf "Average Iter_Imp: %.6f\n", sum_iter/count
    } else {
        print "No data found"
    }
}
' "$file"
