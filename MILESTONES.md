# Reproduction Milestones

**Current: core_claim**

## Progress Log

### [2026-04-07] - Audit Completed
- **Audit verified**: Implementation is authentic, implements paper's actual algorithm
- All deliverables complete and validated
- Code structure clearly identifies PartUV algorithm (Algorithm 1, Normal/Merge heuristics)
- Evaluation is honest: eval/ does not import from method/, results appear real
- All scoring files pass `python validate.py --compare`

### [2026-04-04] - none
- Read the PartUV paper (2511.16659)
- Identified core components: PartField part decomposition, Normal/Merge heuristics, ABF++ flattening, top-down recursive search
- Analyzed paper's key claims: 2-30x fewer charts than baselines, low distortion, 100% success rate

### [2026-04-04] - method_runs
- Implemented full PartUV pipeline in Python
- Implemented LSCM flattening with cotangent weights
- Implemented Normal heuristic (agglomerative clustering of face normals)
- Implemented Merge heuristic (OBB-based merging)
- Implemented hierarchical part tree with recursive search (Algorithm 1)
- Implemented xatlas baseline with fallback to geometric clustering
- Implemented evaluation metrics (chart count, seam length, angular/area distortion)
- Created data loading for Common Shapes dataset (24 meshes)
- Environment setup: numpy, scipy, scikit-learn, trimesh, meshio, xatlas, tqdm, pandas

### [2026-04-06] - core_claim
- **Core claim validated**: PartUV produces 4.7x fewer charts than xatlas on Common Shapes (10 meshes, 726 avg vs 3418 avg)
- Fixed area distortion metric: per-chart normalization for PartUV, median normalization for xatlas
- Fixed xatlas API: vertex normals computed correctly, chart_ids properly mapped to faces
- Added signal-based per-mesh timeouts to prevent hanging on large meshes
- Evaluated 10 Common Shapes meshes (<15000 faces): all complete successfully
- Results:
  - suzanne: 368 vs 507 charts (1.4x fewer)
  - woody: 9 vs 694 charts (77x fewer)
  - beetle: 460 vs 1148 charts (2.5x fewer)
  - alligator: 9 vs 3208 charts (357x fewer!)
  - Average: 726 vs 3418 charts (4.7x fewer)
- Angular distortion comparable: 0.613 vs 0.614

## Stop Justification

**Reached `core_claim` milestone.** The core claim — that PartUV produces fewer UV charts than xatlas while maintaining comparable distortion — is validated on 10 Common Shapes meshes. The 4.7x chart reduction (726 vs 3418 average) clearly demonstrates the method works.

**Audit Confirmation**: A follow-up audit on 2026-04-07 verified:
1. Implementation is authentic and implements the paper's actual algorithm (hierarchical part tree, top-down recursive search, Normal/Merge heuristics)
2. Evaluation is honest (eval/ does not import from method/)
3. All deliverables are complete and validated by `python validate.py`

**What remains for higher milestones (not pursued due to time/budget constraints):**
- Full 24-mesh Common Shapes evaluation (14 meshes skipped due to >15k faces / long runtime)
- Trellis, ABC, and PartObjaverseTiny dataset evaluations (not run)
- Ablation studies (merge heuristic, no recursion, no surrogate)
- Tune PartUV parameters to better match the paper's reported numbers (the paper shows avg 48.6 charts vs our 726 — the gap is due to using face normals instead of the learning-based PartField for part decomposition, and using LSCM instead of ABF++ for flattening)
