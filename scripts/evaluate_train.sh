#!/bin/bash
set -euo pipefail
export TMPDIR=/dev/shm
cd /home/user

MODE="${1:-discover}"

if [ "$MODE" = "single" ]; then
  METHOD_NAME="$2"
  INPUT_ROOT="$3"
  UV_FILENAME="$4"
  OUTPUT_JSON="$5"

  python3 -m eval.train.evaluate_uv_outputs single \
    --method-name "$METHOD_NAME" \
    --input-root "$INPUT_ROOT" \
    --uv-filename "$UV_FILENAME" \
    --output-json "$OUTPUT_JSON"
  echo "evaluate_train.sh: wrote single-method train results to $OUTPUT_JSON"
  exit 0
fi

if [ "$MODE" = "compare" ]; then
  BASELINE_JSON="$2"
  METHOD_JSON="$3"
  OUTPUT_JSON="${4:-/home/user/scoring/scores_train.json}"
  MANIFEST_JSON="${TRAIN_MANIFEST_JSON:-/home/user/scoring/scores_train_manifest.json}"

  test -f "$BASELINE_JSON" || { echo "ERROR: missing baseline results: $BASELINE_JSON"; exit 1; }
  test -f "$METHOD_JSON" || { echo "ERROR: missing method results: $METHOD_JSON"; exit 1; }

  python3 -m eval.train.evaluate_uv_outputs compare \
    --baseline-json "$BASELINE_JSON" \
    --method-json "$METHOD_JSON" \
    --output-json "$OUTPUT_JSON" \
    --manifest-json "$MANIFEST_JSON"
  echo "evaluate_train.sh: wrote compared train scores to $OUTPUT_JSON"
  exit 0
fi

if [ "$MODE" = "discover" ]; then
  CHECKPOINTS_ROOT="${2:-/home/user/checkpoints}"
  OUTPUT_JSON="${3:-/home/user/scoring/scores_train.json}"
  MANIFEST_JSON="${TRAIN_MANIFEST_JSON:-/home/user/scoring/scores_train_manifest.json}"

  python3 -m eval.train.evaluate_uv_outputs discover \
    --checkpoints-root "$CHECKPOINTS_ROOT" \
    --output-json "$OUTPUT_JSON" \
    --manifest-json "$MANIFEST_JSON"
  echo "evaluate_train.sh: discovered checkpoint outputs and wrote train scores to $OUTPUT_JSON"
  exit 0
fi

# Required ResearchGym interface: a checkpoint/output root as the only
# positional argument discovers and scores every method under that root.
if [ -d "$MODE" ]; then
  CHECKPOINTS_ROOT="$MODE"
  OUTPUT_JSON="${2:-/home/user/scoring/scores_train.json}"
  MANIFEST_JSON="${TRAIN_MANIFEST_JSON:-/home/user/scoring/scores_train_manifest.json}"

  python3 -m eval.train.evaluate_uv_outputs discover \
    --checkpoints-root "$CHECKPOINTS_ROOT" \
    --output-json "$OUTPUT_JSON" \
    --manifest-json "$MANIFEST_JSON"
  echo "evaluate_train.sh: discovered checkpoint outputs and wrote train scores to $OUTPUT_JSON"
  exit 0
fi

echo "Usage:"
echo "  bash scripts/evaluate_train.sh single <method_name> <input_root> <uv_filename> <output_json>"
echo "  bash scripts/evaluate_train.sh compare <baseline_json> <method_json> [output_json]"
echo "  bash scripts/evaluate_train.sh discover [checkpoints_root] [output_json]"
echo "  bash scripts/evaluate_train.sh [checkpoints_root] [output_json]"
exit 1
