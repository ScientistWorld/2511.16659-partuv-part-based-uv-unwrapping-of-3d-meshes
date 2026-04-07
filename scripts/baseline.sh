#!/bin/bash
set -e
export TMPDIR=/dev/shm
cd /home/user

DATA_DIR="${1:-/home/user/data/common_shapes}"
OUTPUT_DIR="${2:-/home/user/checkpoints/xatlas_eval}"
RUN_NAME="${3:-xatlas_eval}"
LIMIT="${4:-0}"

mkdir -p "$OUTPUT_DIR"

python3 -m baseline.export_xatlas_dataset \
  --data-dir "$DATA_DIR" \
  --output-dir "$OUTPUT_DIR/$RUN_NAME" \
  --limit "$LIMIT"

bash scripts/evaluate.sh single xatlas "$OUTPUT_DIR/$RUN_NAME" xatlas.obj "$OUTPUT_DIR/results_${RUN_NAME}.json"
