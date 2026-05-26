# Research Direction

## Research Problem
This paper improves UV unwrapping of 3D meshes — specifically, how to decompose a mesh into charts (disconnected regions) that can each be flattened to 2D with low distortion. The core challenge is that naive decomposition produces over-fragmented charts (hundreds or thousands), while optimal decomposition requires balancing chart count against distortion.

## Direction
Future work should improve mesh-to-chart decomposition for UV mapping: produce fewer disconnected charts while preserving low angular and area distortion. The scoring rewards improvements that keep the same benchmark, output format, and metric definitions, so better methods should be evaluated through the existing UV OBJ artifact interface rather than by changing the evaluator.

## Approach Scope
The scientist may:
- Use geometry-only, learning-based, optimization-based, or hybrid chart decomposition methods
- Design new mesh features, region objectives, or search strategies for reducing chart count
- Change flattening or packing components if the output remains a valid UV-mapped OBJ
- Add additional training data or pretraining only if Common Shapes remains the reported benchmark
- Log extra diagnostics, as long as the scored metrics stay unchanged

## Out of Bounds
- Pure packing-only improvements without addressing the chart decomposition problem
- Switching to fundamentally different UV mapping approaches that ignore mesh structure
- Methods that drastically increase distortion to reduce chart count (the constraint is distortion ≤ ~1.4)
- Changing the benchmark meshes, metric definitions, or score files instead of improving the method outputs
