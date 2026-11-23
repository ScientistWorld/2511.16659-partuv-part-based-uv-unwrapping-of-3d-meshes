#!/bin/bash
# Usage: run_shortcut.sh <name>
# Puts the shortcut in place as an agent would (its outputs in a checkpoint folder named
# partuv_repro, i.e. reported under the method name "partuv"), then runs the hidden test.
set -uo pipefail
NAME="$1"
[ -n "$NAME" ] || { echo "missing name"; exit 2; }
source /home/user/redteam/lib/env.sh
export RUN_MESHES
cd /home/user
rm -rf "$ROOT"
mkdir -p "$ROOT/partuv_repro"
python3 -u "$RT/$NAME/make.py" "$ROOT/partuv_repro" > "$RT/$NAME/make.log" 2>&1
echo "make rc=$?"
tail -n 20 "$RT/$NAME/make.log"
bash "$RT/lib/hidden_test.sh" "$NAME" "$ROOT"
