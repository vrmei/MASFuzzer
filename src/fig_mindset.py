"""Figure: the accountability sink. Inserting a separable safety auditor shifts the DECIDER's mindset --
it performs less of its OWN risk analysis and defers more -- on identical actions.

Reads logs/mindset_analysis.json (run_mindset_analysis.py). Decider model held fixed (DeepSeek-V3); only the
auditor is added/removed. Two judge ratings (0--2): own-scrutiny (independent risk analysis of the action) and
deference (reliance on an upstream verdict). Error bars = SE; significance by Mann--Whitney.
(We do NOT plot the within-auditor certainty->scrutiny trend: it is null, rho=-0.05 p=.66.)
"""
from __future__ import annotations
import json, os, math
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
J = os.path.join(HERE, "..", "logs", "mindset_analysis.json")
FIG = os.path.join(HERE, "..", "docs", "figures")


def se(xs):
    xs = [x for x in xs if x is not None]
    return (np.std(xs, ddof=1) / math.sqrt(len(xs))) if len(xs) > 1 else 0.0


def vals(recs, key):
    return [r[key] for r in recs if r.get(key) is not None]


def main():
    d = json.load(open(J, encoding="utf-8"))
    rec = d["records"] if "records" in d else d
    no, wa = rec["no_auditor"], rec["with_auditor"]

    fig, ax = plt.subplots(figsize=(6.4, 3.9))
    metrics = [("scrutiny", "decider's OWN\nrisk analysis"), ("deference", "deference to an\nupstream verdict")]
    x = np.arange(len(metrics)); w = 0.36
    no_m = [np.mean(vals(no, k)) for k, _ in metrics]
    wa_m = [np.mean(vals(wa, k)) for k, _ in metrics]
    no_e = [se(vals(no, k)) for k, _ in metrics]
    wa_e = [se(vals(wa, k)) for k, _ in metrics]
    ax.bar(x - w/2, no_m, w, yerr=no_e, capsize=4, color="#4c72b0", label="no auditor (decider alone)")
    ax.bar(x + w/2, wa_m, w, yerr=wa_e, capsize=4, color="#c44e52", label="with auditor (decider defers)")
    for xi, v in zip(x - w/2, no_m):
        ax.text(xi, v + 0.04, f"{v:.2f}", ha="center", fontsize=9)
    for xi, v in zip(x + w/2, wa_m):
        ax.text(xi, v + 0.04, f"{v:.2f}", ha="center", fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels([lab for _, lab in metrics])
    ax.set_ylabel("judge rating (0--2)"); ax.set_ylim(0, 2.0)
    ax.legend(fontsize=8.5, loc="upper right")
    ax.grid(axis="y", alpha=.3)
    # significance star on scrutiny
    try:
        _, p = stats.mannwhitneyu(vals(no, "scrutiny"), vals(wa, "scrutiny"), alternative="greater")
        ax.annotate(f"$p$={p:.0e}", (0, max(no_m[0], wa_m[0]) + 0.22), ha="center", fontsize=9, color="#333")
        ax.plot([-w/2, w/2], [max(no_m[0], wa_m[0]) + 0.18]*2, color="#333", lw=1)
    except Exception:
        p = float("nan")
    ax.set_title("The accountability sink: inserting an auditor halves the decider's own scrutiny\n"
                 "(decider model fixed; actions identical)", fontsize=9.5)
    fig.tight_layout()
    out = os.path.join(FIG, "fig_mindset.png")
    fig.savefig(out, dpi=150); plt.close(fig)
    print("saved", out, "| scrutiny %.2f->%.2f p=%.1e | deference %.2f->%.2f | decider_cert %.1f->%.1f"
          % (no_m[0], wa_m[0], p, no_m[1], wa_m[1],
             np.mean(vals(no, "decider_cert")), np.mean(vals(wa, "decider_cert"))))


if __name__ == "__main__":
    main()
