#!/bin/bash
# Reproduce the paper's results end-to-end.
set -e
export TMPDIR=/dev/shm
cd /home/user

DATA_DIR="/home/user/data/common_shapes"
if [ ! -d "$DATA_DIR" ] || [ -z "$(ls -A $DATA_DIR/*.obj 2>/dev/null)" ]; then
    echo "Data not found. Running download script..."
    bash scripts/download.sh
fi

echo ""
echo "=== Step 1: Run xatlas baseline ==="
bash scripts/baseline.sh "$DATA_DIR" /home/user/checkpoints xatlas_run1

echo ""
echo "=== Step 2: Run PartUV method ==="
bash scripts/method.sh "$DATA_DIR" /home/user/checkpoints partuv_run1

echo ""
echo "=== Step 3: Create scores.json ==="
TMPDIR=/dev/shm python3 -c "
import json, os

scores = {'common_shapes_comparison': {}}

for fname, method_key in [('results_xatlas_run1.json', 'xatlas'), ('results_partuv_run1.json', 'partuv')]:
    fpath = f'checkpoints/{fname}'
    if os.path.exists(fpath):
        with open(fpath) as f:
            raw = json.load(f)
        if method_key in raw:
            r = raw[method_key]
            scores['common_shapes_comparison'][method_key] = {
                'avg_charts': r.get('avg_charts', 0),
                'median_charts': r.get('median_charts', 0),
                'median_seam_length': r.get('median_seam_length', 0),
                'angular_distortion': r.get('angular_distortion', 0),
                'area_distortion': r.get('area_distortion', 0),
                'overall_area_distortion': r.get('overall_area_distortion', 0),
                'success_rate': r.get('success_rate', 0),
                'time_seconds': r.get('avg_time', 0),
            }

os.makedirs('scoring', exist_ok=True)
with open('scoring/scores.json', 'w') as f:
    json.dump(scores, f, indent=2)
print('scores.json written!')
"

echo ""
echo "=== Reproduction complete! ==="
