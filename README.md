# PartUV: Part-Based UV Unwrapping of 3D Meshes

<!-- scope-note -->
> [!NOTE]
> **Not a full reproduction of the paper.** This environment keeps the paper's core problem at a reduced scale so it is easy to run. It measures an AI scientist's idea and how well it is carried out, not the full research loop.

| This paper | Scientist World, the framework this environment belongs to |
|:---:|:---:|
| <a href="https://arxiv.org/abs/2511.16659"><img alt="This paper on arXiv" src="https://img.shields.io/badge/arXiv-2511.16659-b31b1b?logo=arxiv&logoColor=white"></a> | <a href="https://arxiv.org/abs/2611.08478"><img alt="Scientist World on arXiv" src="https://img.shields.io/badge/arXiv-2611.08478-b31b1b?logo=arxiv&logoColor=white"></a> <a href="https://github.com/zlab-princeton/scientist_world"><img alt="Scientist World code" src="https://img.shields.io/badge/Code-Scientist_World-181717?logo=github&logoColor=white"></a> <a href="https://github.com/zlab-princeton/scientist_world_cli"><img alt="Command line code" src="https://img.shields.io/badge/Code-Command_line-181717?logo=github&logoColor=white"></a> |

| **Paper ID** | [2511.16659](https://arxiv.org/abs/2511.16659) |
|:---|:---|
| **Domain** | Computer Graphics / 3D Geometry Processing |
| **TL;DR** | PartUV uses learning-based part decomposition combined with geometry-based heuristics and recursive search to produce UV unwrappings with significantly fewer charts than existing tools, while maintaining low distortion and part-aligned boundaries. |

## Summary

UV unwrapping flattens 3D meshes onto 2D planes for texture mapping. Existing methods (xatlas, Blender) often produce highly fragmented charts on complex meshes. PartUV introduces a two-stage approach: first uses PartField (a learning-based method) for semantic part decomposition, then applies two geometry-based heuristics (Normal clustering and OBB-based Merge) in a top-down recursive search with ABF++ flattening. The result is fewer charts with boundaries aligned to meaningful object parts, while keeping distortion low.

## Problem

UV unwrapping projects 3D mesh surfaces onto 2D planes by assigning every 3D surface point a corresponding 2D UV coordinate. For complex meshes, flattening the entire surface into a single 2D chart introduces large distortion. Chart segmentation (seam cutting) divides the mesh into multiple charts, each flattened separately, but existing methods often produce highly fragmented charts — a single chart may contain only one or a handful of triangles — which hampers texture painting, introduces artifacts at chart boundaries, and burdens downstream applications.

## The paper's method

PartUV introduces a **part-based UV unwrapping pipeline** that combines semantic part decomposition (via a learning-based method called PartField) with geometry-based heuristics in a top-down recursive tree search. The key insight is that leveraging high-level semantic priors for mesh decomposition — rather than relying solely on local geometric properties — yields significantly fewer, part-aligned charts while maintaining low distortion.

## Key results of the paper

- On Common Shapes (24 meshes): PartUV produces 48.6 average charts vs 974.8 (xatlas) and 1360.3 (Blender) — a 20x-28x reduction
- On Trellis (114 AI-generated meshes): 568.7 average charts vs 1541.6 (xatlas) — 2.7x reduction
- On PartObjaverseTiny (200 man-made meshes): 544.8 average charts vs 1142.1 (xatlas) — 2.1x reduction
- Angular distortion remains high (~0.98) across datasets, comparable to baselines
- 100% success rate across all four datasets

## Run it

```bash
pip install sciworld
sw research 2511.16659 --mode innovate --agent claude-code
sw evaluate 2511.16659
```

## More

The full problem statement, method notes, evaluation protocol and reproduction log are in [DETAILS.md](DETAILS.md).

