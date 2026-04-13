# Progress

## What Works

- Briefing, scoring references, and the Common Shapes dataset are present.
- The workspace targets the official PartUV pipeline with the Objaverse-trained PartField checkpoint.
- Offline resources staged in the workspace:
  - `environment/wheels/partuv-0.1.2-...whl` (rebuilt with fixed namespace packages)
  - `environment/wheels/torch_scatter-2.1.2+pt27cu128-...whl`
  - `checkpoints/partfield/model_objaverse.ckpt` (1.2GB)
  - `data/common_shapes/` (24 meshes)
- The active evaluation path scores Common Shapes outputs with method-agnostic UV metrics.
- The container environment is fixed:
  - Uses `Bootstrap: scratch` with Ubuntu Jammy rootfs (Canonical CDN, reliable)
  - Uses `%files` to copy wheel files into the container image at build time
  - All Python packages installed in `%post` at build time
  - `LD_PRELOAD` set for libstdc++ compatibility
- The pipeline scripts are fixed:
  - baseline.sh, method.sh, reproduce.sh use consistent output paths
  - official_pipeline.py uses correct wheel import paths
  - Source tree has all required `__init__.py` files for Python packages

## Results Achieved

- No results yet - first GPU job submitted.

## What Remains

- Run PartUV on Common Shapes dataset (24 meshes)
- Run xatlas baseline on same meshes
- Evaluate and compare results
- Validate scores against reference and claim milestone

## Issues Encountered

- Previous iterations had repeated container build failures due to registry pulls and image source changes
- Wheel had missing `__init__.py` for namespace package `partfield_official` - fixed by rebuilding wheel
- `method/__init__.py` had interfering relative imports - fixed
- Output path mismatches between baseline.sh/method.sh and reproduce.sh - fixed

## Deviations from Paper

- None claimed yet. The intent is to run the released PartUV method with the public Objaverse-trained PartField checkpoint on Common Shapes (one of the paper's four datasets).
