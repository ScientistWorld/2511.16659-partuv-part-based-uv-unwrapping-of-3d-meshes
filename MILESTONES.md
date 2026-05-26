# Reproduction Milestones

**Current: core_claim**

## Progress Log

### [2026-05-26 18:28] - core_claim
- Continuing-agent audit confirmed the claimed reproduction path is `method/official_pipeline.py`, which runs the released PartUV implementation with PartField inference and paper settings rather than the legacy prototype.
- Fixed audit issues by removing wall-clock `avg_time` from scored metrics and regenerating `scoring/scores.json` from existing method/baseline artifacts through `scripts/evaluate.sh`.
- Removed a stale baseline fallback dependency on `method/` and documented legacy prototype modules so they are not mistaken for the claimed method.
- `python3 validate.py --compare` passes after the fixes.

### [2026-05-26 18:26] - core_claim
- Implemented and packaged the actual PartUV pipeline using PartField feature inference, hierarchical part-tree construction, recursive PartTreeSearch, Normal/Merge chart candidates, ABF flattening, and UV OBJ export.
- Reproduced the Common Shapes comparison against xatlas on all 24 meshes.
- `python3 validate.py --compare` passes, with PartUV producing 48.71 average charts versus xatlas 945.83 while maintaining 100% success and paper-level angular distortion.

## Stop Justification
- Completed at milestone `core_claim`.
