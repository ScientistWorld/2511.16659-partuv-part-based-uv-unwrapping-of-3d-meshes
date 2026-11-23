#!/bin/bash
# Run the reference PartUV on a folder of meshes.
#   bash scripts/method.sh [input_dir] [output_dir]
# Default: the visible training meshes -> checkpoints/partuv_repro/train_outputs (as evaluate_train.sh does).
set -euo pipefail
cd /home/user
IN_DIR="${1:-/home/user/data/downloads/common_shapes}"
OUT_DIR="${2:-/home/user/checkpoints/partuv_repro/manual_outputs}"
exec bash /home/user/method/unwrap.sh "$IN_DIR" "$OUT_DIR"
