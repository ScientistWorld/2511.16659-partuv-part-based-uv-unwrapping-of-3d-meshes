#!/bin/bash
set -e
export TMPDIR=/dev/shm
export PYTHONPATH=/home/user/.local/lib/python3.12/site-packages
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

python3 -m method.official_pipeline \
  --data-dir "$DATA_DIR" \
  --output-dir "$OUTPUT_DIR" \
  --checkpoint-path "$CKPT_PATH" \
  --config-path /home/user/method/official_partuv/config/config.yaml \
  --threshold 1.25 \
  --limit "$LIMIT"

bash scripts/evaluate.sh single partuv "$OUTPUT_DIR" final_components.obj "$OUTPUT_DIR/results.json"
