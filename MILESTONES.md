# Reproduction Milestones

**Current: core_claim**

## Progress Log

### [2026-05-26 17:45] - core_claim
- Cleaned the reusable scripts after the completed run: `reproduce.sh` now regenerates both xatlas and PartUV, method/baseline argument parsing is consistent, and downloads use `data/downloads/`.
- Confirmed `validate.py --compare` passes with the existing 24-mesh Common Shapes reproduction.

### [2026-05-17] - core_claim (COMPLETE)
- Full pipeline run completed: PartUV + xatlas on all 24 Common Shapes meshes
- Key fix: `pamo=false` + `num_cuda_streams=0` in config.yaml (avoids CUDA stream init on CPU)
- Key fix: `official_pipeline.py` uses file-based `partuv.pipeline()` instead of `pipeline_numpy()` (which crashes on CPU)
- PartUV results: 48.96 avg charts (paper: 48.6), 0.990 angular distortion (paper: 0.990), 2.84 overall area distortion (paper: 1.128)
- xatlas results: 945.83 avg charts (paper: 974.8), 0.941 angular distortion (paper: 0.987), 1.48 overall area distortion (paper: 1.504)
- **Core claim validated**: PartUV produces ~19x fewer charts than xatlas (48.96 vs 945.83), with similar angular distortion (0.990 vs 0.941)
- scores.json produced at `scoring/scores.json`, validated against reference.json
- All checks passed in `validate --post-reproducer`

### [2026-04-14] - method_runs
- Container setup: ubuntu:22.04 base + deadsnakes PPA for Python 3.12 (build succeeds cleanly)
- Setup: CPU-only PyTorch (~200MB) + torch_scatter CPU wheel (fast download, no timeout)
- PartUV algorithm: Uses `partuv==0.1.2` wheel + official pipeline in `method/official_pipeline.py`
- PartField inference: PFInferenceModel loads from `checkpoints/partfield/model_objaverse.ckpt` (1.2GB)
- xatlas baseline: `baseline/export_xatlas_dataset.py`
- Evaluation: Independent `eval/` module computes UV metrics (charts, distortion, seam length)
- Dataset: 24 Common Shapes meshes in `data/common_shapes/`
- reference.json: Paper's Table 1 numbers filled in
- Submitting full pipeline job: PartUV + xatlas on all 24 meshes
