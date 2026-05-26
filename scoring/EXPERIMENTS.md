# Experiment Overview

This file describes what each experiment in `scores.json` is trying to establish.
Each experiment corresponds to a key in the `experiments` object of `scores.json`.

## common_shapes_comparison

**What it tests:** Whether PartUV produces fewer UV charts than the xatlas baseline on the Common Shapes 3D mesh dataset, while maintaining comparable distortion quality.

**Scientific purpose:** UV unwrapping of 3D meshes produces chart fragments — disconnected regions that can be flattened. The goal is to minimize chart count (fewer seams, less fragmentation) without sacrificing mapping quality (low angular and area distortion). This experiment directly tests the core claim that PartUV achieves a better chart-count-to-quality tradeoff than xatlas.

**Primary metric:** avg_charts (lower is better)

**How it was run:** Both PartUV and xatlas were run on all 24 Common Shapes meshes. Chart counts and distortion metrics were computed from each exported UV OBJ and aggregated.
