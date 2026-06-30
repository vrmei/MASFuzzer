"""Figure 1 = the MASFuzzer METHOD diagram (not a results plot).
The fitness the attacker hill-climbs is the DENSE intermediate LEVER measured on the upstream agent output
(certainty / endorsement / vote, by gate)---NOT the sparse final hijack outcome. This is the design that
distinguishes the fuzzer from the (measurement-only) capability paradox.
"""
import os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

FIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "figures")
fig, ax = plt.subplots(figsize=(7.6, 3.6))
ax.set_xlim(0, 100); ax.set_ylim(0, 50); ax.axis("off")


def box(x, y, w, h, text, fc, fs=8.5, tc="black"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=1.2", fc=fc, ec="black", lw=1.1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc)


def arrow(x1, y1, x2, y2, text="", col="black", rad=0.0, fs=7.5, lw=1.4):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14,
                                 color=col, lw=lw, connectionstyle=f"arc3,rad={rad}"))
    if text:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 2.2, text, ha="center", va="bottom", fontsize=fs, color=col)


box(2, 30, 20, 13, "Attacker LLM\nrewrites $x$ to\nraise $\\ell_\\tau$", "#dbe9f6")
box(40, 31, 30, 16, "", "#ffffff")
ax.text(55, 45.2, "MAS topology $\\tau$", ha="center", va="center", fontsize=8.8)
box(42, 33, 12.5, 9.5, "upstream\nagents $o_{<n}$", "#fde9d9")
box(56, 33, 12, 9.5, "decider\n$d=o_n$", "#e2efda")
box(80, 33, 17, 13, "Oracle\n$O(d){\\geq}2$?\n(sparse)", "#f2dcdb")

arrow(22, 36.5, 40, 39.5, "mutated $x$")
arrow(70, 39.5, 80, 39.5)

arrow(48, 34.5, 40, 18, col="#1f77b4", rad=0.25, lw=1.8)
box(20, 8, 46, 12,
    "FITNESS $\\ell_\\tau$ = lever on the upstream output\n(dense, every candidate) -- NOT the sparse hijack label",
    "#d6eadf", fs=8.2, tc="#0b5")
arrow(20, 14, 8, 30, "hill-climb $\\ell_\\tau$ (elites)", col="#1f77b4", rad=0.25, lw=1.8)

ax.text(83, 14,
        "$\\ell_\\tau$ is topology-native:\nauditor $\\to$ certainty\nhandoff $\\to$ endorsement\nbroadcast $\\to$ vote",
        ha="center", va="center", fontsize=7.6,
        bbox=dict(boxstyle="round", fc="#fff6d6", ec="#caa"))

ax.text(50, 48.5, "MASFuzzer: hill-climb the dense intermediate lever (the fitness), not the sparse outcome",
        ha="center", fontsize=9.3, fontweight="bold")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_method.png"), dpi=150, bbox_inches="tight")
print("saved fig_method.png")
