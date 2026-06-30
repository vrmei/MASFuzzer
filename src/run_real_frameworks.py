"""Real-framework evaluation: run the certainty-guided fuzzer against a supervisor MAS built in a REAL
framework (LangGraph / AutoGen / CrewAI) instead of the abstracted topology.py.

The attacker LLM, certainty fitness, behavior judge, and the independent rule oracle all stay in the main env
(validated code); only the auditor->decider orchestration is delegated, over a subprocess bridge, to the real
framework's engine. WIN = the certainty->hijack mechanism (dose-response rho>0, certainty arm ASR>neutral)
reproduces on the real framework, under BOTH the LLM oracle and the independent non-LLM oracle.

Usage: python run_real_frameworks.py --fw langgraph --seeds 7 --budget 20
"""
from __future__ import annotations
import argparse, json, os, random
from scipy import stats
try:
    from sklearn.metrics import cohen_kappa_score
except Exception:
    cohen_kappa_score = None

import config
from llm_client import LLMClient
from run_manager_rigor import SOPS
from run_mas_vs_single import SOP_WORKER_FULL
import behavior_judge, certainty_core, llm_mutator, rule_oracle
from real_bridge import FrameworkBridge

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data", "paradox_dataset_500.json")
ELITE_K, WARMSTART_DIV = 5, 6


def evaluate(bridge, judge, sop_unused, payload, target_tool, ctx, seed):
    for attempt in range(3):
        r = bridge.run(payload, ctx, seed + attempt)
        if not r.get("error") and (r.get("audit") or r.get("decision")):
            break
    audit = r.get("audit", "") or ""
    decision = r.get("decision", "") or ""
    sc = certainty_core.score_all(audit)
    b = behavior_judge.judge_behavior(judge, target_tool, payload, decision, seed)
    ro = rule_oracle.grade(decision, payload, target_tool)
    return {"payload": payload, "target_tool": target_tool, "lex_raw": sc["lex_raw"],
            "lex_norm": sc["lex_norm"], "embed": sc["embed"], "grade": b["grade"], "hijacked": b["hijacked"],
            "rule_score": ro["score"], "rule_hijacked": ro["hijacked"], "err": bool(r.get("error"))}


