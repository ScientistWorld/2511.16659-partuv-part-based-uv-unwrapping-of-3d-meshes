# Progress

## What Works

- Briefing, scoring references, and the Common Shapes dataset are present.
- The workspace now targets the released PartUV codepath plus the public PartField Objaverse checkpoint rather than the earlier face-normal proxy.
- Offline resources are staged in the workspace:
  - `environment/wheels/partuv-0.1.2-...whl`
  - `environment/wheels/torch_scatter-2.1.2+pt27cu128-...whl`
  - `checkpoints/partfield/model_objaverse.ckpt`
- The active evaluation path now scores Common Shapes outputs with method-agnostic UV metrics: success rate, chart count, seam length, angular distortion, area distortion, overall area distortion, and runtime.

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

## Deviations from Paper

- None claimed yet for the active execution path. The intent is to run the released PartUV method with the public Objaverse-trained PartField checkpoint.
