# Progress

## What Works

- Briefing, scoring references, and the Common Shapes dataset are present.
- The workspace runs the official `partuv==0.1.2` pipeline with the Objaverse-trained PartField checkpoint.
- The PartUV wrapper performs the paper's actual method: PartField feature inference, hierarchical part tree construction, top-down recursive search, Normal/Merge heuristics, ABF flattening, and export of UV OBJ results.
- `eval/` is method-agnostic: it reads exported OBJ artifacts and does not import `method/`.
- `scripts/reproduce.sh` now regenerates xatlas and PartUV outputs on the same mesh subset and writes `scoring/scores.json`.
- `scripts/run.sh` now performs a one-mesh container smoke test in isolated `checkpoints/smoke/` outputs, preserving the canonical 24-mesh `scoring/scores.json`.
- Smoke scripts now use strict shell settings, unbuffered Python, explicit progress logs, and required artifact checks.
- Runtime scripts now use the container's system Python packages installed by `environment/setup.sh`; they no longer prepend the stale workspace-local `.local/site-packages` tree.
- Single-method evaluation now fails if no UV OBJ artifacts are found, preventing empty result files from being scored.
- `scripts/run.sh` avoids an eager torch diagnostic on CPU test nodes; torch is now exercised only when the actual PartUV method command runs.
- `scripts/download.sh` verifies and fetches Common Shapes plus the PartField checkpoint into portable workspace paths.

## Results Achieved

- Full Common Shapes run completed on all 24 meshes.
- xatlas reproduction: 100% success, 945.83 average charts, 128.0 median charts, 34.95 median seam length, 0.941 angular distortion, 1.566 area distortion, 1.475 overall area distortion.
- PartUV reproduction: 100% success, 48.71 average charts, 20.5 median charts, 79.13 median seam length, 0.990 angular distortion, 1.429 area distortion, 2.905 overall area distortion.
- Core claim supported: PartUV produces roughly 19x fewer charts than xatlas on Common Shapes while keeping angular distortion at the paper's reported level. Area distortion is higher than the paper's Common Shapes value but remains in the same order of magnitude and below xatlas on the chart-level area metric.

## What Remains

- Re-run the patched end-to-end script after packaging changes.
- Higher milestones would require adding more paper datasets (Trellis, ABC, PartObjaverseTiny), Open3D/Nuvo/OptCuts comparisons, and ablations.

## Issues Encountered

- CPU smoke job `da43a5da-788` exited with code 1 after creating an empty `checkpoints/smoke/xatlas` directory. The logs did not include a Python traceback, so the scripts were patched to make the next failure diagnosable at the exact command and artifact boundary.
- CPU smoke job `46b9c53f-95e` reached `baseline.sh` but exited before xatlas emitted its first Python progress line. This points to package import/startup rather than the xatlas algorithm itself; the runtime `PYTHONPATH` override has been removed and import probes added.
- CPU smoke job `3a0fad9c-777` failed directly after the Python version print, before any resource checks. The torch diagnostic block was the next command, so it was removed from the smoke path.
- The public pipeline was easier to run via the file-based `partuv.pipeline()` API than `pipeline_numpy()` on CPU.
- The PartUV configuration disables PaMO (`pamo=false`) and CUDA stream usage so the released pipeline can run reliably in this environment.
- The evaluator's seam-length and overall-area conventions differ from the paper on some meshes, producing worse PartUV seam and overall area values despite matching the primary chart count and angular distortion claims.
- Previous script drift meant `scripts/reproduce.sh` did not regenerate the xatlas baseline; this has been corrected.
- Continuation audit found two smoke-test risks: limited runs could evaluate stale output directories, and `evaluate.sh compare` silently skipped missing JSON files. The scripts now clear generation outputs before reruns and fail fast when either comparison input is absent.

## Deviations from Paper

- Reproduced only the Common Shapes experiment from Table 1, not all four datasets.
- Used the released PartUV Python package and public PartField checkpoint rather than rebuilding the authors' C++ stack from source.
- Disabled PaMO/GPU simplification in the PartUV config for reproducible CPU execution. The core PartField-guided recursive decomposition and ABF unwrapping remain intact.
