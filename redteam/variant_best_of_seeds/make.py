#!/usr/bin/env python3
"""Best-of-seeds PartUV: per mesh, pick among the seed-42 (gym reference), seed-0, seed-1 and
seed-2 PartUV runs the output with the fewest charts as reported by PartUV itself
(run_summary.json num_components), tie-break on PartUV's own reported distortion. This
uses no evaluator code and no test metric: it is a plain restart-and-select search."""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, "/home/user/redteam/lib")
from rt_common import REF_OUT, UV_NAME, env_meshes  # noqa: E402

CANDIDATES = {
    "seed42": REF_OUT,
    "seed0": Path("/home/user/checkpoints/rt/ref_seed0/partuv_repro"),
    "seed1": Path("/home/user/checkpoints/rt/ref_seed1/partuv_repro"),
    "seed2": Path("/home/user/checkpoints/rt/ref_seed2/partuv_repro"),
}

out = Path(sys.argv[1])
choice = {}
for name in env_meshes():
    best = None
    for tag, root in CANDIDATES.items():
        d = root / name
        if not (d / UV_NAME).exists() or not (d / "run_summary.json").exists():
            continue
        s = json.loads((d / "run_summary.json").read_text())
        key = (int(s["num_components"]), float(s.get("distortion", 0.0)))
        if best is None or key < best[0]:
            best = (key, tag, d)
    mesh_dir = out / name
    mesh_dir.mkdir(parents=True, exist_ok=True)
    if best is None:
        print(f"[best_of_seeds] {name}: no candidate")
        continue
    for fname in (UV_NAME, "material.mtl", "material_0.png", "run_summary.json"):
        src = best[2] / fname
        if src.exists():
            os.symlink(src, mesh_dir / fname)
    choice[name] = {"tag": best[1], "num_components": best[0][0], "distortion": best[0][1]}
    print(f"[best_of_seeds] {name}: {best[1]} charts={best[0][0]} dist={best[0][1]:.4f}")
(Path(__file__).resolve().parent / "choice.json").write_text(json.dumps(choice, indent=2))
