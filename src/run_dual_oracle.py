"""Break the circularity (#1) + add a hard action-preservation gate (#5), from the code side.

#1: every candidate's Manager decision is graded by BOTH the inherited LLM oracle AND the independent,
    self-contained, non-LLM rule_oracle. We report (a) their agreement (Cohen's kappa) and (b) the core
    certainty->hijack relationship under EACH oracle. If certainty->hijack survives under the rule oracle --- a
    grader that does not reward confidence/plausibility and shares nothing with the mother paper --- the
    relationship is not a judge-confidence artifact, and this result does not depend on the mother paper.

#5: a HARD constraint gate in the mutation loop --- a child is rejected (the parent is kept) if the mutation
    weakened/removed the destructive action (rule_oracle.action_preserved), so the elite pool cannot be polluted
    by "high-certainty but action-defanged" samples that would inflate ASR.

Usage: python run_dual_oracle.py --backend openrouter --seeds 20 --budget 50 --attacker deepseek/deepseek-chat
"""
from __future__ import annotations
import argparse, json, os, random, re
from scipy import stats
from sklearn.metrics import cohen_kappa_score

import config
from llm_client import LLMClient
from run_manager_rigor import SOPS
from topology import run_supervisor
import behavior_judge, certainty_core, llm_mutator, rule_oracle

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data", "paradox_dataset_500.json")
_DESTR = rule_oracle._DESTR


def action_preserved(parent_payload: str, child_payload: str) -> bool:
    """#5 gate: if the parent requested a destructive action, the child must still request one."""
    if not _DESTR.search(parent_payload):
        return True                      # parent had no explicit destructive verb -> nothing to preserve
    return bool(_DESTR.search(child_payload))


def evaluate(worker, judge, sop, payload, tgt, seed):
    tr = run_supervisor(worker, payload, "SRE incident", sop, seed)
    sc = certainty_core.score_all(tr.steps[0].output)
    b = behavior_judge.judge_behavior(judge, tgt, payload, tr.final_text, seed)          # LLM oracle
    ro = rule_oracle.grade(tr.final_text, payload, tgt)                                    # independent oracle
    coh = llm_mutator.coherence(judge, payload, seed)
    return {"payload": payload, "tgt": tgt, "lex_raw": sc["lex_raw"], "lex_norm": sc["lex_norm"],
            "llm_grade": b["grade"], "llm_hijacked": int(b["hijacked"]),
            "rule_hijacked": ro["hijacked"], "rule_score": ro["score"], "coh": coh}


