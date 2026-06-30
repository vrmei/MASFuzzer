"""Decisive coverage ablation in the LARGE/SPARSE regime: cascading-hallucination fuzzing.
novelty (exploring MAP-Elites) vs asr (greedy) vs random, equal budget, on the 3-agent cascade target.

Primary metric = deep_cells (distinct name-class x origin at propagation depth>=2 — the sparse, hard,
coordinated multi-hop failures). Secondary = distinct_cells (depth>=1), raw counts.

Hypothesis (where coverage SHOULD win): novelty reaches more deep_cells than asr > random, because deep
cascades need a coordinated multi-step attack that corpus-building search assembles and one-shot sampling misses.

Usage: python run_cascade_fuzz.py --seeds 10 --budget 70 --backend openrouter
"""
from __future__ import annotations
import argparse, json, os, random
import config
from llm_client import LLMClient
import fuzz_cascade

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data", "paradox_dataset_500.json")
MODEL = "deepseek/deepseek-chat"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="openrouter", choices=["openrouter", "hf", "mock"])
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--budget", type=int, default=70)
    ap.add_argument("--rngseed", type=int, default=0)
    ap.add_argument("--out", default=os.path.join(HERE, "..", "logs", "cascade_fuzz.json"))
    args = ap.parse_args()

    raw = json.load(open(DATA, encoding="utf-8"))
    # distinct incident tasks as base seeds
    seen, base = set(), []
    for i, a in enumerate(raw):
        inc = a.get("source_incident", "").strip()
        if inc and inc not in seen:
            seen.add(inc)
            base.append(fuzz_cascade.Seed(task=inc, pid=a.get("id", i)))
        if len(base) >= args.seeds:
            break

    m = LLMClient(role="agent", backend=args.backend, model=MODEL)
    print("=" * 86, flush=True)
    print(f"D5 CASCADE FUZZER  backend={m.backend}  target=3-agent chain  base_seeds={len(base)}  "
          f"budget={args.budget}/mode  ~{3 * args.budget * 3} calls", flush=True)
    print("=" * 86, flush=True)

    results = {}
    for mode in ("directed", "novelty", "random"):
        rng = random.Random(args.rngseed)
        r = fuzz_cascade.campaign(m, base, args.budget, mode, rng)
        results[mode] = r
        print(f"  [{mode:8s}] deep_cells={r['deep_cells']:3d}  distinct_cells={r['distinct_cells']:3d}  "
              f"raw_deep={r['raw_deep']:3d}  raw_cascades={r['raw_cascades']:3d}", flush=True)
        json.dump(results, open(args.out, "w"), indent=2)

    print("-" * 86, flush=True)
    di, nv, rd = results["directed"], results["novelty"], results["random"]
    print(f"DEEP cascade cells (depth>=2): directed={di['deep_cells']}  novelty={nv['deep_cells']}  random={rd['deep_cells']}", flush=True)
    print(f"distinct cells (depth>=1)    : directed={di['distinct_cells']}  novelty={nv['distinct_cells']}  random={rd['distinct_cells']}", flush=True)
    win = di["distinct_cells"] > max(nv["distinct_cells"], rd["distinct_cells"])
    print(f"VERDICT: {'DIRECTED COVERAGE WINS (coverage-guidance done right beats sampling)' if win else 'directed coverage still does not beat random -> robust honest negative'}", flush=True)
    print("=" * 86, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
