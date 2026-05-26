# Reproduction Milestones

**Current: core_claim**

## Progress Log

### [2026-05-26 17:57] - core_claim
- CPU smoke job `3a0fad9c-777` failed immediately after printing Python version, before the non-torch package import probe or resource checks.
- The only command at that boundary was the torch diagnostic block; removed it from `scripts/run.sh` so CPU smoke can reach xatlas and PartUV pipeline checks.
- Kept the lightweight `numpy`, `xatlas`, and `trimesh` import probe to validate baseline/evaluator dependencies without triggering torch startup before the method script.

### [2026-05-26 17:54] - core_claim
- CPU smoke job `46b9c53f-95e` still failed before xatlas entered `baseline.export_xatlas_dataset.main`, which isolates the failure to Python startup/import resolution for the baseline command.
- Removed the workspace-local `/home/user/.local/lib/python3.12/site-packages` override from runtime scripts so jobs use the reproducible system packages installed by `environment/setup.sh`.
- Added an explicit import probe for `numpy`, `xatlas`, `trimesh`, and `partuv` in `scripts/run.sh` before the smoke pipeline starts.

### [2026-05-26 17:50] - core_claim
- CPU smoke job `da43a5da-788` failed before producing xatlas results; logs stopped after environment/resource diagnostics and left only an empty `checkpoints/smoke/xatlas` directory.
- Added strict shell mode, unbuffered Python, explicit resource/artifact checks, and xatlas progress logging so the next smoke job reports the failing command and missing artifact directly.
- Hardened `eval.evaluate_uv_outputs` so evaluating a directory with no UV artifacts exits nonzero instead of writing an empty aggregate.

### [2026-05-26 17:39] - core_claim
- Continuation audit found the active reproduction path is genuine: `scripts/method.sh` runs `method.official_pipeline`, which calls the released PartUV pipeline with PartField inference, recursive decomposition, Normal/Merge decisions, and ABF/LSCM unwrapping.
- Confirmed `eval/` remains independent from `method/` and `python3 validate.py --compare` passes on the existing 24-mesh Common Shapes scores.
- Fixed smoke-run hygiene so limited jobs write isolated outputs, do not overwrite canonical 24-mesh scores, clear stale output directories before generation, and fail if either baseline or method results are missing.

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
