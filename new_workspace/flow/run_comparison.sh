
predictions="${1:-../../models/base_model/pred/}"
mode="${2:-0}" 


chmod +x run_designs.sh
chmod +x run_loop_batch.sh

./run_designs.sh \
	"$predictions" \
	"$mode"

./run_loop_batch.sh \
	"$predictions" \
	"$mode" \
