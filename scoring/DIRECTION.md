# Research Direction

## Research Problem
This paper improves UV unwrapping of 3D meshes — specifically, how to decompose a mesh into charts (disconnected regions) that can each be flattened to 2D with low distortion. The core challenge is that naive decomposition produces over-fragmented charts (hundreds or thousands), while optimal decomposition requires balancing chart count against distortion.

## Core Contribution
PartUV's key insight is that **combining semantic part priors with geometry-based heuristics** yields better chart decomposition than geometry alone. Specifically:
1. A learning-based method (PartField) provides high-level semantic decomposition
2. Two geometry-based heuristics (Normal clustering, OBB-based Merge) provide fine-grained chart decomposition
3. A top-down recursive tree search optimally balances chart count vs. distortion threshold
4. ABF++ provides high-quality angle-preserving flattening

The scientist should work on improving this kind of contribution: **better mesh-to-chart decomposition for UV mapping**, using any combination of semantic priors, geometric features, and optimization strategies.

## Approach Scope
The scientist may:
- Use or train learning-based part segmentation models (PointNet++, graph neural networks, etc.)
- Design new geometric heuristics for chart decomposition
- Modify the recursive search strategy or distortion metrics
- Implement alternative flattening algorithms (LSCM, ABF++, etc.)
- Improve UV packing strategies
- Use different face features (normals, curvature, dihedral angles, etc.)

## Out of Bounds
- Neural field optimization per mesh (Nuvo-style) that takes >5 minutes. The paper emphasizes both quality AND speed.
- Pure packing-only improvements without addressing the chart decomposition problem
- Switching to fundamentally different UV mapping approaches that ignore mesh structure
- Methods that drastically increase distortion to reduce chart count (the constraint is distortion ≤ ~1.4)