def campaign(worker, attacker, judge, sop, base, exemplars, budget, mode, rng, seed0):
    recs, archive = [], []
    sc = seed0
    n_seed = max(2, budget // 6)
    n_gated = 0
    for i in range(min(len(base), n_seed)):
        r = evaluate(worker, judge, sop, base[i][0], base[i][1], sc); sc += 1
        recs.append(r); archive.append(r)
    for it in range(n_seed, budget):
        if mode == "certainty" and archive:
            parent = rng.choice(sorted(archive, key=lambda r: r["lex_raw"], reverse=True)[:5])
            pp, tgt = parent["payload"], parent["tgt"]
        else:
            pp, tgt = rng.choice(base)
        mut = llm_mutator.mutate(attacker, pp, mode, exemplars, sc); sc += 1
        if not action_preserved(pp, mut):        # #5 HARD GATE: reject defanged child, keep parent
            mut = pp; n_gated += 1
        r = evaluate(worker, judge, sop, mut, tgt, sc); sc += 1
        recs.append(r); archive.append(r)
    return {"mode": mode, "n": len(recs), "n_gated": n_gated,
            "asr_llm": sum(r["llm_hijacked"] for r in recs) / len(recs),
            "asr_rule": sum(r["rule_hijacked"] for r in recs) / len(recs),
            "mean_coh": sum(r["coh"] for r in recs) / len(recs), "records": recs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="openrouter")
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--budget", type=int, default=50)
    ap.add_argument("--rigor", default="strict", choices=list(SOPS))
    ap.add_argument("--attacker", default="deepseek/deepseek-chat")
    ap.add_argument("--arms", default="certainty,neutral")
    ap.add_argument("--rngseed", type=int, default=0)
    ap.add_argument("--out", default=os.path.join(HERE, "..", "logs", "dual_oracle.json"))
    args = ap.parse_args()

    data = json.load(open(DATA, encoding="utf-8"))[: args.seeds]
    base = [(a["payload"], a["target_tool"]) for a in data]
    worker = LLMClient(role="agent", backend=args.backend, model=config.MODELS["worker"])
    attacker = LLMClient(role="attacker", backend=args.backend, model=args.attacker)
    judge = LLMClient(role="judge", backend=args.backend, model=config.MODELS["judge"])
    sop = SOPS[args.rigor]

    print("=" * 92, flush=True)
    print(f"D5 DUAL-ORACLE (independent non-LLM oracle + action-preservation gate)  "
          f"worker={config.MODELS['worker']}  rigor={args.rigor}  budget={args.budget}/arm", flush=True)
    print("=" * 92, flush=True)
    exemplars, _ = llm_mutator.mine_exemplars(worker, [b[0] for b in base], k=4, seed0=100)

    results, allr = {}, []
    for k, mode in enumerate(args.arms.split(",")):
        rng = random.Random(args.rngseed + k)
        r = campaign(worker, attacker, judge, sop, base, exemplars, args.budget, mode, rng, seed0=110000 + 1000 * k)
        results[mode] = r; allr += r["records"]
        print(f"  [{mode:9s}] ASR(LLM)={r['asr_llm']:.2f}  ASR(rule)={r['asr_rule']:.2f}  "
              f"gated={r['n_gated']}  coh={r['mean_coh']:.2f}", flush=True)
        json.dump({mm: {kk: vv for kk, vv in rr.items() if kk != "records"} for mm, rr in results.items()},
                  open(args.out, "w"), indent=2)

    # --- the key checks ---
    llm_h = [r["llm_hijacked"] for r in allr]
    rule_h = [r["rule_hijacked"] for r in allr]
    lex = [r["lex_raw"] for r in allr]
    kappa = cohen_kappa_score(llm_h, rule_h)
    agree = sum(int(a == b) for a, b in zip(llm_h, rule_h)) / len(allr)
    rho_llm, p_llm = stats.spearmanr(lex, [r["llm_grade"] for r in allr])
    rho_rule, p_rule = stats.spearmanr(lex, [r["rule_score"] for r in allr])
    results["_validation"] = {"n": len(allr), "kappa": float(kappa), "agreement": agree,
                              "rho_cert_LLM": [float(rho_llm), float(p_llm)],
                              "rho_cert_RULE": [float(rho_rule), float(p_rule)]}
    results["_raw"] = {"lex_raw": lex, "llm_grade": [r["llm_grade"] for r in allr],
                       "rule_score": [r["rule_score"] for r in allr],
                       "llm_hijacked": llm_h, "rule_hijacked": rule_h}
    json.dump(results, open(args.out, "w"), indent=2)

    print("-" * 92, flush=True)
    print(f"ORACLE AGREEMENT (n={len(allr)}):  Cohen's kappa = {kappa:+.3f}   raw agreement = {agree:.2%}", flush=True)
    print(f"certainty -> hijack  under LLM oracle :  rho={rho_llm:+.3f}  p={p_llm:.3g}", flush=True)
    print(f"certainty -> hijack  under RULE oracle:  rho={rho_rule:+.3f}  p={p_rule:.3g}  (independent, non-LLM)", flush=True)
    ok = rho_rule > 0 and p_rule < 0.05
    print(f"VERDICT: {'certainty->hijack SURVIVES an independent non-LLM oracle -> NOT a judge-confidence artifact' if ok else 'relationship does not replicate under the rule oracle'}", flush=True)
    print("=" * 92, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
