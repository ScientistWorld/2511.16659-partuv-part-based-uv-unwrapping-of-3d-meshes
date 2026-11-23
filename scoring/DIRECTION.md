# Research Direction

## Research Problem
UV unwrapping of 3D meshes: decompose a mesh into charts that can each be flattened to 2D with
low distortion. Naive decompositions produce hundreds or thousands of charts; the challenge is to
use as few charts as possible while every chart stays injective and within a distortion bound.

## Direction
Produce fewer charts on unseen meshes while keeping every chart valid (continuous, fold- and
overlap-free, area distortion <= 1.25) and angular distortion low. The bound is fixed by the
evaluator: raising it, or outputting charts that break it, is scored as failure, not as fewer
charts.

## Approach Scope
The scientist may:
- Use geometry-only, learning-based, optimization-based, or hybrid chart decomposition methods
- Design new mesh features, part priors, region objectives or search strategies
- Change the flattening algorithm, or post-process charts (e.g. merging neighbours) as long as the
  merged charts stay valid
- Spend more computation per mesh (runtime is not scored), as long as the method runs offline on
  meshes it has not seen

## Out of Bounds
- Packing-only changes (they do not change any scored metric)
- Altering the input surface (vertex positions, triangles) or dropping parts of it
- Changing the benchmark meshes, metric definitions, thresholds or score files
- Per-mesh tuning keyed on the identity of held-out meshes
