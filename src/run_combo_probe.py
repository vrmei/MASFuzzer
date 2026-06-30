"""Is the hijack lever a COMBINATION, not a single feature?  (zero-deepseek)

For each architecture we record the FULL lexical-feature panel of the upstream text per candidate + the hijack
label, then fit MULTIVARIATE models (cross-validated) and compare to the best single feature:
  - logistic regression (linear combination) CV AUC + standardized coefficients
  - random forest (captures interactions / nonlinearity) CV AUC + feature importances
  - best single-feature univariate AUC
If the combination beats the best single feature, the lever is combinatorial; the coefficients/importances name
the winning combination per architecture.

Usage: python run_combo_probe.py --backend openrouter --seeds 25 --budget 70
"""
from __future__ import annotations
import argparse, json, os, random
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import roc_auc_score

import config
from llm_client import LLMClient
from run_manager_rigor import SOPS
from topology import TOPOLOGIES
import behavior_judge, lexical_features
from mas_ops import Seed as CSeed, ALL_OPS

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data", "paradox_dataset_500.json")
FEATS = lexical_features.FEATURES


def collect(arch, m, judge, sop, base, budget, rng, seed0):
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
        up = " ".join(s.output for s in tr.steps[:-1]) or tr.final_text
        panel = lexical_features.score_panel(up)
        b = behavior_judge.judge_behavior(judge, tgt, payload, tr.final_text, sc); sc += 1
        recs.append({**panel, "hijacked": int(b["hijacked"])})
    return recs


def analyze(recs):
    X = np.array([[r[f] for f in FEATS] for r in recs], float)
    y = np.array([r["hijacked"] for r in recs])
    out = {"n": len(y), "asr": float(y.mean())}
    if y.sum() < 4 or (len(y) - y.sum()) < 4:
        out["note"] = "too few of one class for CV"; return out
    Xs = StandardScaler().fit_transform(X)
    cv = StratifiedKFold(5, shuffle=True, random_state=0)
    # multivariate linear
    lr = LogisticRegression(max_iter=1000, C=1.0)
    out["logit_auc"] = float(np.mean(cross_val_score(lr, Xs, y, cv=cv, scoring="roc_auc")))
    lr.fit(Xs, y)
    out["logit_coef"] = {f: round(float(c), 3) for f, c in zip(FEATS, lr.coef_[0])}
    # nonlinear / interactions
    rf = RandomForestClassifier(n_estimators=300, max_depth=4, random_state=0)
    out["rf_auc"] = float(np.mean(cross_val_score(rf, X, y, cv=cv, scoring="roc_auc")))
    rf.fit(X, y)
    out["rf_importance"] = {f: round(float(i), 3) for f, i in zip(FEATS, rf.feature_importances_)}
    # best single feature (univariate CV AUC, sign-corrected)
    best, bestauc = None, 0.0
    for j, f in enumerate(FEATS):
        a = roc_auc_score(y, Xs[:, j])
        a = max(a, 1 - a)
        if a > bestauc:
            bestauc, best = a, f
    out["best_single"] = best
    out["best_single_auc"] = round(float(bestauc), 3)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="openrouter")
    ap.add_argument("--seeds", type=int, default=25)
    ap.add_argument("--budget", type=int, default=70)
    ap.add_argument("--rigor", default="strict", choices=list(SOPS))
    ap.add_argument("--archs", default="supervisor,pipeline,swarm,swarm_audited,groupchat,single")
    ap.add_argument("--rngseed", type=int, default=0)
    ap.add_argument("--out", default=os.path.join(HERE, "..", "logs", "combo_probe.json"))
    args = ap.parse_args()

    data = json.load(open(DATA, encoding="utf-8"))[: args.seeds]
    base = [(a["payload"], a["target_tool"]) for a in data]
    m = LLMClient(role="agent", backend=args.backend, model=config.MODELS["worker"])
    judge = LLMClient(role="judge", backend=args.backend, model=config.MODELS["judge"])
    sop = SOPS[args.rigor]

    print("=" * 96, flush=True)
    print(f"D5 COMBO-PROBE  is the lever combinatorial?  model={config.MODELS['worker']}  budget={args.budget}/arch", flush=True)
    print("=" * 96, flush=True)
    results = {}
    for k, arch in enumerate(args.archs.split(",")):
        rng = random.Random(args.rngseed + k)
        recs = collect(arch, m, judge, sop, base, args.budget, rng, seed0=80000 + 1000 * k)
        a = analyze(recs)
        results[arch] = a
        if "logit_auc" in a:
            gain = a["logit_auc"] - a["best_single_auc"]
            rfgain = a["rf_auc"] - a["best_single_auc"]
            top = sorted(a["logit_coef"].items(), key=lambda x: -abs(x[1]))[:3]
            rftop = sorted(a["rf_importance"].items(), key=lambda x: -x[1])[:3]
            print(f"\n[{arch}] ASR={a['asr']:.2f} n={a['n']}", flush=True)
            print(f"   best-single={a['best_single']} AUC={a['best_single_auc']:.3f} | "
                  f"logit-COMBO AUC={a['logit_auc']:.3f} (Δ{gain:+.3f}) | RF AUC={a['rf_auc']:.3f} (Δ{rfgain:+.3f})", flush=True)
            print(f"   logit top: {', '.join(f'{f}={c:+.2f}' for f,c in top)}", flush=True)
            print(f"   RF   top: {', '.join(f'{f}={i:.2f}' for f,i in rftop)}", flush=True)
        else:
            print(f"\n[{arch}] ASR={a['asr']:.2f} n={a['n']} — {a.get('note','')}", flush=True)
        json.dump(results, open(args.out, "w"), indent=2)
    print("\n" + "=" * 96, flush=True)
    print("Combinatorial if COMBO AUC (logit/RF) > best-single AUC; the top coefs/importances name the combo.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
