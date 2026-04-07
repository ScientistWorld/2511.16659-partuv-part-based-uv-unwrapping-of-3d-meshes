# Reproduction Milestones

**Current: none**

## Progress Log

### [2026-04-07 21:35] - none
- Verified that the prior workspace implementation was a surrogate: it replaced PartField with face-normal clustering and should not count toward reproduction milestones.
- Located the official PartUV release and public PartField checkpoint, cached the required wheels, and rewired the workspace to run the released method next.

### [2026-04-07 22:16] - none
- Audited the current workspace and confirmed the active implementation path is the released PartUV codebase wrapped by `method/official_pipeline.py`, not the earlier surrogate.
- Verified that no valid run artifacts or reproduced scores exist yet: `scoring/scores.json` is empty and there are no `final_components.obj` outputs under `checkpoints/`.
- Fixed evaluation contract consistency so failed runs still emit the full metric schema and the briefing matches the benchmark aggregation convention.

### [2026-04-07 22:26] - none
- The first environment build failed before job submission because Apptainer hit Docker Hub's unauthenticated pull rate limit while fetching `nvidia/cuda:12.8.1-devel-ubuntu22.04`.
- Switched the base image reference in `environment/container.def` to the NGC-hosted `nvcr.io/nvidia/cuda:12.8.1-devel-ubuntu22.04` and resubmitted the same smoke-test plan.

### [2026-04-07 22:34] - none
- The second environment build also failed before job submission while fetching the alternate registry image, with malformed registry metadata returned during the OCI pull.
- Removed the need to compile PartUV from source in the container: the environment now installs the cached prebuilt `partuv` wheel and cached `torch_scatter` wheel, and the base image has been simplified to a plain Ubuntu image from a different registry.

### [2026-04-07 22:47] - none
- Fixed the submitted compute-node workflow so it no longer calls `scripts/download.sh` from `scripts/reproduce.sh`; the job now assumes pre-staged local assets, matching the cluster's no-internet constraint.
- Added fast preflight checks for the cached Common Shapes data and PartField checkpoint in `scripts/run.sh`.
- Corrected evaluation aggregation to use median seam length, matching Table 1 and `scoring/reference.json`.

### [2026-04-07 22:58] - none
- Another environment build failed before `%post` while pulling the Microsoft Container Registry base image; the failure occurred during OCI blob fetch, not Python package installation.
- Switched `environment/container.def` from the MCR devcontainer image to `Bootstrap: library` with `ubuntu:22.04`, and restored explicit Python installation in `%post` so the build no longer depends on the flaky OCI registry path.

## Stop Justification
