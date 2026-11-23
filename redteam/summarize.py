#!/usr/bin/env python3
"""Tabulate every red-team scenario's hidden-test score against the gym reference.

Pure standard library. Reads redteam/<name>/scores_test.json (copied right after the
no-argument `bash scripts/evaluate_test.sh` run) and redteam/reference_scores_test.json
(the gym's scoring/scores_test.json at the start of this iteration).

Proxy rank: sum over scored metrics of |coefficient| * improvement-in-better-direction /
spread, where spread is the population std of that metric across the honest PartUV runs
here (gym reference, reference seeds, variants, tau sweep; xatlas excluded). The real ranker normalizes by the
spread across future attempts, which is unknown; this proxy only indicates the sign/scale.
"""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

RT = Path(__file__).resolve().parent
EXP = "common_shapes_comparison"
REF = json.loads((RT / "reference_scores_test.json").read_text())["experiments"][EXP]["results"]
COEF = json.loads((RT.parent / "scoring" / "reference.json").read_text())["experiments"][EXP]["metrics"]
METRICS = ["success_rate", "avg_charts", "median_charts", "angular_distortion", "area_distortion"]
HONEST = ["ref_seed0", "ref_seed1", "ref_seed2", "ref_seed42", "variant_best_of_seeds", "variant_lscm", "variant_normals",
          "variant_more_search", "variant_tau_1p1", "variant_tau_1p5", "shortcut_high_tau", "bruteforce_tau_inf"]
SEEDS = ["ref_seed0", "ref_seed1", "ref_seed2"]


def load(name: str):
    d = RT / name
    status = json.loads((d / "hidden_test_status.json").read_text()) if (d / "hidden_test_status.json").exists() else None
    scores = json.loads((d / "scores_test.json").read_text()) if (d / "scores_test.json").exists() else None
    results = scores["experiments"][EXP]["results"] if scores else {}
    return status, results


def better(m: str, value: float, ref: float) -> float:
    sign = 1.0 if COEF[m]["higher_is_better"] else -1.0
    return sign * (value - ref)


def main() -> None:
    names = sorted(p.name for p in RT.iterdir() if p.is_dir() and p.name != "lib" and (p / "run.sh").exists())
    rows = {}
    for n in names:
        status, results = load(n)
        rows[n] = {"status": status, "results": results}

    ref = REF["partuv"]
    # Spread proxy: honest PartUV runs only (seeds, variants, tau sweep) plus the gym reference. xatlas is
    # left out: its ~950 charts would dominate the chart spread, while future attempts cluster near PartUV.
    pop = [ref] + [rows[n]["results"]["partuv"] for n in HONEST if "partuv" in rows.get(n, {}).get("results", {})]
    spread = {}
    for m in METRICS:
        vals = [r[m] for r in pop if math.isfinite(r[m])]
        spread[m] = statistics.pstdev(vals) if len(vals) > 1 else float("nan")

    seed_vals = [ref] + [rows[n]["results"]["partuv"] for n in SEEDS if "partuv" in rows.get(n, {}).get("results", {})]
    seed_stats = {}
    for m in METRICS:
        v = [r[m] for r in seed_vals]
        seed_stats[m] = {"values": v, "mean": statistics.mean(v), "std": statistics.stdev(v) if len(v) > 1 else 0.0,
                         "range": max(v) - min(v)}

    def proxy(r: dict) -> float:
        # Non-finite metric values (NaN, inf) are skipped here, mirroring a ranker that skips missing
        # values; such rows are flagged in the "non-finite" column.
        total = 0.0
        for m in METRICS:
            if m not in r or r[m] is None or not math.isfinite(r[m]) or spread[m] == 0 or not math.isfinite(spread[m]):
                continue
            total += abs(COEF[m]["coefficient"]) * better(m, r[m], ref[m]) / spread[m]
        return total

    def nonfinite(r: dict) -> str:
        bad = [m for m in METRICS if m in r and (r[m] is None or not math.isfinite(r[m]))]
        return ",".join(bad) if bad else "-"

    table = []
    for n in names:
        res = rows[n]["results"]
        st = rows[n]["status"] or {}
        for method, r in sorted(res.items()):
            deltas = {m: better(m, r[m], ref[m]) for m in METRICS if m in r}
            dominates = all(deltas.get(m, -1) >= 0 for m in METRICS) and any(deltas.get(m, 0) > 0 for m in METRICS)
            beats_seed_spread = {m: deltas[m] > 2 * seed_stats[m]["std"] for m in METRICS if m in deltas}
            table.append({"scenario": n, "method": method, "evaluate_test_rc": st.get("evaluate_test_rc"),
                          **{m: r.get(m) for m in METRICS}, "dominates_reference": dominates,
                          "nonfinite": nonfinite(r), "better_by_2_seed_std": beats_seed_spread,
                          "proxy_rank_vs_reference": proxy(r)})
        if not res:
            table.append({"scenario": n, "method": None, "evaluate_test_rc": st.get("evaluate_test_rc")})

    out = {"reference": ref, "xatlas_reference": REF["xatlas"], "spread_used_for_proxy": spread,
           "seed_stats": seed_stats, "rows": table}
    (RT / "summary.json").write_text(json.dumps(out, indent=2))

    def fmt(x, nd=3):
        if x is None:
            return "-"
        if isinstance(x, float) and not math.isfinite(x):
            return str(x)
        return f"{x:.{nd}f}" if isinstance(x, float) else str(x)

    lines = ["| scenario | method | test rc | success | avg charts | median charts | angular | area | dominates ref | non-finite | proxy rank |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    lines.append(f"| gym reference (seed 42) | partuv | - | {fmt(ref['success_rate'],1)} | {fmt(ref['avg_charts'],2)} | {fmt(ref['median_charts'],1)} | {fmt(ref['angular_distortion'],4)} | {fmt(ref['area_distortion'],4)} | - | - | 0.00 |")
    x = REF["xatlas"]
    lines.append(f"| gym baseline | xatlas | - | {fmt(x['success_rate'],1)} | {fmt(x['avg_charts'],2)} | {fmt(x['median_charts'],1)} | {fmt(x['angular_distortion'],4)} | {fmt(x['area_distortion'],4)} | no | - | {proxy(x):.2f} |")
    for t in table:
        if t.get("method") is None:
            lines.append(f"| {t['scenario']} | (nothing written) | {t['evaluate_test_rc']} | | | | | | | | |")
            continue
        lines.append(f"| {t['scenario']} | {t['method']} | {t['evaluate_test_rc']} | {fmt(t['success_rate'],1)} | {fmt(t['avg_charts'],2)} | "
                     f"{fmt(t['median_charts'],1)} | {fmt(t['angular_distortion'],4)} | {fmt(t['area_distortion'],4)} | "
                     f"{'YES' if t['dominates_reference'] else 'no'} | {t['nonfinite']} | {t['proxy_rank_vs_reference']:.2f} |")
    lines.append("")
    lines.append("Seed spread (gym reference seed 42 + seeds 0,1,2): " + "; ".join(
        f"{m}: mean {seed_stats[m]['mean']:.4f}, std {seed_stats[m]['std']:.4f}, range {seed_stats[m]['range']:.4f}" for m in METRICS))
    lines.append("")
    lines.append("Proxy spread (pop. std over the gym reference + honest PartUV runs): " + ", ".join(f"{m} {spread[m]:.4g}" for m in METRICS))
    (RT / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
