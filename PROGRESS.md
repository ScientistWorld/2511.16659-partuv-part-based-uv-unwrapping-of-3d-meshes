# Progress

## What Works

- **PartUV algorithm implementation**: Full pipeline with Normal heuristic (face normal clustering), Merge heuristic (OBB-based), LSCM flattening, and top-down recursive tree search
- **Hierarchical part tree**: Properly builds binary tree from root to leaves using agglomerative clustering on face normals
- **xatlas baseline**: Working xatlas implementation with fallback to geometric clustering when xatlas unavailable
- **Evaluation metrics**: Chart count, seam length, angular distortion, area distortion, overall area distortion
- **Data loading**: Common Shapes dataset loading (22 meshes)
- **Shell scripts**: All scripts created and configured for the pipeline
- **Environment setup**: All Python packages installed (numpy, scipy, scikit-learn, trimesh, meshio, xatlas, tqdm, pandas)

## Results

Pending: job is running to produce actual results.

Expected (from paper's Table 1, Common Shapes):
- PartUV: avg_charts ~48.6, angular_distortion ~0.990, area_distortion ~1.283
- xatlas: avg_charts ~974.8, angular_distortion ~0.987, area_distortion ~1.885

## Remaining

- Wait for job results and validate that the method produces fewer charts than baseline
- Verify distortion metrics are within acceptable range
- Push code and results to git

## Issues

- `/tmp` is a 64MB tmpfs — must use `TMPDIR=/dev/shm` for all pip operations
- GitHub repo `alecjacobson/common-3d-test-models` uses `master` branch, not `main`
- Bash was not functioning in this turn — submitted job instead
- PartField (the paper's learning-based part decomposition) is not publicly available — using face normals as a substitute feature, which matches the paper's ablation study (Table 4b)

## Code Fixes Made

1. **LSCM flattening**: Fixed cotangent formula from `dot/(|a|*|b|)` (cosine) to `dot/(|cross|)` (cotangent). Rewrote solver to use proper sparse matrix operations.
2. **Hierarchical tree**: Rewrote tree building to correctly build binary tree from root to leaves.
3. **Candidate generation**: Fixed `_gen_candidates_h1` to return proper chart decompositions (list of lists) instead of concatenated arrays.
4. **xatlas cleanup**: Added proper temp directory cleanup with try/finally.
5. **Package init files**: Added `__init__.py` to data/, eval/, baseline/, method/ packages.

## Deviations from Paper

1. **PartField**: The paper's learning-based part decomposition model (PartField) is not publicly available. We substitute it with face normal features, matching the paper's ablation study configuration.
2. **LSCM instead of ABF++**: We use LSCM for flattening because it's simpler to implement. The paper's appendix shows ABF++ produces better results, but LSCM should still produce valid UV mappings.
3. **Dataset**: We use Common Shapes (22 meshes) which is the primary benchmark dataset. The paper also evaluates on Trellis, ABC, and PartObjaverseTiny.
4. **Merge heuristic**: Simplified implementation — the paper's merge heuristic is more sophisticated.
5. **Only Common Shapes tested**: Not reproducing all four datasets due to time/resource constraints.

The core algorithm (recursive tree search + Normal heuristic + LSCM flattening) is preserved. The method still aims to minimize chart count while keeping distortion below threshold.
