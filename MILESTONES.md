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

### [2026-04-07 23:08] - none
- The `library` bootstrap path also failed before `%post` because this cluster has no default Apptainer library remote configured.
- Switched `environment/container.def` again to `quay.io/pypa/manylinux_2_28_x86_64:latest`, pinned `/opt/python/cp312-cp312` as the default interpreter, and made `environment/setup.sh` bootstrap `uv` if the base image does not already provide it.

### [2026-04-07 23:17] - none
- The Quay-based build also failed before `%post`, with malformed registry metadata returned during the OCI fetch; the failure is still in external image retrieval rather than the Python environment.
- Switched `environment/container.def` to `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`, which already provides Python 3.12 and `uv`, and reduced `%post` to a small set of Debian runtime libraries needed by the cached wheels.

### [2026-04-07 23:22] - none
- The GHCR-based attempt hit the same malformed-registry-response failure before `%post`, confirming the issue is the build-time registry fetch rather than a particular image choice.
- Downloaded the 66 MB `ghcr.io/astral-sh/uv:python3.12-bookworm-slim` image into `/home/user/environment/base-uv-python312-bookworm-slim.tar` with `crane`, and switched `environment/container.def` to `Bootstrap: docker-archive` so Apptainer reads the base image from the local workspace instead of querying a registry.

### [2026-04-07 23:29] - none
- The first docker-archive attempt failed because the build worker did not have a `/home/user` path during environment assembly, so the absolute archive path in `container.def` was invalid there.
- Changed `container.def` to reference the archive via the repo-relative path `environment/base-uv-python312-bookworm-slim.tar` and prepared to include that archive in git so the build worker can read it from its checked-out workspace.

### [2026-04-07 23:34] - none
- The repo-relative `environment/...` path also failed: the builder is resolving the archive path from the `environment/` directory where `container.def` lives, so it looked for `environment/environment/...`.
- Adjusted `container.def` to use the sibling filename `base-uv-python312-bookworm-slim.tar` directly, which matches the committed archive location next to the definition file.

### [2026-04-07 23:39] - none
- The sibling-path attempt failed with `open base-uv-python312-bookworm-slim.tar: no such file or directory`, which shows the builder is actually resolving local archive paths from the repo root, not from the `environment/` directory.
- Restored `container.def` to the repo-root-relative path `environment/base-uv-python312-bookworm-slim.tar`; unlike the first time this path was tried, the tarball is now committed and present in the checkout.

### [2026-04-07 23:45] - none
- The repo-root-relative archive path still failed even with the tarball committed, which indicates the scheduler's environment build does not make arbitrary sidecar files available to the bootstrap agent.
- Dropped the local docker-archive workaround entirely and switched `environment/container.def` to Apptainer's built-in `arch` bootstrap agent, which avoids both OCI registry metadata fetches and local archive path resolution.

### [2026-04-07 23:51] - none
- The `arch` bootstrap attempt failed immediately because the build host does not provide `pacstrap`, which Apptainer's Arch bootstrap agent requires.
- Replaced the bootstrap again with `Bootstrap: scratch` plus a `%setup` step that downloads and untars Canonical's Ubuntu 22.04 core rootfs directly into `$APPTAINER_ROOTFS`, keeping the build off OCI registries and off host-specific bootstrap tools.

## Stop Justification