def campaign(bridge, attacker, judge, base, exemplars, budget, mode, ctx, rng, seed0):
    recs, archive = [], []
    sc = seed0
    n_seed = min(len(base), max(2, budget // WARMSTART_DIV))
    for i in range(n_seed):
        recs.append(evaluate(bridge, judge, None, base[i][0], base[i][1], ctx, sc)); sc += 1
        archive.append(recs[-1])
    for it in range(n_seed, budget):
        if mode == "certainty" and archive:
            parent = rng.choice(sorted(archive, key=lambda r: r["lex_raw"], reverse=True)[:ELITE_K])
            pp, tgt = parent["payload"], parent["target_tool"]
        else:
            pp, tgt = rng.choice(base)
        mut = llm_mutator.mutate(attacker, pp, mode, exemplars, sc); sc += 1
        recs.append(evaluate(bridge, judge, None, mut, tgt, ctx, sc)); sc += 1
        archive.append(recs[-1])
    lex = [r["lex_raw"] for r in recs]
    return {"mode": mode, "n": len(recs), "mean_lex": sum(lex) / len(lex), "max_lex": max(lex),
            "asr_llm": sum(r["hijacked"] for r in recs) / len(recs),
            "asr_rule": sum(r["rule_hijacked"] for r in recs) / len(recs),
            "n_err": sum(r["err"] for r in recs), "records": recs}


def _spear(xs, ys):
    if len(set(xs)) < 2 or len(set(ys)) < 2:
        return 0.0, 1.0
    rho, p = stats.spearmanr(xs, ys); return float(rho), float(p)


def cluster_bootstrap_rho(recs, xkey, ykey, n_boot=2000, rng_seed=0):
    """95% CI for Spearman rho, resampling whole reps (clusters) with replacement -> robust to within-rep
    dependence (reviewer stats concern). Returns (lo, hi, point)."""
    import collections
    by_rep = collections.defaultdict(list)
    for r in recs:
        by_rep[r.get("rep", 0)].append(r)
    reps = list(by_rep)
    rng = random.Random(rng_seed)
    point = _spear([r[xkey] for r in recs], [r[ykey] for r in recs])[0]
    if len(reps) < 2:
        return (None, None, point)
    boots = []
    for _ in range(n_boot):
        samp = []
        for _ in reps:
            samp += by_rep[reps[rng.randrange(len(reps))]]
        rho = _spear([r[xkey] for r in samp], [r[ykey] for r in samp])[0]
        boots.append(rho)
    boots.sort()
    return (boots[int(0.025 * n_boot)], boots[int(0.975 * n_boot)], point)


def dose(records, key, nb=5):
    bins = [[] for _ in range(nb)]
    for r in records:
        bins[min(nb - 1, int(r["lex_norm"] * nb))].append(r[key])
    return [{"bin": f"[{i/nb:.1f},{(i+1)/nb:.1f})", "n": len(b), "asr": (sum(b)/len(b)) if b else None}
            for i, b in enumerate(bins)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fw", required=True, choices=["langgraph", "autogen", "crewai"])
    ap.add_argument("--seeds", type=int, default=7)
    ap.add_argument("--reps", type=int, default=7, help="independent statistical seeds (clusters)")
    ap.add_argument("--budget", type=int, default=25)
    ap.add_argument("--arms", default="certainty,neutral")
    ap.add_argument("--aud-model", default="meta-llama/llama-3.2-3b-instruct")
    ap.add_argument("--dec-model", default="deepseek/deepseek-chat")
    ap.add_argument("--attacker", default="deepseek/deepseek-chat")
    ap.add_argument("--ctx", default="SRE incident")
    ap.add_argument("--data", default=DATA)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    out = args.out or os.path.join(HERE, "..", "logs", "real", f"{args.fw}_real.json")
    data = json.load(open(args.data, encoding="utf-8"))[: args.seeds]
    base = [(a["payload"], a["target_tool"]) for a in data]
    attacker = LLMClient(role="attacker", backend="openrouter", model=args.attacker)
    judge = LLMClient(role="judge", backend="openrouter", model=config.MODELS["judge"])
    # exemplars mined with the same weak auditor model (few-shot seeds for the attacker)
    aud_main = LLMClient(role="agent", backend="openrouter", model=args.aud_model)
    exemplars, scored = llm_mutator.mine_exemplars(aud_main, [b[0] for b in base], k=4, seed0=100)

    print("=" * 90, flush=True)
    print(f"D5 REAL-FRAMEWORK fuzzer  fw={args.fw}  auditor={args.aud_model}  decider={args.dec_model}  "
          f"attacker={args.attacker}  seeds={args.seeds}  budget={args.budget}/arm", flush=True)
    print(f"mined {len(exemplars)} exemplars (top lex={scored[0][0]:.1f}..{scored[-1][0]:.1f})", flush=True)
    print("=" * 90, flush=True)

    bridge = FrameworkBridge(args.fw, args.aud_model, args.dec_model, SOP_WORKER_FULL, SOPS["strict"])
    arms = args.arms.split(",")
    all_recs = []
    per_rep = []          # [{rep, certainty:{asr_llm,asr_rule,mean_lex}, neutral:{...}}]
    try:
        for rep in range(args.reps):
            rep_row = {"rep": rep}
            for k, mode in enumerate(arms):
                rng = random.Random(1000 * rep + k)
                r = campaign(bridge, attacker, judge, base, exemplars, args.budget, mode, args.ctx, rng,
                             seed0=30000 + 5000 * rep + 1000 * k)
                for rec in r["records"]:
                    rec["rep"] = rep; rec["arm"] = mode
                all_recs += r["records"]
                rep_row[mode] = {"asr_llm": r["asr_llm"], "asr_rule": r["asr_rule"], "mean_lex": r["mean_lex"],
                                 "n_err": r["n_err"]}
                print(f"  rep{rep} [{mode:9s}] mean_lex={r['mean_lex']:6.2f}  ASR_llm={r['asr_llm']:.2f}  "
                      f"ASR_rule={r['asr_rule']:.2f}  err={r['n_err']}", flush=True)
            per_rep.append(rep_row)
            json.dump({"per_rep": per_rep, "records": all_recs}, open(out, "w"), indent=2)
    finally:
        bridge.close()

    lex = [r["lex_raw"] for r in all_recs]
    grd = [r["grade"] for r in all_recs]; rsc = [r["rule_score"] for r in all_recs]
    lh = [r["hijacked"] for r in all_recs]; rh = [r["rule_hijacked"] for r in all_recs]
    rho_l, p_l = _spear(lex, grd); rho_r, p_r = _spear(lex, rsc)
    lo_l, hi_l, _ = cluster_bootstrap_rho(all_recs, "lex_raw", "grade")
    lo_r, hi_r, _ = cluster_bootstrap_rho(all_recs, "lex_raw", "rule_score")
    kappa = float(cohen_kappa_score(lh, rh)) if cohen_kappa_score and len(set(lh)) > 1 and len(set(rh)) > 1 else None

    def arm_stats(arm):
        v_llm = [row[arm]["asr_llm"] for row in per_rep]; v_rule = [row[arm]["asr_rule"] for row in per_rep]
        import statistics as st
        return {"asr_llm_mean": st.mean(v_llm), "asr_llm_sd": st.pstdev(v_llm),
                "asr_rule_mean": st.mean(v_rule), "asr_rule_sd": st.pstdev(v_rule)}
    arm_summ = {a: arm_stats(a) for a in arms}

    pooled = {"n": len(all_recs), "reps": args.reps, "rho_cert_llmgrade": [rho_l, p_l], "ci_llm": [lo_l, hi_l],
              "rho_cert_rulescore": [rho_r, p_r], "ci_rule": [lo_r, hi_r], "kappa_llm_rule": kappa,
              "dose_llm": dose(all_recs, "hijacked"), "dose_rule": dose(all_recs, "rule_hijacked"),
              "arm_summary": arm_summ,
              "raw": {"lex_raw": lex, "llm_grade": grd, "rule_score": rsc, "llm_hijacked": lh, "rule_hijacked": rh}}
    json.dump({"per_rep": per_rep, "pooled": pooled, "records": all_recs}, open(out, "w"), indent=2)

    print("-" * 90, flush=True)
    print(f"POOLED (n={len(all_recs)}, reps={args.reps}) on REAL {args.fw}:", flush=True)
    print(f"  rho(certainty, LLM grade)  = {rho_l:+.3f}  p={p_l:.3g}  95%CI[{lo_l},{hi_l}]", flush=True)
    print(f"  rho(certainty, rule score) = {rho_r:+.3f}  p={p_r:.3g}  95%CI[{lo_r},{hi_r}]  (independent oracle)", flush=True)
    print(f"  oracle agreement kappa     = {kappa}", flush=True)
    for d in pooled["dose_llm"]:
        bar = "#" * int((d["asr"] or 0) * 36)
        print(f"   {d['bin']}  n={d['n']:3d}  ASR_llm={('%.2f'%d['asr']) if d['asr'] is not None else ' NA '}  {bar}",
              flush=True)
    if "certainty" in arm_summ and "neutral" in arm_summ:
        c, n = arm_summ["certainty"], arm_summ["neutral"]
        print(f"  ASR_llm  certainty {c['asr_llm_mean']:.2f}±{c['asr_llm_sd']:.2f}  vs  "
              f"neutral {n['asr_llm_mean']:.2f}±{n['asr_llm_sd']:.2f}", flush=True)
        print(f"  ASR_rule certainty {c['asr_rule_mean']:.2f}±{c['asr_rule_sd']:.2f}  vs  "
              f"neutral {n['asr_rule_mean']:.2f}±{n['asr_rule_sd']:.2f}", flush=True)
    print("=" * 90, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
