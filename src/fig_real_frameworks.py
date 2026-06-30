"""Figure: the certainty->hijack mechanism reproduces on REAL MAS frameworks (LangGraph / AutoGen / CrewAI).

Panel A: per-framework ASR, certainty arm vs neutral arm (LLM oracle), error bars = std across the 7 reps.
Panel B: pooled certainty->hijack dose-response per framework, annotated with the cluster-robust rho and 95% CI.
Reads logs/real/<fw>_real.json produced by run_real_frameworks.py.
"""
from __future__ import annotations
import json, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "..", "logs", "real")
FIG = os.path.join(HERE, "..", "docs", "figures")
FW = [("langgraph", "LangGraph", "#1f77b4"), ("autogen", "AutoGen", "#2ca02c"), ("crewai", "CrewAI", "#d62728")]


def load(fw):
    p = os.path.join(LOG, f"{fw}_real.json")
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return None


def main():
    data = [(fw, name, col, load(fw)) for fw, name, col in FW]
    data = [d for d in data if d[3] and "pooled" in d[3]]
    if not data:
        print("no real-framework results yet"); return

    fig, (axA, axB) = plt.subplots(1, 2, figsize=(11, 4.0))

    # Panel A: certainty vs neutral ASR (LLM oracle), mean +/- sd across reps
    x = np.arange(len(data)); w = 0.36
    cert = [d[3]["pooled"]["arm_summary"]["certainty"]["asr_llm_mean"] for d in data]
    cert_sd = [d[3]["pooled"]["arm_summary"]["certainty"]["asr_llm_sd"] for d in data]
    neut = [d[3]["pooled"]["arm_summary"]["neutral"]["asr_llm_mean"] for d in data]
    neut_sd = [d[3]["pooled"]["arm_summary"]["neutral"]["asr_llm_sd"] for d in data]
    axA.bar(x - w/2, cert, w, yerr=cert_sd, capsize=3, color="#1f77b4", label="certainty-steered")
    axA.bar(x + w/2, neut, w, yerr=neut_sd, capsize=3, color="#bbbbbb", label="neutral (same rewriter)")
    axA.set_xticks(x); axA.set_xticklabels([d[1] for d in data])
    axA.set_ylabel("hijack ASR (LLM oracle)"); axA.set_ylim(0, 1.0)
    axA.set_title("Certainty-steering beats neutral on REAL frameworks", fontsize=10)
    axA.legend(fontsize=8.5, loc="upper right"); axA.grid(axis="y", alpha=.3)
    for xi, c in zip(x, cert):
        axA.text(xi - w/2, c + 0.02, f"{c:.2f}", ha="center", fontsize=8)

    # Panel B: pooled dose-response per framework
    for fw, name, col, d in data:
        dr = d["pooled"]["dose_llm"]
        xs = [(i + .5) / len(dr) for i in range(len(dr))]
        ys = [b["asr"] if b["asr"] is not None else np.nan for b in dr]
        rho, p = d["pooled"]["rho_cert_llmgrade"]
        lo, hi = d["pooled"].get("ci_llm", [None, None])
        ci = f", CI[{lo:+.2f},{hi:+.2f}]" if lo is not None else ""
        axB.plot(xs, ys, "-o", color=col, lw=2, ms=6, label=f"{name} ($\\rho$={rho:+.2f}{ci})")
    axB.set_xlabel("auditor output certainty (normalized bin)")
    axB.set_ylabel("hijack ASR"); axB.set_ylim(0, 1.0); axB.set_xlim(0, 1.0); axB.grid(alpha=.3)
    axB.set_title("Auditor-certainty$\\to$hijack dose-response (real frameworks)", fontsize=10)
    axB.legend(fontsize=8, loc="upper left")

    fig.tight_layout()
    out = os.path.join(FIG, "fig_real_frameworks.png")
    fig.savefig(out, dpi=150); plt.close(fig)
    print("saved", out)


if __name__ == "__main__":
    main()
