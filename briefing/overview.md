# Overview

- **Paper ID:** 2511.16659
- **Title:** PartUV: Part-Based UV Unwrapping of 3D Meshes
- **Domain:** Computer Graphics / 3D Geometry Processing
- **TL;DR:** PartUV uses learning-based part decomposition combined with geometry-based heuristics and recursive search to produce UV unwrappings with significantly fewer charts than existing tools, while maintaining low distortion and part-aligned boundaries.

## Short Summary

UV unwrapping flattens 3D meshes onto 2D planes for texture mapping. Existing methods (xatlas, Blender) often produce highly fragmented charts on complex meshes. PartUV introduces a two-stage approach: first uses PartField (a learning-based method) for semantic part decomposition, then applies two geometry-based heuristics (Normal clustering and OBB-based Merge) in a top-down recursive search with ABF++ flattening. The result is fewer charts with boundaries aligned to meaningful object parts, while keeping distortion low.

## Key Results

- On Common Shapes (24 meshes): PartUV produces 48.6 average charts vs 974.8 (xatlas) and 1360.3 (Blender) — a 20x-28x reduction
- On Trellis (114 AI-generated meshes): 568.7 average charts vs 1541.6 (xatlas) — 2.7x reduction
- On PartObjaverseTiny (200 man-made meshes): 544.8 average charts vs 1142.1 (xatlas) — 2.1x reduction
- Angular distortion remains high (~0.98) across datasets, comparable to baselines
- 100% success rate across all four datasets
- Runtime: typically a few to tens of seconds per mesh
