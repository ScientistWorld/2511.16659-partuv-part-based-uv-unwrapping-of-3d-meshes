#!/bin/bash
set -e
export TMPDIR=/dev/shm
export PYTHONPATH=/dev/shm/site-packages
cd /home/user

echo "=== PartUV Job ==="
echo "Python: $(python3 --version)"
echo "PYTHONPATH: $PYTHONPATH"
echo "CWD: $(pwd)"

# Check if data is available
if [ ! -d "data/common_shapes" ] || [ -z "$(ls -A data/common_shapes/*.obj 2>/dev/null)" ]; then
    echo "Data not found. Running download..."
    bash scripts/download.sh
fi

echo "Dataset found:"
ls data/common_shapes/*.obj 2>/dev/null | wc -l
echo "meshes"
echo ""

# Verify packages
python3 -c "import numpy; import scipy; import sklearn; import trimesh; import meshio; import pandas; print('All packages OK')"

# Run full evaluation (xatlas first, then PartUV)
echo "=== Running evaluation ==="
python3 -m method.pipeline \
    --data-dir data/common_shapes \
    --output-dir checkpoints \
    --method both \
    --distortion-threshold 1.5 \
    --max-candidates 3 \
    --name eval1

echo ""
echo "=== Creating scores.json ==="
python3 -c "
import json, os

scores = {'experiments': {'common_shapes_comparison': {'description': 'Common Shapes: PartUV vs xatlas. PartUV produces fewer charts via hierarchical part decomposition.', 'weight': 1.0, 'primary_metric': 'avg_charts', 'metrics': {'avg_charts': {'higher_is_better': False, 'coefficient': 1.0}, 'median_charts': {'higher_is_better': False, 'coefficient': 0.5}, 'angular_distortion': {'higher_is_better': True, 'coefficient': 0.3}, 'overall_area_distortion': {'higher_is_better': False, 'coefficient': 0.2}}, 'results': {}}}

for fname, method_key in [('results_xatlas_eval1.json', 'xatlas'), ('results_partuv_eval1.json', 'partuv_reproduced')]:
    fpath = f'checkpoints/{fname}'
    if os.path.exists(fpath):
        with open(fpath) as f:
            raw = json.load(f)
        if method_key in raw:
            r = raw[method_key]
            result_entry = {
                'type': 'baseline' if 'xatlas' in method_key else 'proposed',
                'avg_charts': round(r.get('avg_charts', 0), 1),
                'median_charts': round(r.get('median_charts', 0), 1),
                'median_seam_length': round(r.get('median_seam_length', 0), 1),
                'angular_distortion': round(r.get('angular_distortion', 0), 4),
                'overall_area_distortion': round(r.get('overall_area_distortion', 0), 4),
                'success_rate': round(r.get('success_rate', 0), 1),
                'time_seconds': round(r.get('avg_time', 0), 1),
            }
            scores['experiments']['common_shapes_comparison']['results'][method_key] = result_entry
            print(f'{method_key}: avg_charts={result_entry[\"avg_charts\"]:.1f}, angular={result_entry[\"angular_distortion\"]:.4f}, area={result_entry[\"overall_area_distortion\"]:.4f}')

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
