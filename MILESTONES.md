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

### [2026-05-26 18:34] - core_claim
- Audited the inherited workspace after the milestone reset and confirmed the active method path is the released PartUV algorithm, not a surrogate.
- Tightened scoring to exclude packing-dependent seam and overall-atlas area metrics from `scores.json`; those metrics remain logged as diagnostics because the reproduced export is the released un-packed chart-component output.
- Revalidated the environment with `python3 validate.py --compare`.

### [2026-05-26 19:45] - core_claim
- Completed final verification of the gym packaging.
- Confirmed method-agnostic evaluation separation, portable downloads, train/test split consistency, and score comparability with `python3 validate.py --compare`.
- Cleaned method-agnostic documentation and moved large fetched data under `data/downloads/`.

### [2026-05-26 19:46] - core_claim
- Re-ran `python3 validate.py --compare` during autonomous final audit; all scoring, import-separation, portable-path, train/test, and score-discrimination checks passed.
- Cross-checked paper analysis: the implemented path matches PartUV's PartField-guided tree search with Normal/Merge heuristics, ABF unwrapping, and distortion-bounded chart selection.

### [2026-05-26 19:58] - core_claim
- Completed final verification report.
- Confirmed `scripts/evaluate.sh compare` works standalone on existing artifacts and regenerates `scoring/scores.json`.
- Verified both dataset/model download URLs used by `scripts/download.sh` return HTTP 200 responses.

## Stop Justification
- Completed at milestone `core_claim`.
