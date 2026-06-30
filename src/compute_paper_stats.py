"""Rigorous statistics for the paper (addresses reviewer points 2): paired CI on the headline, cluster-robust
dose-response (kills pseudoreplication), and multiple-comparison correction of the mechanism levers.
All from existing logs — zero new API. Prints numbers to paste into the paper + writes logs/paper_stats.json.
"""
from __future__ import annotations
import json, os
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.genmod.generalized_estimating_equations import GEE
from statsmodels.genmod.cov_struct import Exchangeable
from statsmodels.genmod.families import Binomial
from statsmodels.stats.multitest import multipletests

HERE = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(HERE, "..", "logs")
rng = np.random.default_rng(0)


def load_seed(s):
    return json.load(open(os.path.join(LOGS, f"tab2_big_s{s}.json"), encoding="utf-8"))


# ── 1. HEADLINE: certainty vs neutral, seed as the experimental unit + cluster bootstrap ────────────────
def headline():
    seeds = [load_seed(s) for s in (0, 1, 2)]
    per_seed = {a: [np.mean([r["hijacked"] for r in d[a]["records"]]) for d in seeds]
                for a in ("certainty", "neutral", "concat")}
    diff = np.array(per_seed["certainty"]) - np.array(per_seed["neutral"])
    # paired t over 3 seed-level ASRs (weak, n=3) — reported honestly
    t, p_t = stats.ttest_rel(per_seed["certainty"], per_seed["neutral"])
    # cluster bootstrap: resample candidates WITHIN each (seed,arm), recompute per-seed diff, average
    B = 20000
    boot = np.empty(B)
    cert = [[r["hijacked"] for r in d["certainty"]["records"]] for d in seeds]
    neut = [[r["hijacked"] for r in d["neutral"]["records"]] for d in seeds]
    for b in range(B):
        ds = []
        for c, n in zip(cert, neut):
            cc = rng.choice(c, len(c), replace=True).mean()
            nn = rng.choice(n, len(n), replace=True).mean()
            ds.append(cc - nn)
        boot[b] = np.mean(ds)
    ci = (float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)))
    return {"per_seed_certainty": per_seed["certainty"], "per_seed_neutral": per_seed["neutral"],
            "per_seed_concat": per_seed["concat"],
            "mean_diff": float(diff.mean()), "paired_t": float(t), "paired_p_n3": float(p_t),
            "bootstrap95_diff": ci, "ci_excludes_0": ci[0] > 0}


# ── 2. DOSE-RESPONSE: per-seed Spearman (independent campaigns) + GEE cluster-robust (vs naive pooled) ───
def dose():
    seeds = [load_seed(s) for s in (0, 1, 2)]
    arms = ("certainty", "neutral", "concat")
    per_seed_rho = []
    rows = []  # (hijacked, lex_norm, cluster=seed*arm)
    allx, ally = [], []
    for si, d in enumerate(seeds):
        xs = [r["lex_raw"] for a in arms for r in d[a]["records"]]
        ys = [r["grade"] for a in arms for r in d[a]["records"]]
        rho, p = stats.spearmanr(xs, ys)
        per_seed_rho.append((float(rho), float(p)))
        for ai, a in enumerate(arms):
            for r in d[a]["records"]:
                rows.append((r["hijacked"], r["lex_norm"], si * 10 + ai))
        allx += xs; ally += ys
    naive_rho, naive_p = stats.spearmanr(allx, ally)
    # GEE logistic, cluster = seed*arm (9 clusters) -> cluster-robust SE on lex_norm
    y = np.array([r[0] for r in rows]); x = np.array([r[1] for r in rows]); g = np.array([r[2] for r in rows])
    X = sm.add_constant(x)
    res = GEE(y, X, groups=g, family=Binomial(), cov_struct=Exchangeable()).fit()
    coef = float(res.params[1]); robust_p = float(res.pvalues[1]); robust_se = float(res.bse[1])
    rhos = [r for r, _ in per_seed_rho]
    return {"naive_pooled_rho": float(naive_rho), "naive_pooled_p": float(naive_p),
            "per_seed_rho": per_seed_rho, "per_seed_rho_mean": float(np.mean(rhos)),
            "per_seed_rho_range": [float(min(rhos)), float(max(rhos))],
            "gee_lexnorm_coef": coef, "gee_robust_se": robust_se, "gee_robust_p": robust_p,
            "n_clusters": int(len(set(g))), "n_obs": int(len(y))}


