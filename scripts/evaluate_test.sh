#!/bin/bash
set -euo pipefail
export TMPDIR=/dev/shm
cd /home/user

MODE="${1:-from-train}"

if [ "$MODE" = "single" ]; then
  METHOD_NAME="$2"
  INPUT_ROOT="$3"
  UV_FILENAME="$4"
  OUTPUT_JSON="$5"

  python3 -m eval.test.evaluate_uv_outputs single \
    --method-name "$METHOD_NAME" \
    --input-root "$INPUT_ROOT" \
    --uv-filename "$UV_FILENAME" \
    --output-json "$OUTPUT_JSON"
  echo "evaluate_test.sh: wrote single-method test results to $OUTPUT_JSON"
  exit 0
fi

if [ "$MODE" = "compare" ]; then
  BASELINE_JSON="$2"
  METHOD_JSON="$3"
  OUTPUT_JSON="${4:-/home/user/scoring/scores_test.json}"
  MANIFEST_JSON="${TEST_MANIFEST_JSON:-/home/user/scoring/scores_test_manifest.json}"

  test -f "$BASELINE_JSON" || { echo "ERROR: missing baseline results: $BASELINE_JSON"; exit 1; }
  test -f "$METHOD_JSON" || { echo "ERROR: missing method results: $METHOD_JSON"; exit 1; }

  python3 -m eval.test.evaluate_uv_outputs compare \
    --baseline-json "$BASELINE_JSON" \
    --method-json "$METHOD_JSON" \
    --output-json "$OUTPUT_JSON" \
    --manifest-json "$MANIFEST_JSON"
  echo "evaluate_test.sh: wrote compared test scores to $OUTPUT_JSON"
  exit 0
fi

if [ "$MODE" = "from-train" ]; then
  TRAIN_SCORES_JSON="${2:-/home/user/scoring/scores_train.json}"
  OUTPUT_JSON="${3:-/home/user/scoring/scores_test.json}"
  TRAIN_MANIFEST_JSON="${TRAIN_MANIFEST_JSON:-/home/user/scoring/scores_train_manifest.json}"
  TEST_MANIFEST_JSON="${TEST_MANIFEST_JSON:-/home/user/scoring/scores_test_manifest.json}"
  CHECKPOINTS_ROOT="${CHECKPOINTS_ROOT:-/home/user/checkpoints}"

  test -f "$TRAIN_SCORES_JSON" || { echo "ERROR: missing train scores: $TRAIN_SCORES_JSON"; exit 1; }

  python3 -m eval.test.evaluate_uv_outputs from-train \
    --train-scores-json "$TRAIN_SCORES_JSON" \
    --train-manifest-json "$TRAIN_MANIFEST_JSON" \
    --checkpoints-root "$CHECKPOINTS_ROOT" \
    --output-json "$OUTPUT_JSON" \
    --manifest-json "$TEST_MANIFEST_JSON"
  echo "evaluate_test.sh: wrote held-out test scores to $OUTPUT_JSON"
  exit 0
fi

# Required ResearchGym interface: a checkpoint/output root as the only
# positional argument reuses the train method set and scores the held-out slice.
if [ -d "$MODE" ]; then
  CHECKPOINTS_ROOT="$MODE"
  TRAIN_SCORES_JSON="${2:-/home/user/scoring/scores_train.json}"
  OUTPUT_JSON="${3:-/home/user/scoring/scores_test.json}"
  TRAIN_MANIFEST_JSON="${TRAIN_MANIFEST_JSON:-/home/user/scoring/scores_train_manifest.json}"
  TEST_MANIFEST_JSON="${TEST_MANIFEST_JSON:-/home/user/scoring/scores_test_manifest.json}"

  test -f "$TRAIN_SCORES_JSON" || { echo "ERROR: missing train scores: $TRAIN_SCORES_JSON"; exit 1; }

  python3 -m eval.test.evaluate_uv_outputs from-train \
    --train-scores-json "$TRAIN_SCORES_JSON" \
    --train-manifest-json "$TRAIN_MANIFEST_JSON" \
    --checkpoints-root "$CHECKPOINTS_ROOT" \
    --output-json "$OUTPUT_JSON" \
    --manifest-json "$TEST_MANIFEST_JSON"
  echo "evaluate_test.sh: wrote held-out test scores to $OUTPUT_JSON"
  exit 0
fi

echo "Usage:"
echo "  bash scripts/evaluate_test.sh single <method_name> <input_root> <uv_filename> <output_json>"
echo "  bash scripts/evaluate_test.sh compare <baseline_json> <method_json> [output_json]"
echo "  bash scripts/evaluate_test.sh from-train [scores_train_json] [scores_test_json]"
echo "  bash scripts/evaluate_test.sh [checkpoints_root] [scores_train_json] [scores_test_json]"
exit 1
