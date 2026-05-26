#!/bin/bash
set -euo pipefail
export TMPDIR=/dev/shm
export PYTHONFAULTHANDLER=1
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}"
cd /home/user

DATA_DIR="${1:-/home/user/data/common_shapes}"
OUTPUT_DIR="${2:-/home/user/checkpoints/xatlas_repro}"
LIMIT="${3:-0}"

rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

echo "baseline.sh: data=$DATA_DIR output=$OUTPUT_DIR limit=$LIMIT"
python3 -u -m baseline.export_xatlas_dataset \
  --data-dir "$DATA_DIR" \
  --output-dir "$OUTPUT_DIR" \
  --limit "$LIMIT"

bash scripts/evaluate.sh single xatlas "$OUTPUT_DIR" xatlas.obj "$OUTPUT_DIR/results.json"
test -f "$OUTPUT_DIR/results.json" || { echo "ERROR: xatlas evaluation did not write $OUTPUT_DIR/results.json"; exit 1; }
