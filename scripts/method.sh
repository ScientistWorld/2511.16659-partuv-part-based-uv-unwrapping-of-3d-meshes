#!/bin/bash
set -euo pipefail
export TMPDIR=/dev/shm
export PYTHONFAULTHANDLER=1
export PYTHONNOUSERSITE=1
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export OPENBLAS_CORETYPE="${OPENBLAS_CORETYPE:-GENERIC}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}"
cd /home/user

DATA_DIR="${1:-/home/user/data/common_shapes}"
OUTPUT_DIR="${2:-/home/user/checkpoints/partuv_repro}"
LIMIT="${3:-0}"
CKPT_PATH="${PARTFIELD_CHECKPOINT:-/home/user/data/downloads/partfield/model_objaverse.ckpt}"

if [ ! -f "$CKPT_PATH" ] && [ -f /home/user/checkpoints/partfield/model_objaverse.ckpt ]; then
  CKPT_PATH="/home/user/checkpoints/partfield/model_objaverse.ckpt"
fi

rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"
test -f "$CKPT_PATH" || { echo "ERROR: PartField checkpoint missing. Run scripts/download.sh first."; exit 1; }

echo "method.sh: data=$DATA_DIR output=$OUTPUT_DIR limit=$LIMIT checkpoint=$CKPT_PATH"
python3 -u -m method.official_pipeline \
  --data-dir "$DATA_DIR" \
  --output-dir "$OUTPUT_DIR" \
  --checkpoint-path "$CKPT_PATH" \
  --config-path /home/user/method/official_partuv/config/config.yaml \
  --threshold 1.25 \
  --limit "$LIMIT"

bash scripts/evaluate.sh single partuv "$OUTPUT_DIR" final_components.obj "$OUTPUT_DIR/results.json"
test -f "$OUTPUT_DIR/results.json" || { echo "ERROR: PartUV evaluation did not write $OUTPUT_DIR/results.json"; exit 1; }
