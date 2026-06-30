"""Aggregate multi-seed runs into mean±std tables (Table 2 headline + Table 5 architecture matrix).

Table 2: tab2_s{0,1,2}.json  (run_certainty_llm worker-gated supervisor, arms certainty/neutral/concat).
Table 5: arch_<A>.json (seed0) + arch_<A>_s{1,2}.json  (run_arch_matrix weak homogeneous, 4 arms).
Reports per cell: mean ASR ± std across seeds, and the winner with a stability flag.
"""
from __future__ import annotations
import json, os, glob
from statistics import mean, pstdev

HERE = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(HERE, "..", "logs")


def load(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return None


def cell(arms_results, mode):
    r = arms_results.get(mode)
    return r["asr"] if r else None


def table2():
    arms = ["certainty", "neutral", "concat"]
    seeds = []
    for s in range(0, 7):
        d = load(os.path.join(LOGS, f"tab2_big_s{s}.json")) or load(os.path.join(LOGS, f"tab2_s{s}.json"))
        if d and all(m in d for m in arms):
            seeds.append(d)
    if not seeds:
        print("Table 2: no complete seeds yet"); return
    print(f"\n=== TABLE 2 — certainty-guided vs baselines (worker-gated supervisor, {len(seeds)} seeds) ===")
    print(f"{'arm':12} {'ASR mean±std':16} {'deep mean':10} {'coh mean':9}")
    for m in arms:
        asrs = [cell(d, m) for d in seeds if cell(d, m) is not None]
        deeps = [d[m]["n_deep"] for d in seeds if m in d]
        cohs = [d[m]["mean_coherence"] for d in seeds if m in d]
        print(f"{m:12} {mean(asrs):.2f} ± {pstdev(asrs):.2f}     {mean(deeps):5.1f}      {mean(cohs):.2f}")


def table5():
    archs = ["single", "pipeline", "supervisor", "groupchat", "swarm"]
    arms = ["certainty", "recipe", "neutral", "concat"]
    print(f"\n=== TABLE 5 — architecture × guidance (weak homogeneous), mean ASR ± std ===")
    hdr = f"{'arch':12}" + "".join(f"{a:>16}" for a in arms) + f"{'winner':>12}{'stable':>8}"
    print(hdr)
    for A in archs:
        # combine the 3 clean small-scale seeds (n=36) with the big-scale seed(s) (n=72) for the matrix map.
        files = (sorted(glob.glob(os.path.join(LOGS, f"arch_{A}_s[1-9].json")))
                 + sorted(glob.glob(os.path.join(LOGS, f"arch_{A}_big_s[0-9].json"))))
        seeds = [load(f) for f in files]
        seeds = [d for d in seeds if d]
        if not seeds:
            print(f"{A:12} (no data)"); continue
        row = f"{A:12}"
        per_arm_means = {}
        winners_per_seed = []
        for a in arms:
            vals = [cell(d, a) for d in seeds if cell(d, a) is not None]
            if vals:
                per_arm_means[a] = mean(vals)
                row += f"{mean(vals):.2f}±{pstdev(vals):.2f}".rjust(16)
            else:
                row += "—".rjust(16)
        for d in seeds:
            present = {a: cell(d, a) for a in arms if cell(d, a) is not None}
            if present:
                winners_per_seed.append(max(present, key=present.get))
        winner = max(per_arm_means, key=per_arm_means.get) if per_arm_means else "—"
        stable = "yes" if winners_per_seed and all(w == winners_per_seed[0] for w in winners_per_seed) else "MIXED"
        row += f"{winner:>12}{stable:>8}  (n={len(seeds)}; per-seed {winners_per_seed})"
        print(row)


def strong():
    print(f"\n=== Strong-decider (swarm/groupchat) — seeds available ===")
    for A in ("swarm", "groupchat"):
        files = sorted(glob.glob(os.path.join(LOGS, f"arch_{A}_strong*.json")))
        seeds = [load(f) for f in files]; seeds = [d for d in seeds if d]
        if not seeds:
            print(f"{A}: (no data)"); continue
        for a in ("certainty", "recipe", "neutral", "concat"):
            vals = [cell(d, a) for d in seeds if cell(d, a) is not None]
            if vals:
                print(f"  {A:10} {a:10} ASR {mean(vals):.2f} ± {pstdev(vals):.2f}  (n={len(vals)})")


if __name__ == "__main__":
    table2(); table5(); strong()
