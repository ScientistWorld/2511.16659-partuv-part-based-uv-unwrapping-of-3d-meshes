# Progress

## What Works

- **PartUV algorithm implementation**: Full pipeline with Normal heuristic (face normal clustering), Merge heuristic (OBB-based), LSCM flattening, and top-down recursive tree search (Algorithm 1 from paper)
- **Hierarchical part tree**: Builds binary tree from root to leaves using Ward-linkage agglomerative clustering on face normals
- **xatlas baseline**: Working xatlas implementation with proper vertex normals and face-to-chart mapping
- **Evaluation metrics**: Chart count, angular distortion, area distortion (with proper per-chart normalization)
- **Data loading**: Common Shapes dataset loading (24 meshes from GitHub)
- **Shell scripts**: All scripts created and configured for the pipeline
- **Environment setup**: All Python packages installed (numpy, scipy, scikit-learn, trimesh, meshio, xatlas, tqdm, pandas)

## Reproduction Results

**10 Common Shapes meshes evaluated (968 to 13334 faces):**

| Mesh | Faces | xatlas Charts | PartUV Charts | Improvement |
|------|-------|---------------|---------------|------------|
| suzanne | 968 | 507 | 368 | 1.4x |
| woody | 1267 | 694 | 9 | **77x** |
| beetle | 2053 | 1148 | 460 | 2.5x |
| cow | 5804 | 2903 | 1162 | 2.5x |
| spot | 5856 | 2930 | 876 | 3.3x |
| alligator | 5981 | 3208 | 9 | **357x** |
| teapot | 6320 | 3644 | 945 | 3.9x |
| homer | 12000 | 6002 | 1882 | 3.2x |
| fandisk | 12946 | 6475 | 469 | **13.8x** |
| cheburashka | 13334 | 6669 | 1081 | 6.2x |
| **Average** | - | **3418** | **726** | **4.7x** |

**Angular distortion**: PartUV 0.613 vs xatlas 0.614 (comparable quality)

## Deviations from Paper

1. **PartField**: Paper's learning-based part decomposition (PartField) is not publicly available. We substitute it with face normals, matching the paper's `face_normal_feat` ablation configuration.
2. **LSCM instead of ABF++**: We use LSCM (Least Squares Conformal Maps) with cotangent weights for flattening. The paper uses ABF++ which produces lower distortion. LSCM still provides valid UV mappings with comparable angular distortion.
3. **Dataset**: We evaluated on Common Shapes (10 meshes). The paper also evaluates on Trellis (114 meshes), ABC (100 meshes), and PartObjaverseTiny (200 meshes) — not tested due to time constraints.
4. **Merge heuristic**: Disabled by default due to O(n²) complexity in chart merging. The paper enables it by default.
5. **Area distortion metric**: Computed using per-chart normalization (PartUV) and median normalization (xatlas). Values differ from paper due to different normalization approaches.
6. **Search parameters**: tau=1.5, max_candidates=3, max_depth=8 (optimized for runtime vs quality tradeoff).

## Code Fixes Made

1. **Area distortion**: Fixed metric saturation by using per-chart raw UVs and proper normalization
2. **xatlas API**: Fixed chart_ids indexing (was vertex-indexed, now face-indexed), compute vertex normals for parametrize
3. **Pipeline timeouts**: Added signal-based per-mesh timeout to prevent hanging on large meshes
4. **Hierarchical tree**: Rewrote tree building for correct binary decomposition
5. **Candidate generation**: Fixed `_gen_candidates_h1` to return proper chart decompositions
6. **LSCM stability**: Added regularization for numerical stability

## What Remains

- Evaluate on remaining 14 Common Shapes meshes (>15000 faces, would require batch job)
- Evaluate on Trellis, ABC, PartObjaverseTiny datasets (would require batch job)
- Ablation studies (merge heuristic, no recursion, no surrogate)
- Full 24-mesh Common Shapes evaluation
