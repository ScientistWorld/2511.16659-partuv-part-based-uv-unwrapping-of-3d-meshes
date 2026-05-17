#!/bin/bash
set -e
export TMPDIR=/dev/shm
export PYTHONPATH=/home/user/.local/lib/python3.12/site-packages
cd /home/user

DATA_DIR="${1:-/home/user/data/common_shapes}"
OUTPUT_DIR="${2:-/home/user/checkpoints/partuv_repro}"
RUN_NAME="${3:-partuv_repro}"
LIMIT="${4:-0}"
CKPT_PATH="/home/user/checkpoints/partfield/model_objaverse.ckpt"

mkdir -p "$OUTPUT_DIR"

python3 -m method.official_pipeline \
  --data-dir "$DATA_DIR" \
  --output-dir "$OUTPUT_DIR" \
  --checkpoint-path "$CKPT_PATH" \
  --config-path /home/user/method/official_partuv/config/config.yaml \
  --threshold 1.25 \
  --limit "$LIMIT"

bash scripts/evaluate.sh single partuv "$OUTPUT_DIR" final_components.obj "$OUTPUT_DIR/results.json"
