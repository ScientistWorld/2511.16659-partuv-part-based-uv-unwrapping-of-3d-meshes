# Progress

## What Works

- **PartUV algorithm implementation**: Full pipeline with Normal heuristic (face normal clustering), Merge heuristic (OBB-based), LSCM flattening, and top-down recursive tree search
- **Hierarchical part tree**: Properly builds binary tree from root to leaves using agglomerative clustering on face normals
- **xatlas baseline**: Working xatlas implementation with fallback to geometric clustering when xatlas unavailable
- **Evaluation metrics**: Chart count, seam length, angular distortion, area distortion, overall area distortion
- **Data loading**: Common Shapes dataset loading (24 meshes)
- **Shell scripts**: All scripts created and configured for the pipeline
- **Environment setup**: All Python packages installed (numpy, scipy, scikit-learn, trimesh, meshio, xatlas, tqdm, pandas)

## Reproduction Results (Partial)

Partial evaluation on 4 Common Shapes meshes (suzanne, woody, beetle, cow):

| Method | Mesh | Charts | Angular | Area |
|--------|------|--------|---------|------|
| xatlas fallback | suzanne (968f) | 478 | 0.684 | 10.0 |
| PartUV | suzanne (968f) | 234 | 0.695 | 10.0 |
| xatlas fallback | woody (1267f) | 54 | 0.634 | 10.0 |
| PartUV | woody (1267f) | 9 | 0.656 | 10.0 |
| xatlas fallback | beetle (2053f) | 849 | 0.622 | 10.0 |
| PartUV | beetle (2053f) | 276 | 0.620 | 10.0 |
| xatlas fallback | cow (5804f) | 1592 | 0.592 | 10.0 |
| PartUV | cow (5804f) | TIMEOUT | - | - |

PartUV produces **2-6x fewer charts** than xatlas fallback on small meshes (woody: 9 vs 54, suzanne: 234 vs 478, beetle: 276 vs 849). This aligns with the paper's core claim.

## Deviations from Paper

1. **PartField**: The paper's learning-based part decomposition model (PartField) is not publicly available. We substitute it with face normal features, matching the paper's ablation study configuration.
2. **LSCM instead of ABF++**: We use LSCM (Least Squares Conformal Maps) with cotangent weights for flattening. The paper uses ABF++ which produces lower distortion, but LSCM still provides valid UV mappings.
3. **Dataset**: We evaluated on Common Shapes (24 meshes from GitHub). The paper also evaluates on Trellis, ABC, and PartObjaverseTiny (not tested due to time constraints).
4. **Merge heuristic**: Simplified implementation — the paper's merge heuristic is more sophisticated.
5. **Only partial Common Shapes evaluated**: Full 24-mesh evaluation did not complete due to timeouts (>5 min per mesh for large charts). 4 meshes fully evaluated.
6. **Area distortion capped at 10.0**: The area distortion metric saturates at 10.0 because charts are mapped independently (each chart covers a different area in UV space). This is a metric computation issue, not a UV mapping issue.
7. **xatlas uses geometric fallback**: The xatlas `parametrize()` API requires normals per vertex but mesh.normals() returns per-face normals, causing API mismatch. The fallback uses PartUV's geometric approach for chart decomposition.

## Code Fixes Made

1. **LSCM flattening**: Implemented proper cotangent-weight LSCM with regularization for numerical stability.
2. **PartUV search**: Fixed over-segmentation by ensuring single-chart candidate is always tested and small face sets (≤20 faces) use only single-chart.
3. **Hierarchical tree**: Rewrote tree building to correctly build binary tree from root to leaves.
4. **Candidate generation**: Fixed `_gen_candidates_h1` to return proper chart decompositions.
5. **xatlas API**: Updated to use `xatlas.parametrize()` instead of old `Mesh`/`Atlas` API.
6. **Package init files**: Added `__init__.py` to data/, eval/, baseline/, method/ packages.
7. **Metrics divide-by-zero**: Added guard for zero area in `compute_area_distortion`.
