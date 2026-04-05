#!/bin/bash
# Evaluation script — the standard way to evaluate work in this environment.
set -e
export TMPDIR=/dev/shm
cd /home/user

mkdir -p scoring

RUN_NAME="${1:-run1}"
DATA_DIR="${2:-/home/user/data/common_shapes}"
OUTPUT_DIR="${3:-/home/user/checkpoints}"

echo "=== PartUV Evaluation ==="
echo "Run name: $RUN_NAME"
echo "Data dir: $DATA_DIR"
echo "Output dir: $OUTPUT_DIR"

# Check for results from the pipeline
RESULTS_FILE="$OUTPUT_DIR/results_${RUN_NAME}.json"
if [ -f "$RESULTS_FILE" ]; then
    echo "Found results file: $RESULTS_FILE"
    python3 -c "
import json
import os

results_file = '$RESULTS_FILE'
output_dir = '$OUTPUT_DIR'
run_name = '$RUN_NAME'

with open(results_file) as f:
    raw = json.load(f)

scores = {'common_shapes_comparison': {}}

for method, result in raw.items():
    agg = {}
    for k, v in result.items():
        if k not in ('per_mesh', 'method', 'success_rate'):
            agg[k] = v
    if agg:
        scores['common_shapes_comparison'][method] = agg

with open('scoring/scores.json', 'w') as f:
    json.dump(scores, f, indent=2)

print('scores.json written successfully')
print(json.dumps(scores, indent=2))
"
else
    echo "Results file not found: $RESULTS_FILE"
    echo '{}' > scoring/scores.json
fi

echo ""
echo "Evaluation complete!"
