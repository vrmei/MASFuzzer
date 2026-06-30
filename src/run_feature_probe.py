"""Per-architecture linguistic-LEVER discovery (zero deepseek load).

For each topology, generate diverse candidates by chaining hand-coded operators (FREE — no attacker LLM), run
the topology (llama agents), score the lexical-feature PANEL on the upstream agent text, grade the decision,
and compute Spearman rho(feature, grade) PER ARCHITECTURE. The feature with the strongest rho is that
topology's candidate hijack lever. Goal: turn 'certainty only generalizes to supervisor' into a per-architecture
mechanism MAP (different topologies, different lexical levers).

Usage: python run_feature_probe.py --backend openrouter --seeds 25 --budget 50
"""
from __future__ import annotations
import argparse, json, os, random
from scipy import stats

import config
from llm_client import LLMClient
from run_manager_rigor import SOPS
from topology import TOPOLOGIES
import behavior_judge, lexical_features
from mas_ops import Seed as CSeed, ALL_OPS

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data", "paradox_dataset_500.json")
ARCHS = ["single", "pipeline", "supervisor", "groupchat", "swarm"]


def upstream_text(tr):
    up = " ".join(s.output for s in tr.steps[:-1])
    return up if up.strip() else tr.final_text     # single agent: no upstream -> use its own output


def probe_arch(arch, m, judge, sop, base, budget, rng, seed0):
    fn = TOPOLOGIES[arch]
    recs = []
    sc = seed0
    for it in range(budget):
        pp, tgt = rng.choice(base)
        cs = CSeed(payload=pp, target_tool=tgt, pid=0)
        for _ in range(rng.randint(0, 3)):
            cs = rng.choice(ALL_OPS)(cs)
        payload = cs.payload + ("\n" + cs.inject if cs.inject else "")
        tr = fn(m, payload, "SRE incident", sop, sc); sc += 1
        feats = lexical_features.score_panel(upstream_text(tr))
        b = behavior_judge.judge_behavior(judge, tgt, payload, tr.final_text, sc); sc += 1
        recs.append({**feats, "grade": b["grade"], "hijacked": int(b["hijacked"])})
    # per-feature Spearman rho with grade
    out = {}
    grades = [r["grade"] for r in recs]
    for f in lexical_features.FEATURES:
        xs = [r[f] for r in recs]
        if len(set(xs)) < 2 or len(set(grades)) < 2:
            out[f] = (0.0, 1.0)
        else:
            rho, p = stats.spearmanr(xs, grades); out[f] = (float(rho), float(p))
    asr = sum(r["hijacked"] for r in recs) / len(recs)
    return {"arch": arch, "n": len(recs), "asr": asr, "rho": out, "records": recs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="openrouter", choices=["openrouter", "hf", "mock"])
    ap.add_argument("--seeds", type=int, default=25)
    ap.add_argument("--budget", type=int, default=50)
    ap.add_argument("--rigor", default="strict", choices=list(SOPS))
    ap.add_argument("--archs", default=",".join(ARCHS))
    ap.add_argument("--rngseed", type=int, default=0)
    ap.add_argument("--out", default=os.path.join(HERE, "..", "logs", "feature_probe.json"))
    args = ap.parse_args()

    data = json.load(open(DATA, encoding="utf-8"))[: args.seeds]
    base = [(a["payload"], a["target_tool"]) for a in data]
    m = LLMClient(role="agent", backend=args.backend, model=config.MODELS["worker"])
    judge = LLMClient(role="judge", backend=args.backend, model=config.MODELS["judge"])
    sop = SOPS[args.rigor]

    print("=" * 96, flush=True)
    print(f"D5 FEATURE-PROBE  per-architecture lexical lever  model={config.MODELS['worker']}  "
          f"rigor={args.rigor}  budget={args.budget}/arch  (zero-deepseek)", flush=True)
    print("=" * 96, flush=True)
    feats = lexical_features.FEATURES
    print(f"{'arch':11} {'ASR':>5}  " + "  ".join(f"{f[:8]:>8}" for f in feats) + "   TOP-lever", flush=True)
    print("-" * 96, flush=True)

    results = {}
    for k, arch in enumerate(args.archs.split(",")):
        rng = random.Random(args.rngseed + k)
        r = probe_arch(arch, m, judge, sop, base, args.budget, rng, seed0=40000 + 1000 * k)
        results[arch] = r
        cells = []
        for f in feats:
            rho, p = r["rho"][f]
            star = "*" if p < 0.05 else " "
            cells.append(f"{rho:+.2f}{star}".rjust(8))
        top = max(feats, key=lambda f: r["rho"][f][0])
        trho, tp = r["rho"][top]
        print(f"{arch:11} {r['asr']:.2f}  " + "  ".join(cells) +
              f"   {top}({trho:+.2f}{'*' if tp<0.05 else ''})", flush=True)
        json.dump({a: {"arch": rr["arch"], "n": rr["n"], "asr": rr["asr"], "rho": rr["rho"]}
                   for a, rr in results.items()}, open(args.out, "w"), indent=2)

    print("-" * 96, flush=True)
    print("Reading: per row, the feature with the largest +rho is that architecture's candidate lexical lever.", flush=True)
    print("'*' = p<0.05. certainty should top supervisor; watch which feature tops the OTHER topologies.", flush=True)
    print("=" * 96, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
