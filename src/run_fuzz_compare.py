"""Fuzzer ablation v2: NOVELTY-guided (QD) vs ASR-only vs RANDOM, at equal budget, on the supervisor topology.

Primary metric = distinct_failure_modes (behavioral diversity of hijacks: # successful attacks mutually > tau
apart). Secondary = raw_hijacks (count, gamed by ASR-only's clustering), explored (frontier size).

Hypothesis: novelty > asr > random on distinct_failure_modes (even if asr has more raw_hijacks).
Kill-criterion: if novelty does NOT beat asr/random on distinct_failure_modes, the coverage signal is useless.

Usage: python run_fuzz_compare.py --seeds 12 --budget 50 --rigor medium --backend openrouter
"""
from __future__ import annotations
import argparse, json, os, random
import config
from llm_client import LLMClient
from run_manager_rigor import SOPS
import fuzz

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data", "paradox_dataset_500.json")
MODEL = "deepseek/deepseek-chat"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="openrouter", choices=["openrouter", "hf", "mock"])
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--budget", type=int, default=50)
    ap.add_argument("--rigor", default="medium", choices=list(SOPS))
    ap.add_argument("--tau", type=float, default=0.30)
    ap.add_argument("--rngseed", type=int, default=0)
    ap.add_argument("--out", default=os.path.join(HERE, "..", "logs", "fuzz_compare_v2.json"))
    args = ap.parse_args()

    data = json.load(open(DATA, encoding="utf-8"))[: args.seeds]
    base = [fuzz.Seed(payload=a["payload"], target_tool=a["target_tool"],
                      strategy=a.get("strategy", "?"), pid=a.get("id", i)) for i, a in enumerate(data)]
    m = LLMClient(role="agent", backend=args.backend, model=MODEL)
    judge = LLMClient(role="judge", backend=args.backend, model=config.MODELS["judge"])
    sop = SOPS[args.rigor]

    print("=" * 84, flush=True)
    print(f"D5 FUZZER v2 (novelty/QD)  backend={judge.backend}  topology=supervisor  rigor={args.rigor}", flush=True)
    print(f"base_seeds={args.seeds}  budget={args.budget}/mode  tau={args.tau}  ~{3 * args.budget * 2} calls", flush=True)
    print("=" * 84, flush=True)

    results = {}
    for mode in ("novelty", "asr", "random"):
        rng = random.Random(args.rngseed)         # same rng across modes -> fair
        r = fuzz.campaign(m, judge, sop, base, args.budget, mode, rng, tau=args.tau)
        results[mode] = r
        print(f"  [{mode:7s}] distinct_failure_modes={r['distinct_failure_modes']:3d}  "
              f"raw_hijacks={r['raw_hijacks']:3d}  explored={r['explored']:3d}", flush=True)
        json.dump(results, open(args.out, "w"), indent=2)

    print("-" * 84, flush=True)
    nv, a, rd = results["novelty"], results["asr"], results["random"]
    print(f"DISTINCT failure modes : novelty={nv['distinct_failure_modes']}  asr={a['distinct_failure_modes']}  random={rd['distinct_failure_modes']}", flush=True)
    print(f"raw hijacks (secondary): novelty={nv['raw_hijacks']}  asr={a['raw_hijacks']}  random={rd['raw_hijacks']}", flush=True)
    win = nv["distinct_failure_modes"] > max(a["distinct_failure_modes"], rd["distinct_failure_modes"])
    print(f"VERDICT: {'NOVELTY-GUIDED WINS on diversity (coverage signal useful)' if win else 'no diversity gain -> kill-criterion still hit'}", flush=True)
    print("=" * 84, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
