# Reproduction Milestones

**Current: core_claim**

## Progress Log

### [2026-05-26 18:28] - method_runs
- Packaged the released PartUV pipeline and verified that it executes end-to-end in the compute container on Common Shapes meshes.
- Confirmed the active method path uses PartField inference, hierarchical part-tree construction, top-down recursive chart search, Normal/Merge heuristics, ABF-based unwrapping, and UV OBJ export.

### [2026-05-26 18:40] - core_claim
- Completed a full Common Shapes reproduction with xatlas and PartUV outputs scored by the method-agnostic evaluator.
- Reproduced the central chart-fragmentation claim: PartUV produced 48.71 average charts versus 945.83 for xatlas, matching the paper's 48.6 average charts for PartUV on Common Shapes.
- Preserved the main distortion constraint: PartUV angular distortion was 0.990, matching the paper's 0.990 and above the reproduced xatlas value of 0.941.
- `python3 validate.py --compare` passes with import separation, portable path, and eval-output checks.

## Stop Justification
- Stopping at `core_claim`: the reusable environment is packaged, validated, and the minimum paper claim is supported on Common Shapes. Higher milestones would require adding Trellis, ABC, PartObjaverseTiny, Open3D/Nuvo/OptCuts comparisons, and ablations.
