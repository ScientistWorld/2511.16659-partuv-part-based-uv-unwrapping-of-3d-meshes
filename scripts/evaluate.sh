#!/bin/bash
set -euo pipefail
export TMPDIR=/dev/shm
cd /home/user

MODE="${1:-}"

if [ "$MODE" = "single" ]; then
  METHOD_NAME="$2"
  INPUT_ROOT="$3"
  UV_FILENAME="$4"
  OUTPUT_JSON="$5"

  python3 -m eval.evaluate_uv_outputs \
    --method-name "$METHOD_NAME" \
    --input-root "$INPUT_ROOT" \
    --uv-filename "$UV_FILENAME" \
    --output-json "$OUTPUT_JSON"
  exit 0
fi

if [ "$MODE" = "compare" ]; then
  BASELINE_JSON="$2"
  METHOD_JSON="$3"
  OUTPUT_JSON="${4:-/home/user/scoring/scores.json}"

  test -f "$BASELINE_JSON" || { echo "ERROR: missing baseline results: $BASELINE_JSON"; exit 1; }
  test -f "$METHOD_JSON" || { echo "ERROR: missing method results: $METHOD_JSON"; exit 1; }

  python3 - <<PY
import json
from pathlib import Path

baseline_path = Path("${BASELINE_JSON}")
method_path = Path("${METHOD_JSON}")
output_path = Path("${OUTPUT_JSON}")

scores = {
    "experiments": {
        "common_shapes_comparison": {
            "results": {}
        }
    }
}

for path in [baseline_path, method_path]:
    with open(path) as f:
        payload = json.load(f)
    for method_name, result in payload.items():
        scores["experiments"]["common_shapes_comparison"]["results"][method_name] = {
            key: value
            for key, value in result.items()
            if key not in {"per_mesh"}
        }

output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w") as f:
    json.dump(scores, f, indent=2)
print(json.dumps(scores, indent=2))
PY
  exit 0
fi

echo "Usage:"
echo "  bash scripts/evaluate.sh single <method_name> <input_root> <uv_filename> <output_json>"
echo "  bash scripts/evaluate.sh compare <baseline_json> <method_json> [output_json]"
exit 1
