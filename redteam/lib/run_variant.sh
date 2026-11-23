#!/bin/bash
# Usage: run_variant.sh <name> [partuv_variant.py args...]
# Runs the released PartUV pipeline with the given knobs on the held-out meshes (plus one
# train mesh for registration), then runs the hidden test. Resumable: finished meshes are kept.
set -uo pipefail
NAME="$1"; shift
[ -n "$NAME" ] || { echo "missing name"; exit 2; }
source /home/user/redteam/lib/env.sh
cd /home/user
CKPT="${PARTFIELD_CHECKPOINT:-/home/user/data/downloads/partfield/model_objaverse.ckpt}"
[ -f "$CKPT" ] || CKPT=/home/user/checkpoints/partfield/model_objaverse.ckpt
mkdir -p "$ROOT/partuv_repro"
python3 -u "$RT/lib/partuv_variant.py" --output-dir "$ROOT/partuv_repro" --checkpoint-path "$CKPT" \
  --meshes $RUN_MESHES "$@" > "$ROOT/method.log" 2>&1
echo "method rc=$?"
grep -E "^\[variant\]|Traceback|Error|FAILED" "$ROOT/method.log" | tail -n 60 > "$RT/$NAME/method_summary.log"
cp "$ROOT/partuv_repro/variant_manifest.json" "$RT/$NAME/variant_manifest.json" 2>/dev/null
bash "$RT/lib/hidden_test.sh" "$NAME" "$ROOT"
