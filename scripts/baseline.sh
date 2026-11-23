#!/bin/bash
# Run the xatlas baseline on a folder of meshes.
#   bash scripts/baseline.sh [input_dir] [output_dir]
set -euo pipefail
cd /home/user
IN_DIR="${1:-/home/user/data/downloads/common_shapes}"
OUT_DIR="${2:-/home/user/checkpoints/xatlas_repro/manual_outputs}"
exec bash /home/user/baseline/unwrap.sh "$IN_DIR" "$OUT_DIR"
