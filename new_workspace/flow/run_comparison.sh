
predictions="${1:-../../models/base_model/pred/}"
mode="${2:-0}" 


chmod +x run_designs.sh
chmod +x run_loop_batch.sh
chmod +x calculate_avg_imp.sh

./run_designs.sh \
	"$predictions" \
	"$mode"

./run_loop_batch.sh \
	"$predictions" \
	"$mode" 


./calculate_avg_imp.sh \
      "placement_metrics"
