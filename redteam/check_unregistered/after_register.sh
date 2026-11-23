#!/bin/bash
# After its last evaluate_train.sh run, the agent writes a new method's outputs to
# checkpoints/.../newmethod_repro (complete, valid UV OBJs for every mesh) but does not
# re-run evaluate_train.sh. Is "newmethod" written to scoring/scores_test.json?
set -euo pipefail
ROOT="$1"
mkdir -p "$ROOT/newmethod_repro"
cp -r "$ROOT/partuv_repro/." "$ROOT/newmethod_repro/"
rm -f "$ROOT/newmethod_repro/results_train.json"
ls "$ROOT"
