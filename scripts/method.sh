#!/bin/bash
set -e
export TMPDIR=/dev/shm
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libstdc++.so.6
cd /home/user

DATA_DIR="${1:-/home/user/data/common_shapes}"
OUTPUT_DIR="${2:-/home/user/checkpoints/partuv_eval}"
RUN_NAME="${3:-partuv_eval}"
LIMIT="${4:-0}"
CKPT_PATH="/home/user/checkpoints/partfield/model_objaverse.ckpt"

mkdir -p "$OUTPUT_DIR"

python3 -m method.official_pipeline \
  --data-dir "$DATA_DIR" \
  --output-dir "$OUTPUT_DIR/$RUN_NAME" \
  --checkpoint-path "$CKPT_PATH" \
  --config-path /home/user/method/official_partuv/config/config.yaml \
  --threshold 1.25 \
  --limit "$LIMIT"

bash scripts/evaluate.sh single partuv "$OUTPUT_DIR/$RUN_NAME" final_components.obj "$OUTPUT_DIR/results_${RUN_NAME}.json"
