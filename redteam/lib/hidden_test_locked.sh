#!/bin/bash
# Called by hidden_test.sh while holding the scoring/ lock. See hidden_test.sh.
set -uo pipefail
NAME="$1"
CKPT_ROOT="$2"
OUT="/home/user/redteam/$NAME"
cd /home/user
mkdir -p "$OUT"

echo "[hidden_test] $NAME: root=$CKPT_ROOT start $(date -Is)"
# Start from an empty scoring state so nothing from another scenario leaks in.
rm -f scoring/scores_train.json scoring/scores_train_manifest.json \
      scoring/scores_test.json scoring/scores_test_manifest.json

t0=$(date +%s)
bash scripts/evaluate_train.sh "$CKPT_ROOT" > "$OUT/evaluate_train.log" 2>&1
train_rc=$?
t1=$(date +%s)

after_rc=0
if [ -f "$OUT/after_register.sh" ]; then
  bash "$OUT/after_register.sh" "$CKPT_ROOT" > "$OUT/after_register.log" 2>&1
  after_rc=$?
fi

# The hidden test: no arguments, exactly as the grader runs it.
bash scripts/evaluate_test.sh > "$OUT/evaluate_test.log" 2>&1
test_rc=$?
t2=$(date +%s)

rm -f "$OUT/scores_test.json" "$OUT/scores_train.json"
[ -f scoring/scores_test.json ] && cp scoring/scores_test.json "$OUT/scores_test.json"
[ -f scoring/scores_train.json ] && cp scoring/scores_train.json "$OUT/scores_train.json"
for d in "$CKPT_ROOT"/*/; do
  [ -f "$d/results_test.json" ] && cp "$d/results_test.json" "$OUT/per_mesh_test_$(basename "$d").json"
done

cat > "$OUT/hidden_test_status.json" <<EOF
{"evaluate_train_rc": $train_rc, "after_register_rc": $after_rc, "evaluate_test_rc": $test_rc,
 "evaluate_train_seconds": $((t1 - t0)), "evaluate_test_seconds": $((t2 - t1)),
 "scores_test_json_present": $([ -f scoring/scores_test.json ] && echo true || echo false)}
EOF
echo "[hidden_test] $NAME: train_rc=$train_rc test_rc=$test_rc test_seconds=$((t2 - t1))"
tail -3 "$OUT/evaluate_test.log"
exit 0
