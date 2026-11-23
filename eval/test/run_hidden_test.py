#!/usr/bin/env python3
"""Hidden test: run every method on disk on the held-out meshes and score what it produces.

A method is any folder ``<root>/<dir>/`` (default root: /home/user/checkpoints) holding an
entry script ``unwrap.sh``. It is called as

    bash <dir>/unwrap.sh <input_dir> <output_dir>

where ``<input_dir>`` holds the held-out meshes as ``<id>.obj`` (anonymous ids, no UVs) and the
method must write ``<output_dir>/<id>/uv.obj`` for each of them. The method is reported under
``<dir>`` with a trailing ``_repro`` removed.

The held-out meshes live only in eval/test/meshes/. They and the scoring code are loaded into
memory before any method runs; each method gets fresh copies in a temporary folder that is
deleted after scoring. scoring/scores_test.json is deleted first and written atomically at
the end, so a crashed run leaves no score file. Only the five scored numbers per method are
written there; nothing a method writes (other than its UV OBJs) is read.
"""

from __future__ import annotations

import hashlib
import json
import lzma
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from eval.test import uv_eval

EXPERIMENT = "common_shapes_comparison"
SCORED = ("success_rate", "avg_charts", "median_charts", "angular_distortion", "area_distortion")
ENTRY = "unwrap.sh"
OUTPUT_NAME = "uv.obj"
MESH_DIR = Path(__file__).resolve().parent / "meshes"
DEFAULT_ROOT = Path("/home/user/checkpoints")
DEFAULT_OUT = Path("/home/user/scoring/scores_test.json")
# Hang guard only (a method that never returns would otherwise block every other method's
# score). The reference finishes the whole held-out set in well under 10% of this.
GUARD_SECONDS = 4 * 3600


def log(msg: str) -> None:
    print(f"[hidden-test] {msg}", flush=True)


def load_meshes():
    manifest = json.loads((MESH_DIR / "manifest.json").read_text())
    meshes = []
    for entry in manifest["meshes"]:
        raw = lzma.decompress((MESH_DIR / entry["file"]).read_bytes())
        if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
            raise SystemExit(f"held-out mesh {entry['id']} does not match its checksum")
        inp = uv_eval.prepare_input(entry["id"], raw.decode("utf-8", errors="replace"))
        meshes.append((entry["id"], raw, inp))
    return meshes


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


def run_method(name: str, d: Path, meshes, tmp_root: str, guard: float):
    work = Path(tempfile.mkdtemp(prefix="uvtest_", dir=tmp_root))
    in_dir, out_dir = work / "input", work / "output"
    in_dir.mkdir()
    out_dir.mkdir()
    for mid, raw, _ in meshes:
        (in_dir / f"{mid}.obj").write_bytes(raw)
    t0 = time.time()
    rc = None
    try:
        with open(d / "hidden_test.log", "w") as lf:
            proc = subprocess.Popen(["bash", str(d / ENTRY), str(in_dir), str(out_dir)], cwd=str(d),
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
    per_mesh = []
    for mid, _, inp in meshes:
        p = out_dir / mid / OUTPUT_NAME
        t1 = time.time()
        if not p.is_file():
            r = uv_eval.failed_mesh(inp, f"no {OUTPUT_NAME} written")
        elif p.stat().st_size > uv_eval.MAX_OUTPUT_BYTES:
            r = uv_eval.failed_mesh(inp, "output file too large")
        else:
            try:
                r = uv_eval.evaluate_output(inp, p.read_text(errors="replace"))
            except Exception as exc:  # scoring never crashes the whole test
                print(f"[hidden-test] {name}/{mid}: scoring error {exc!r}", file=sys.stderr, flush=True)
                r = uv_eval.failed_mesh(inp, f"unscorable output ({type(exc).__name__})")
        r = dict(r, id=mid, eval_seconds=round(time.time() - t1, 2))
        per_mesh.append(r)
    shutil.rmtree(work, ignore_errors=True)
    return per_mesh, rc, runtime


def main() -> int:
    root = Path(os.environ.get("CHECKPOINTS_ROOT", str(DEFAULT_ROOT)))
    out = Path(os.environ.get("SCORES_TEST_JSON", str(DEFAULT_OUT)))
    details_path = os.environ.get("UV_TEST_DETAILS_JSON")
    out.unlink(missing_ok=True)
    meshes = load_meshes()
    methods = discover(root)
    if not methods:
        log(f"no method folders with {ENTRY} under {root}")
        return 1
    log(f"{len(meshes)} held-out meshes; methods: {', '.join(n for n, _ in methods)}")
    tmp_root = os.environ.get("TMPDIR") or tempfile.gettempdir()
    guard = float(os.environ.get("UV_EVAL_GUARD_SECONDS", GUARD_SECONDS))
    results, details = {}, {}
    for name, d in methods:
        log(f"running {name} ({d})")
        per_mesh, rc, runtime = run_method(name, d, meshes, tmp_root, guard)
        agg = uv_eval.aggregate(per_mesh)
        results[name] = {k: agg[k] for k in SCORED}
        details[name] = {"folder": str(d), "returncode": rc, "method_seconds": round(runtime, 1),
                         "scores": results[name], "per_mesh": per_mesh}
        log(f"{name}: rc={rc} t={runtime:.0f}s " + " ".join(f"{k}={v:.4f}" for k, v in results[name].items()))
    scores = {"experiments": {EXPERIMENT: {"results": results}}}
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_text(json.dumps(scores, indent=2))
    os.replace(tmp, out)
    log(f"wrote {out}")
    if details_path:
        Path(details_path).parent.mkdir(parents=True, exist_ok=True)
        Path(details_path).write_text(json.dumps(details, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
