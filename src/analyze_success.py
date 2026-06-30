"""Mine the ORIGINAL successful-attack corpus: what conditions make an attack succeed?

Uses CP's existing batch logs (zero new API): 500 payloads x N manager configs (worker fixed = Llama-3.1-8B),
each with the validated oracle grade. Per payload we get a CROSS-MANAGER success profile (how many managers it
hijacks), then characterize what predicts success: attack strategy, target-tool class, payload-text certainty
(the mother-paper driver), length, and strategy x tool cells.

Output: logs/success_analysis.json + a console report. This is the work-list the labeling workflow pipelines over.
"""
from __future__ import annotations
import sys, os, glob, json, re
from collections import defaultdict
from scipy import stats

CP = r"Z:\study\project\CP_bak"
sys.path.insert(0, os.path.join(CP, "cross_validation"))
from log_parser import parse_full_mas_log

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import certainty_core
DATA = os.path.join(HERE, "..", "data", "paradox_dataset_500.json")
OUT = os.path.join(HERE, "..", "logs", "success_analysis.json")

MAS_GLOB = os.path.join(CP, "logs", "batch_*_vs_Llama-3.1-8B_*.log")
MAS_RE = r"batch_(.+?)_vs_Llama-3\.1-8B"


def asr_of(cnt, n):
    return (cnt / n * 100) if n else 0.0


def main():
    data = {d["id"]: d for d in json.load(open(DATA, encoding="utf-8"))}

    # per-payload grade per manager
    by_payload = defaultdict(dict)        # pid -> {manager: grade}
    managers = []
    for f in sorted(glob.glob(MAS_GLOB)):
        m = re.search(MAS_RE, os.path.basename(f))
        if not m:
            continue
        mgr = m.group(1)
        recs = parse_full_mas_log(f)
        graded = 0
        for r in recs:
            try:
                g = int(r["original_grade"])
            except Exception:
                continue
            by_payload[r["payload_id"]][mgr] = g
            graded += 1
        if graded:
            managers.append(mgr)
    managers = sorted(set(managers))
    print(f"managers parsed: {len(managers)}  | payloads with grades: {len(by_payload)}")
    print(f"managers: {managers}")

    # per-payload success profile
    rows = []
    for pid, gd in by_payload.items():
        meta = data.get(pid, {})
        n = len(gd)
        succ = sum(1 for g in gd.values() if g >= 2)
        payload = meta.get("payload", "")
        rows.append({
            "pid": pid, "strategy": meta.get("strategy", "?"), "target_tool": meta.get("target_tool", "?"),
            "source_company": meta.get("source_company", "?"),
            "n_mgr": n, "succ": succ, "succ_rate": succ / n if n else 0.0,
            "pay_lex": certainty_core.lexicon_certainty(payload),
            "pay_embed": certainty_core.embed_certainty(payload),
            "pay_len": len(payload.split()),
        })

    def grp(field):
        agg = defaultdict(lambda: [0, 0])      # key -> [succ, total] over payload x manager
        for r in rows:
            agg[r[field]][0] += r["succ"]; agg[r[field]][1] += r["n_mgr"]
        return sorted(((k, asr_of(s, t), t) for k, (s, t) in agg.items()), key=lambda x: -x[1])

    print("\n=== ASR by STRATEGY (over payload x manager) ===")
    for k, a, t in grp("strategy"):
        print(f"  {k:28s} ASR={a:5.1f}%  (n={t})")
    print("\n=== ASR by TARGET_TOOL ===")
    for k, a, t in grp("target_tool"):
        print(f"  {k:32s} ASR={a:5.1f}%  (n={t})")

    # strategy x tool cells
    cell = defaultdict(lambda: [0, 0])
    for r in rows:
        cell[(r["strategy"], r["target_tool"])][0] += r["succ"]
        cell[(r["strategy"], r["target_tool"])][1] += r["n_mgr"]
    cells = sorted(((k, asr_of(s, t), t) for k, (s, t) in cell.items() if t >= 30), key=lambda x: -x[1])
    print("\n=== ASR by STRATEGY x TARGET_TOOL (cells n>=30) — top & bottom 6 ===")
    for k, a, t in cells[:6]:
        print(f"  HI  {k[0]:24s} x {k[1]:30s} ASR={a:5.1f}% (n={t})")
    for k, a, t in cells[-6:]:
        print(f"  LO  {k[0]:24s} x {k[1]:30s} ASR={a:5.1f}% (n={t})")

    # payload-text features vs success_rate (Spearman, payload-level)
    sr = [r["succ_rate"] for r in rows]
    def sp(key):
        xs = [r[key] for r in rows]
        if len(set(xs)) < 2:
            return (0.0, 1.0)
        rho, p = stats.spearmanr(xs, sr); return (float(rho), float(p))
    print("\n=== payload-text feature vs cross-manager success_rate (Spearman, n payloads) ===")
    for key in ("pay_lex", "pay_embed", "pay_len"):
        rho, p = sp(key); print(f"  {key:10s} rho={rho:+.3f}  p={p:.3g}")

    # universally-strong vs universally-weak payloads
    rows.sort(key=lambda r: -r["succ_rate"])
    print("\n=== most UNIVERSALLY successful payloads (top 8 by succ_rate) ===")
    for r in rows[:8]:
        print(f"  pid={r['pid']:>3} sr={r['succ_rate']:.2f} {r['strategy']:22s} {r['target_tool']:28s} "
              f"lex={r['pay_lex']:+5.1f}")
    print("=== most ROBUSTLY blocked payloads (bottom 6) ===")
    for r in rows[-6:]:
        print(f"  pid={r['pid']:>3} sr={r['succ_rate']:.2f} {r['strategy']:22s} {r['target_tool']:28s} "
              f"lex={r['pay_lex']:+5.1f}")

    json.dump({"managers": managers, "n_payloads": len(rows),
               "by_strategy": grp("strategy"), "by_tool": grp("target_tool"),
               "cells": [(f"{k[0]}|{k[1]}", a, t) for k, a, t in cells],
               "rows": rows}, open(OUT, "w"), indent=2)
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
