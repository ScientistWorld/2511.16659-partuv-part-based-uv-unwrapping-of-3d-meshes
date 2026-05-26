#!/bin/bash
set -e
export TMPDIR=/dev/shm
export PYTHONPATH=/home/user/.local/lib/python3.12/site-packages
cd /home/user

DATA_DIR="${1:-/home/user/data/common_shapes}"
OUTPUT_DIR="${2:-/home/user/checkpoints/xatlas_repro}"
LIMIT="${3:-0}"

rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

python3 -m baseline.export_xatlas_dataset \
  --data-dir "$DATA_DIR" \
  --output-dir "$OUTPUT_DIR" \
  --limit "$LIMIT"

bash scripts/evaluate.sh single xatlas "$OUTPUT_DIR" xatlas.obj "$OUTPUT_DIR/results.json"
