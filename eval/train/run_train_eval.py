#!/usr/bin/env python3
"""Train-split evaluation: run every method on disk on the visible training meshes and score it.

Same interface as the hidden test. A method is any folder ``<root>/<dir>/`` (default root:
/home/user/checkpoints) holding an entry script ``unwrap.sh``, called as

    bash <dir>/unwrap.sh <input_dir> <output_dir>

``<input_dir>`` holds the training meshes as ``<name>.obj``; the method must write
``<output_dir>/<name>/uv.obj``. Outputs are kept in ``<dir>/train_outputs/`` together with
per-mesh diagnostics (``results_train.json``). With ``UV_TRAIN_REUSE=1`` a method whose
``train_outputs/`` already holds a ``uv.obj`` for every training mesh is rescored without
being run again. Scores go to scoring/scores_train.json (written atomically).
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from eval.train import uv_eval

EXPERIMENT = "common_shapes_comparison"
SCORED = ("success_rate", "avg_charts", "median_charts", "angular_distortion", "area_distortion")
ENTRY = "unwrap.sh"
OUTPUT_NAME = "uv.obj"
DATA_DIR = Path("/home/user/data/downloads/common_shapes")
TRAIN_MESHES = (
    "beast", "beetle", "bimba", "cheburashka", "fandisk", "homer",
    "igea", "max-planck", "ogre", "spot", "suzanne", "woody",
)
DEFAULT_ROOT = Path("/home/user/checkpoints")
DEFAULT_OUT = Path("/home/user/scoring/scores_train.json")
GUARD_SECONDS = 4 * 3600


def log(msg: str) -> None:
    print(f"[train-eval] {msg}", flush=True)


def discover(root: Path):
    found = []
    if root.is_dir():
        for d in sorted(p for p in root.iterdir() if p.is_dir()):
            if (d / ENTRY).is_file():
                found.append(d)
    names, out = set(), []
    for d in found:
        name = d.name[: -len("_repro")] if d.name.endswith("_repro") and len(d.name) > 6 else d.name
        if name in names:
            name = d.name
        names.add(name)
        out.append((name, d))
    return out


def main() -> int:
    root = Path(os.environ.get("CHECKPOINTS_ROOT", str(DEFAULT_ROOT)))
    out = Path(os.environ.get("SCORES_TRAIN_JSON", str(DEFAULT_OUT)))
    reuse = os.environ.get("UV_TRAIN_REUSE", "") == "1"
    guard = float(os.environ.get("UV_EVAL_GUARD_SECONDS", GUARD_SECONDS))
    out.unlink(missing_ok=True)
    meshes = []
    for name in TRAIN_MESHES:
        path = DATA_DIR / f"{name}.obj"
        if not path.is_file():
            log(f"missing training mesh {path}; run scripts/download.sh")
            return 1
        raw = path.read_bytes()
        meshes.append((name, raw, uv_eval.prepare_input(name, raw.decode("utf-8", errors="replace"))))
    methods = discover(root)
    if not methods:
        log(f"no method folders with {ENTRY} under {root}")
        return 1
    log(f"{len(meshes)} training meshes; methods: {', '.join(n for n, _ in methods)}")
    tmp_root = os.environ.get("TMPDIR") or tempfile.gettempdir()
    results = {}
    for name, d in methods:
        out_dir = d / "train_outputs"
        have_all = all((out_dir / m / OUTPUT_NAME).is_file() for m, _, _ in meshes)
        rc, runtime = "reused", 0.0
        if not (reuse and have_all):
            shutil.rmtree(out_dir, ignore_errors=True)
            out_dir.mkdir(parents=True)
            work = Path(tempfile.mkdtemp(prefix="uvtrain_", dir=tmp_root))
            for m, raw, _ in meshes:
                (work / f"{m}.obj").write_bytes(raw)
            log(f"running {name} ({d})")
            t0 = time.time()
            try:
                with open(d / "train_eval.log", "w") as lf:
                    proc = subprocess.Popen(["bash", str(d / ENTRY), str(work), str(out_dir)], cwd=str(d),
                                            stdout=lf, stderr=subprocess.STDOUT, start_new_session=True)
                    try:
                        rc = proc.wait(timeout=guard)
                    except subprocess.TimeoutExpired:
                        os.killpg(proc.pid, signal.SIGKILL)
                        proc.wait()
                        rc = "hang-guard"
            except OSError as exc:
                rc = f"could not start: {exc}"
            runtime = time.time() - t0
            shutil.rmtree(work, ignore_errors=True)
        per_mesh = []
        for m, _, inp in meshes:
            p = out_dir / m / OUTPUT_NAME
            t1 = time.time()
            if not p.is_file():
                r = uv_eval.failed_mesh(inp, f"no {OUTPUT_NAME} written")
            elif p.stat().st_size > uv_eval.MAX_OUTPUT_BYTES:
                r = uv_eval.failed_mesh(inp, "output file too large")
            else:
                try:
                    r = uv_eval.evaluate_output(inp, p.read_text(errors="replace"))
                except Exception as exc:
                    print(f"[train-eval] {name}/{m}: scoring error {exc!r}", file=sys.stderr, flush=True)
                    r = uv_eval.failed_mesh(inp, f"unscorable output ({type(exc).__name__})")
            per_mesh.append(dict(r, name=m, eval_seconds=round(time.time() - t1, 2)))
        agg = uv_eval.aggregate(per_mesh)
        results[name] = {k: agg[k] for k in SCORED}
        (out_dir / "results_train.json").write_text(json.dumps(
            {"method": name, "returncode": rc, "method_seconds": round(runtime, 1),
             "scores": results[name], "per_mesh": per_mesh}, indent=2))
        log(f"{name}: rc={rc} t={runtime:.0f}s " + " ".join(f"{k}={v:.4f}" for k, v in results[name].items()))
    scores = {"experiments": {EXPERIMENT: {"results": results}}}
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_text(json.dumps(scores, indent=2))
    os.replace(tmp, out)
    log(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
