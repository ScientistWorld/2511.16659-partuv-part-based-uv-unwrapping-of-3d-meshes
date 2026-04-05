# Reproduction Milestones

**Current: method_runs**

## Progress Log

### [2026-04-04] - none
- Read the PartUV paper (2511.16659)
- Identified core components: PartField part decomposition, Normal/Merge heuristics, ABF++ flattening, top-down recursive search
- Analyzed paper's key claims: 2-30x fewer charts than baselines, low distortion, 100% success rate

### [2026-04-04] - method_runs
- Implemented full PartUV pipeline in Python
- Implemented LSCM flattening (ABF++ alternative) for chart parameterization
- Implemented Normal heuristic (agglomerative clustering of face normals)
- Implemented Merge heuristic (OBB-based merging)
- Implemented hierarchical part tree with recursive search (Algorithm 1)
- Implemented xatlas baseline (with fallback to geometric clustering)
- Implemented evaluation metrics (chart count, seam length, angular/area distortion)
- Created data loading for Common Shapes dataset
- Created all shell scripts (download, evaluate, reproduce, run, method, baseline)
- Environment setup: numpy, scipy, scikit-learn, trimesh, meshio, xatlas, tqdm, pandas
- Common Shapes dataset downloaded (22 meshes from GitHub)
- Submitted full reproduction job (xatlas + PartUV on all meshes)

## Stop Justification

<!-- Do not edit this unless you decide to stop -->
