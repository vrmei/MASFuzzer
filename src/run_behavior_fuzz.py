"""v6 ablation: DIRECTED output-behavior coverage vs RANDOM, on the supervisor topology.
Metric = distinct_behavior_cells (distinct (affect x certainty x justification) of the Manager's HIJACKED
decisions). Directed = systematically elicit each behavior region; random = chain random ops. Behavior axes
are EMERGENT (judge-quantified), so a directed coverage win is genuine (no by-construction artifact).

Usage: python run_behavior_fuzz.py --seeds 12 --budget 60 --rigor medium --backend openrouter
"""
from __future__ import annotations
import argparse, json, os, random
import config
from llm_client import LLMClient
from run_manager_rigor import SOPS
import fuzz_behavior

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data", "paradox_dataset_500.json")
MODEL = "deepseek/deepseek-chat"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="openrouter", choices=["openrouter", "hf", "mock"])
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--budget", type=int, default=60)
    ap.add_argument("--rigor", default="medium", choices=list(SOPS))
    ap.add_argument("--rngseed", type=int, default=0)
    ap.add_argument("--out", default=os.path.join(HERE, "..", "logs", "behavior_fuzz.json"))
    args = ap.parse_args()

    data = json.load(open(DATA, encoding="utf-8"))[: args.seeds]
    base = [fuzz_behavior.Seed(payload=a["payload"], target_tool=a["target_tool"], pid=a.get("id", i))
            for i, a in enumerate(data)]
    m = LLMClient(role="agent", backend=args.backend, model=MODEL)
    judge = LLMClient(role="judge", backend=args.backend, model=config.MODELS["judge"])
    sop = SOPS[args.rigor]

    print("=" * 84, flush=True)
    print(f"D5 v6 OUTPUT-BEHAVIOR coverage  backend={m.backend}  rigor={args.rigor}  "
          f"seeds={args.seeds}  budget={args.budget}/mode", flush=True)
    print("=" * 84, flush=True)

    results = {}
    for mode in ("directed", "random"):
        rng = random.Random(args.rngseed)
        r = fuzz_behavior.campaign(m, judge, sop, base, args.budget, mode, rng)
        results[mode] = r
        print(f"  [{mode:8s}] distinct_behavior_cells={r['distinct_behavior_cells']:3d}  "
              f"raw_hijacks={r['raw_hijacks']:3d}", flush=True)
        json.dump(results, open(args.out, "w"), indent=2)

    print("-" * 84, flush=True)
    di, rd = results["directed"], results["random"]
    print(f"distinct behavior cells: directed={di['distinct_behavior_cells']}  random={rd['distinct_behavior_cells']}", flush=True)
    print(f"directed cells: {di['cells']}", flush=True)
    win = di["distinct_behavior_cells"] > rd["distinct_behavior_cells"]
    print(f"VERDICT: {'DIRECTED OUTPUT-BEHAVIOR COVERAGE WINS (emergent descriptor, clean coverage gain)' if win else 'no gain -> output-behavior coverage also does not beat random'}", flush=True)
    print("=" * 84, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
