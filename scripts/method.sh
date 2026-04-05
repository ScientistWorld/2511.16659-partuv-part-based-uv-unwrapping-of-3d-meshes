#!/bin/bash
# Run the paper's proposed method (PartUV).
set -e
export TMPDIR=/dev/shm
cd /home/user

DATA_DIR="${1:-/home/user/data/common_shapes}"
OUTPUT_DIR="${2:-/home/user/checkpoints}"
RUN_NAME="${3:-partuv_run1}"

mkdir -p "$OUTPUT_DIR"

python3 -m method.pipeline \
    --data-dir "$DATA_DIR" \
    --output-dir "$OUTPUT_DIR" \
    --method partuv \
    --distortion-threshold 1.25 \
    --max-candidates 10 \
    --name "$RUN_NAME"

bash scripts/evaluate.sh "$RUN_NAME" "$DATA_DIR" "$OUTPUT_DIR"
