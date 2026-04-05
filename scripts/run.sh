#!/bin/bash
set -e
export TMPDIR=/dev/shm
export UV_CACHE_DIR=/dev/shm/uv-cache
cd /home/user

echo "=== PartUV Job ==="
echo "Python: $(python3 --version)"
echo "CWD: $(pwd)"
echo ""

# Check if data is available
if [ ! -d "data/common_shapes" ] || [ -z "$(ls -A data/common_shapes/*.obj 2>/dev/null)" ]; then
    echo "Data not found. Running download..."
    bash scripts/download.sh
fi

echo "Dataset found:"
ls data/common_shapes/*.obj 2>/dev/null | wc -l
echo "meshes"
echo ""

# Install packages
pip install numpy scipy scikit-learn trimesh meshio xatlas tqdm pandas

# Run xatlas baseline first
echo "=== Running xatlas baseline ==="
python3 -m method.pipeline \
    --data-dir data/common_shapes \
    --output-dir checkpoints \
    --method xatlas \
    --name xatlas_run1

echo ""
echo "=== Running PartUV method ==="
python3 -m method.pipeline \
    --data-dir data/common_shapes \
    --output-dir checkpoints \
    --method partuv \
    --distortion-threshold 1.25 \
    --max-candidates 10 \
    --name partuv_run1

echo ""
echo "=== Creating scores.json ==="
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
            print(f'{method_key}: avg_charts={r.get(\"avg_charts\", 0):.1f}, angular={r.get(\"angular_distortion\", 0):.4f}, area={r.get(\"area_distortion\", 0):.3f}')

os.makedirs('scoring', exist_ok=True)
with open('scoring/scores.json', 'w') as f:
    json.dump(scores, f, indent=2)
print('scores.json written!')
"

echo ""
echo "=== Results ==="
ls -la checkpoints/*.json 2>/dev/null || echo "No result files"
echo ""
echo "=== Done! ==="
