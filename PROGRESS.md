# Progress

## What Works

- Briefing, scoring references, and the Common Shapes dataset are present.
- The workspace now targets the released PartUV codepath plus the public PartField Objaverse checkpoint rather than the earlier face-normal proxy.
- Offline resources are staged in the workspace:
  - `environment/wheels/partuv-0.1.2-...whl`
  - `environment/wheels/torch_scatter-2.1.2+pt27cu128-...whl`
  - `checkpoints/partfield/model_objaverse.ckpt`
- The active evaluation path now scores Common Shapes outputs with method-agnostic UV metrics: success rate, chart count, seam length, angular distortion, area distortion, overall area distortion, and runtime.
- The submitted run path is now compute-safe: it only consumes already-cached local assets and no longer tries to download data or checkpoints on the no-internet cluster nodes.
- The environment has been simplified again to minimize container-build surface area: `container.def` now targets `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`, which already includes Python 3.12 and `uv`, and `%post` only installs a small set of runtime shared libraries.
- The base image is now staged locally as `environment/base-uv-python312-bookworm-slim.tar`, and `container.def` consumes that archive with `Bootstrap: docker-archive` so container builds no longer depend on live registry metadata.
- The archive source in `container.def` is now repo-relative rather than `/home/user`-absolute, because the build worker resolves local files from its checked-out workspace, not from the interactive login-node path.
- The builder appears to resolve `docker-archive` paths from the `environment/` directory itself, so the archive reference has been tightened further to the sibling filename `base-uv-python312-bookworm-slim.tar`.
- The latest error contradicts that intermediate hypothesis: with the tarball committed, `open base-uv-python312-bookworm-slim.tar: no such file or directory` shows the builder is resolving local archive paths from repo root. `container.def` has therefore been switched back to `environment/base-uv-python312-bookworm-slim.tar`.

## Results Achieved

- No valid reproduction numbers are claimed yet for the paper's actual algorithm.
- Previous proxy-based scores were invalid for milestone purposes and have been cleared.
- The audit confirms the active method path is faithful in structure, but there is still no execution evidence for `method_runs` or higher.

## What Remains

- Install the official runtime in the container overlay.
- Run the official PartField preprocessing + PartUV pipeline on at least one Common Shapes mesh.
- Extend evaluation and baseline comparison to support a defensible `core_claim`.

## Issues Encountered

- The prior implementation substituted PartField with face normals; this invalidated earlier milestone and score claims.
- `/home/user/shared/models` is read-only in this workspace, so the PartField checkpoint must be cached under the workspace instead.
- `python validate.py` still fails before the first real run because `scoring/scores.json` is intentionally empty until the official pipeline produces outputs.
- A legacy `logs/eval_run.log` from the earlier surrogate path is still present and should not be treated as evidence for the current official pipeline.
- The first container build failed before job submission because the Docker Hub pull for the CUDA base image hit an unauthenticated rate limit; the base image source has been switched to `nvcr.io` to avoid that transient infrastructure failure.
- The second container build also failed during OCI image fetch from the alternate registry. To remove that dependency and avoid a source build, the environment now installs the cached prebuilt `partuv` wheel and uses a plain Ubuntu base image instead of a CUDA-devel image.
- Before this turn, `scripts/reproduce.sh` still invoked `scripts/download.sh`, which would have failed or hung on compute because internet is unavailable there. That submission path has now been corrected.
- The latest build failure was again pre-`%post`: the scheduler could not fully fetch the MCR devcontainer base image due to an HTTP/2 stream cancellation while downloading a blob. The base image source has been changed again so the next submission exercises a different fetch path.
- The subsequent `Bootstrap: library` attempt also failed before `%post`, but for a different cluster-level reason: no default Apptainer library remote is configured.
- The follow-up Quay-based manylinux attempt also failed before `%post`, again during OCI metadata retrieval (`invalid character 's' after top-level value`). The environment has now been moved to a smaller GHCR-hosted Debian image that already carries Python and `uv`.
- The GHCR direct pull hit the same malformed metadata failure, so the registry itself remains the unstable component. The current workaround is to prefetch that exact image into a local docker archive using `crane` on the login node and build from the archive instead of from the registry.
- The first docker-archive submission still failed because `container.def` used an absolute `/home/user/...` path, but the builder did not have that path in its own filesystem. The archive source has now been changed to a repo-relative path and will be committed so it exists in the scheduler's checkout.
- The next attempt showed that the repo-relative `environment/...` path was still one directory too deep for the builder's working directory. The archive reference now points directly at the sibling tarball beside `container.def`.
- That hypothesis turned out to be wrong because it was confounded by the tarball not yet being present in the scheduler checkout. With the tarball now committed, the sibling-path attempt failed, so the correct fix is to keep the committed archive under `environment/` and reference it from repo root.

## Deviations from Paper

- None claimed yet for the active execution path. The intent is to run the released PartUV method with the public Objaverse-trained PartField checkpoint.
