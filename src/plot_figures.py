"""Generate the paper figures from the real logs. Saves PNGs to docs/figures/.
  fig_dose.png   — pooled certainty-bin -> hijack ASR dose-response (the mechanism)
  fig_table2.png — certainty vs fair baselines, big-scale 3-seed ASR mean±std (the headline)
  fig_table5.png — architecture x guidance ASR mean±std (the honest generalization map)
"""
from __future__ import annotations
import json, os, glob
from statistics import mean, pstdev
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(HERE, "..", "logs")
FIGS = os.path.join(HERE, "..", "docs", "figures")
os.makedirs(FIGS, exist_ok=True)
C = {"certainty": "#1f77b4", "recipe": "#9467bd", "neutral": "#7f7f7f", "concat": "#bcbcbc"}


def load(p):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return None


def pooled_records():
    recs = []
    for f in sorted(glob.glob(os.path.join(LOGS, "tab2_big_s*.json"))):
        d = load(f)
        if not d:
            continue
        for arm in ("certainty", "neutral", "concat"):
            recs += d.get(arm, {}).get("records", [])
    return recs


def fig_dose():
    recs = pooled_records()
    nb = 5
    bins = [[] for _ in range(nb)]
    for r in recs:
        bins[min(nb - 1, int(r["lex_norm"] * nb))].append(r["hijacked"])
    xs = [f"[{i/nb:.1f},\n{(i+1)/nb:.1f})" for i in range(nb)]
    ys = [mean(b) if b else 0 for b in bins]
    ns = [len(b) for b in bins]
    rho, p = stats.spearmanr([r["lex_raw"] for r in recs], [r["grade"] for r in recs])
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    ax.plot(range(nb), ys, "-o", color=C["certainty"], lw=2.2, ms=8)
    for i, (y, n) in enumerate(zip(ys, ns)):
        ax.annotate(f"{y:.2f}\nn={n}", (i, y), textcoords="offset points", xytext=(0, 8),
                    ha="center", fontsize=8)
    ax.set_xticks(range(nb)); ax.set_xticklabels(xs, fontsize=8)
    ax.set_xlabel("worker output certainty (normalized lexicon bin)")
    ax.set_ylabel("hijack ASR")
    ax.set_ylim(0, max(ys) * 1.25 + 0.05)
    ax.set_title(f"Certainty→hijack dose-response  (ρ={rho:+.2f}, p={p:.1e}, n={len(recs)})", fontsize=10)
    ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(os.path.join(FIGS, "fig_dose.png"), dpi=150); plt.close(fig)
    print(f"fig_dose: n={len(recs)} rho={rho:+.3f} p={p:.2e}")


def fig_table2():
    arms = ["certainty", "neutral", "concat"]
    seeds = [load(os.path.join(LOGS, f"tab2_big_s{s}.json")) for s in (0, 1, 2)]
    seeds = [d for d in seeds if d and all(a in d for a in arms)]
    means = {a: mean([d[a]["asr"] for d in seeds]) for a in arms}
    stds = {a: pstdev([d[a]["asr"] for d in seeds]) for a in arms}
    fig, ax = plt.subplots(figsize=(4.6, 3.6))
    bars = ax.bar(range(len(arms)), [means[a] for a in arms], yerr=[stds[a] for a in arms],
                  color=[C[a] for a in arms], capsize=5, width=.6)
    labels = {"certainty": "certainty\n(ours)", "neutral": "neutral\n(same LLM)", "concat": "concat\n(random ops)"}
    ax.set_xticks(range(len(arms))); ax.set_xticklabels([labels[a] for a in arms], fontsize=9)
    ax.set_ylabel("hijack ASR"); ax.set_ylim(0, 0.62)
    for i, a in enumerate(arms):
        ax.annotate(f"{means[a]:.2f}±{stds[a]:.2f}", (i, means[a] + stds[a]), textcoords="offset points",
                    xytext=(0, 4), ha="center", fontsize=9, fontweight="bold" if a == "certainty" else "normal")
    ax.set_title(f"Supervisor (Manager–Worker): certainty steering\nvs fair baselines (n=216/arm, {len(seeds)} seeds)", fontsize=10)
    ax.grid(axis="y", alpha=.3)
    fig.tight_layout(); fig.savefig(os.path.join(FIGS, "fig_table2.png"), dpi=150); plt.close(fig)
    print(f"fig_table2: {means}")


def fig_table5():
    archs = ["supervisor", "single", "pipeline", "groupchat", "swarm"]
    arms = ["certainty", "recipe", "neutral", "concat"]
    data = {}
    for A in archs:
        files = (sorted(glob.glob(os.path.join(LOGS, f"arch_{A}_s[1-9].json")))
                 + sorted(glob.glob(os.path.join(LOGS, f"arch_{A}_big_s[0-9].json"))))
        ds = [load(f) for f in files]; ds = [d for d in ds if d]
        data[A] = {a: ([d[a]["asr"] for d in ds if a in d]) for a in arms}
    fig, ax = plt.subplots(figsize=(8.6, 4.0))
    w = 0.2
    for j, a in enumerate(arms):
        ms = [mean(data[A][a]) if data[A][a] else 0 for A in archs]
        es = [pstdev(data[A][a]) if len(data[A][a]) > 1 else 0 for A in archs]
        ax.bar([i + j * w for i in range(len(archs))], ms, w, yerr=es, capsize=3,
               color=C[a], label=a)
    ax.set_xticks([i + 1.5 * w for i in range(len(archs))])
    ax.set_xticklabels([A + ("\n(auditor-gated)" if A in ("supervisor", "pipeline") else "") for A in archs], fontsize=9)
    ax.set_ylabel("hijack ASR"); ax.set_ylim(0, 0.85)
    ax.legend(ncol=4, fontsize=8, loc="upper right")
    ax.axvspan(-0.15, 0.75, color="#fff3cd", alpha=.5, zorder=0)  # highlight supervisor (the stable cell)
    ax.annotate("ONLY stable\ncertainty win", (0.3, 0.78), ha="center", fontsize=8, color="#8a6d00")
    ax.set_title("Architecture × guidance (n=4 configs: 3 seeds@n36 + 1 big@n72). Certainty wins robustly ONLY in supervisor.", fontsize=9.5)
    ax.grid(axis="y", alpha=.3)
    fig.tight_layout(); fig.savefig(os.path.join(FIGS, "fig_table5.png"), dpi=150); plt.close(fig)
    print("fig_table5: done")


if __name__ == "__main__":
    fig_dose(); fig_table2(); fig_table5()
    print("saved to", FIGS)
