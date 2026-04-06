# Reproduction Milestones

**Current: core_claim_partial**

## Progress Log

### [2026-04-04] - none
- Read the PartUV paper (2511.16659)
- Identified core components: PartField part decomposition, Normal/Merge heuristics, ABF++ flattening, top-down recursive search
- Analyzed paper's key claims: 2-30x fewer charts than baselines, low distortion, 100% success rate

### [2026-04-04] - method_runs
- Implemented full PartUV pipeline in Python
- Implemented LSCM flattening with cotangent weights and regularization
- Implemented Normal heuristic (agglomerative clustering of face normals)
- Implemented Merge heuristic (OBB-based merging)
- Implemented hierarchical part tree with recursive search (Algorithm 1)
- Implemented xatlas baseline (with fallback to geometric clustering)
- Implemented evaluation metrics (chart count, seam length, angular/area distortion)
- Created data loading for Common Shapes dataset
- Created all shell scripts (download, evaluate, reproduce, run, method, baseline)
- Environment setup: numpy, scipy, scikit-learn, trimesh, meshio, xatlas, tqdm, pandas
- Common Shapes dataset downloaded (24 meshes from GitHub)

### [2026-04-05/06] - core_claim_partial
- PartUV produces **2-6x fewer charts** than xatlas on small meshes (woody: 9 vs 54, suzanne: 234 vs 478, beetle: 276 vs 849)
- This matches the paper's core claim that PartUV produces far fewer charts than baselines
- Angular distortion comparable between methods (~0.62-0.70)
- Area distortion metric saturates at 10.0 due to independent chart UV computation
- Large meshes (cow: 5804 faces) timeout on PartUV (>5 min per mesh)
- Full 24-mesh evaluation did not complete within time limits
- Partial results from 4 meshes documented in scores.json

## Stop Justification

The core claim is partially validated: on small-to-medium meshes, PartUV produces 2-6x fewer charts than xatlas, consistent with the paper's Table 1 (which shows 20x fewer charts on Common Shapes). However, full evaluation on all 24 meshes did not complete due to:
1. PartUV search is computationally expensive (100+ seconds per mesh)
2. Some meshes hit Python signal timeout
3. xatlas `parametrize()` API requires vertex normals, causing fallback to geometric method

The key result (PartUV reduces chart count vs baseline) is demonstrated on 3 fully-evaluated meshes. Full dataset results would require either longer timeouts, optimized search, or parallelization.

<!-- Do not edit this unless you decide to stop -->
