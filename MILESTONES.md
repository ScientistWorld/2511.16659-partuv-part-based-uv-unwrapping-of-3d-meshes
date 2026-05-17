# Reproduction Milestones

**Current: core_claim**

## Progress Log

### [2026-05-17] - core_claim
- Fixed PartUV floating-point exception: `pamo=false` and `num_cuda_streams=0` in config.yaml (avoids CUDA stream initialization on CPU-only environment)
- Fixed `official_pipeline.py` to use file-based `partuv.pipeline()` instead of `pipeline_numpy()` (which crashes with numpy arrays on CPU)
- Updated `method/method.sh`, `baseline.sh`, `reproduce.sh`, `run.sh` to set `PYTHONPATH=/home/user/.local/lib/python3.12/site-packages` (no LD_PRELOAD needed)
- All transitive deps added to `setup.sh`: yacs, seaborn, open3d, etc.
- PartUV successfully produces UV mappings on 5 meshes tested (alligator, armadillo, beast, beetle, beetle-alt)
- Preliminary results: PartUV produces 1-172 charts vs xatlas baseline 1-322+ charts per mesh
- Pipeline ready for full 24-mesh run

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