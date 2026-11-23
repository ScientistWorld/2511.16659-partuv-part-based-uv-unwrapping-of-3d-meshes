#!/usr/bin/env python3
"""Rebuild eval/test/meshes/*.obj.xz from the public Common Shapes archive if any is missing.

    python3 eval/test/fetch_meshes.py <common-3d-test-models-master.zip>

The held-out meshes are committed in compressed form; this is only the provenance path
(same files, checked against the sha256 sums in manifest.json).
"""
import hashlib
import json
import lzma
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent / "meshes"


def main() -> int:
    man = json.loads((HERE / "manifest.json").read_text())
    missing = [e for e in man["meshes"] if not (HERE / e["file"]).is_file()]
    if not missing:
        print("held-out meshes present")
        return 0
    with zipfile.ZipFile(sys.argv[1]) as zf:
        names = {Path(n).name: n for n in zf.namelist() if n.endswith(".obj")}
        for e in missing:
            raw = zf.read(names[Path(e["source"]).name])
            if hashlib.sha256(raw).hexdigest() != e["sha256"]:
                raise SystemExit(f"checksum mismatch for {e['id']}")
            (HERE / e["file"]).write_bytes(lzma.compress(raw, preset=9 | lzma.PRESET_EXTREME))
            print(f"rebuilt {e['file']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
