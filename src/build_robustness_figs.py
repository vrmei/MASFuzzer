"""Figures that reflect the cross-model, cross-domain, and independent-oracle results.

fig_dose_multi.png : certainty->hijack dose-response overlaid for THREE settings (SRE/Llama, SRE/Qwen-7B,
                     Finance) -> the mechanism replicates across model AND domain.
fig_dual_oracle.png: the same dose-response graded by the inherited LLM oracle vs the independent non-LLM rule
                     oracle (pooled dual-oracle runs) -> the relationship is not a judge-confidence artifact.
"""
from __future__ import annotations
import json, glob, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
import certainty_core as cc

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "..", "logs")
FIG = os.path.join(HERE, "..", "docs", "figures")
NB = 5


def recs(glob_pat, arms=("certainty", "neutral")):
    out = []
    for f in sorted(glob.glob(os.path.join(LOG, glob_pat))):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        for a in arms:
            out += d.get(a, {}).get("records", [])
    return out


def dose(lex, hij):
    b = [[] for _ in range(NB)]
    for l, h in zip(lex, hij):
        b[min(NB - 1, int(cc.norm01(l) * NB))].append(h)
    xs = [(i + .5) / NB for i in range(NB)]
    ys = [np.mean(x) if x else np.nan for x in b]
    ns = [len(x) for x in b]
    return xs, ys, ns


def fig_dose_multi():
    settings = [("SRE / Llama-3.2-3B", "tab2_big_s*.json", "#1f77b4", "o", ("certainty", "neutral", "concat")),
                ("SRE / Qwen-2.5-7B",  "qwen_headline_s*.json", "#2ca02c", "s", ("certainty", "neutral")),
                ("Finance / Llama-3.2-3B", "finance_headline_s*.json", "#d62728", "^", ("certainty", "neutral"))]
    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    for name, pat, col, mk, arms in settings:
        r = recs(pat, arms)
        if not r:
            continue
        lex = [x["lex_raw"] for x in r]; hij = [x["hijacked"] for x in r]
        rho, p = stats.spearmanr(lex, [x["grade"] for x in r])
        xs, ys, ns = dose(lex, hij)
        ax.plot(xs, ys, "-" + mk, color=col, lw=2, ms=7,
                label=f"{name}  ($\\rho$={rho:+.2f}, p={p:.0e}, n={len(r)})")
    ax.set_xlabel("worker output certainty (normalized bin)")
    ax.set_ylabel("hijack ASR")
    ax.set_ylim(0, 1.0); ax.set_xlim(0, 1.0); ax.grid(alpha=.3)
    ax.legend(fontsize=8, loc="upper left")
    ax.set_title("Certainty$\\to$hijack dose-response replicates across model and domain", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig_dose_multi.png"), dpi=150); plt.close(fig)
    print("saved fig_dose_multi.png")


def fig_dual_oracle():
    lex = []; lh = []; rh = []; llm_g = []; rule_s = []
    for f in sorted(glob.glob(os.path.join(LOG, "dual_oracle_s[234].json"))):
        d = json.load(open(f)).get("_raw")
        if not d:
            continue
        lex += d["lex_raw"]; lh += d["llm_hijacked"]; rh += d["rule_hijacked"]
        llm_g += d["llm_grade"]; rule_s += d["rule_score"]
    from sklearn.metrics import cohen_kappa_score
    k = cohen_kappa_score(lh, rh)
    rr = stats.spearmanr(lex, rule_s)[0]; rl = stats.spearmanr(lex, llm_g)[0]
    xs, yl, _ = dose(lex, lh)
    _, yr, ns = dose(lex, rh)
    fig, ax = plt.subplots(figsize=(6.0, 3.8))
    ax.plot(xs, yl, "-o", color="#7f7f7f", lw=2, ms=7, label=f"inherited LLM oracle ($\\rho$={rl:+.2f})")
    ax.plot(xs, yr, "-s", color="#1f77b4", lw=2.2, ms=7, label=f"independent non-LLM oracle ($\\rho$={rr:+.2f})")
    for x, y, n in zip(xs, yr, ns):
        if not np.isnan(y):
            ax.annotate(f"n={n}", (x, y), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=7)
    ax.set_xlabel("worker output certainty (normalized bin)")
    ax.set_ylabel("hijack rate")
    ax.set_ylim(0, 1.0); ax.set_xlim(0, 1.0); ax.grid(alpha=.3)
    ax.legend(fontsize=8.5, loc="upper left")
    ax.set_title(f"Certainty$\\to$hijack survives an independent oracle\n"
                 f"(oracle agreement $\\kappa$={k:.2f}, n={len(lex)}; rules out a judge-confidence artifact)", fontsize=9.5)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig_dual_oracle.png"), dpi=150); plt.close(fig)
    print(f"saved fig_dual_oracle.png  (kappa={k:.3f}, rho_rule={rr:.3f}, rho_llm={rl:.3f})")


if __name__ == "__main__":
    fig_dose_multi(); fig_dual_oracle()
