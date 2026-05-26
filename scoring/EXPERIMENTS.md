# Experiment Overview

This file describes what each experiment in `scores.json` is trying to establish.
Each experiment corresponds to a key in the `experiments` object of `scores.json`.

## common_shapes_comparison

**What it tests:** Whether a UV unwrapping method produces fewer UV charts than a standard baseline on the Common Shapes 3D mesh dataset, while maintaining comparable chart-level distortion quality.

**Scientific purpose:** UV unwrapping of 3D meshes produces chart fragments, or disconnected regions that can be flattened. The goal is to minimize chart count without sacrificing mapping quality, measured by angular and area distortion. This experiment tests the core chart-count-to-quality tradeoff.

**Primary metric:** avg_charts (lower is better)

**How it was run:** Each method was run on all 24 Common Shapes meshes. Chart counts and distortion metrics were computed from each exported UV OBJ and aggregated. Seam length and overall atlas area distortion are logged in per-run JSON artifacts as diagnostics, but not scored because they depend on final atlas packing.
