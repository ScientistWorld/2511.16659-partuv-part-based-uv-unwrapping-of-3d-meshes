# Reproduction Milestones

**Current: method_runs**

## Progress Log

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