# ── 3. MULTIPLE-COMPARISON CORRECTION of the mechanism levers ───────────────────────────────────────────
def corrections():
    # (name, raw p) — the per-architecture lever + causal tests reported in Sec 5
    levers = [
        ("supervisor: certainty",        0.00028),   # feature_probe
        ("pipeline: certainty",          0.0108),     # feature_probe
        ("swarm: triage_endorse",        0.00107),    # structural_probe
        ("swarm: handoff_endorse",       0.00302),    # structural_probe
        ("groupchat: endorse_balance",   0.0289),     # structural_gc_medium
        ("swarm_audited: auditor_cert (causal)", 0.00822),  # audited_cert
        ("swarm endorse-steer (causal)", 0.001),      # endorse_steer_crit pooled
    ]
    names = [n for n, _ in levers]; praw = [p for _, p in levers]
    rej_holm, p_holm, _, _ = multipletests(praw, alpha=0.05, method="holm")
    rej_bonf, p_bonf, _, _ = multipletests(praw, alpha=0.05, method="bonferroni")
    out = []
    for n, pr, ph, rh, pb in zip(names, praw, p_holm, rej_holm, p_bonf):
        out.append({"lever": n, "p_raw": pr, "p_holm": float(ph), "holm_sig": bool(rh),
                    "p_bonf": float(pb)})
    return out


if __name__ == "__main__":
    res = {"headline": headline(), "dose": dose(), "corrections": corrections()}
    json.dump(res, open(os.path.join(LOGS, "paper_stats.json"), "w"), indent=2)

    h = res["headline"]
    print("=" * 78)
    print("HEADLINE  certainty vs neutral (seed = unit, n=3 seeds, 72 cand/arm/seed)")
    print(f"  per-seed certainty ASR: {[round(x,3) for x in h['per_seed_certainty']]}")
    print(f"  per-seed neutral   ASR: {[round(x,3) for x in h['per_seed_neutral']]}")
    print(f"  mean diff = {h['mean_diff']:+.3f}   paired-t p (n=3) = {h['paired_p_n3']:.4f}")
    print(f"  cluster-bootstrap 95% CI of diff = [{h['bootstrap95_diff'][0]:+.3f}, {h['bootstrap95_diff'][1]:+.3f}]"
          f"  -> excludes 0: {h['ci_excludes_0']}")
    d = res["dose"]
    print("-" * 78)
    print("DOSE-RESPONSE  (pseudoreplication-corrected)")
    print(f"  NAIVE pooled Spearman rho={d['naive_pooled_rho']:+.3f}  p={d['naive_pooled_p']:.2e}  (INFLATED)")
    print(f"  per-seed rho (3 independent campaigns): {[ (round(r,3),round(p,4)) for r,p in d['per_seed_rho'] ]}")
    print(f"  per-seed rho mean={d['per_seed_rho_mean']:+.3f}  range={[round(x,3) for x in d['per_seed_rho_range']]}")
    print(f"  GEE cluster-robust (clusters={d['n_clusters']}, n={d['n_obs']}): coef(lex_norm)={d['gee_lexnorm_coef']:+.2f}"
          f"  robust p={d['gee_robust_p']:.3g}")
    print("-" * 78)
    print("MULTIPLE-COMPARISON CORRECTION (Holm & Bonferroni over 7 lever p-values)")
    for c in res["corrections"]:
        print(f"  {c['lever']:42s} p={c['p_raw']:.4f}  Holm={c['p_holm']:.4f} {'SIG' if c['holm_sig'] else 'n.s.'}"
              f"  Bonf={c['p_bonf']:.4f}")
    print("=" * 78)
