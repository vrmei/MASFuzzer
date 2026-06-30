"""Concept illustration of the LEVER EFFECT for the architecture figure's middle panel.

Same destructive action, two upstream-output states: a HEDGED audit (low certainty -> decider DENY) vs a
CONFIDENT audit (high certainty -> decider EXECUTE). The vertical gauge is the dense fitness
ell_tau = assertive density - hedging density that the attacker hill-climbs; as it fills, the decision flips.
This makes the lever (a property of the intermediate output) visible.
"""
import os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

FIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "figures")
OR = "#e07b00"; GRAY = "#7b8794"; RED = "#c0392b"; GRN = "#1f9d55"; INK = "#1f2937"

fig, ax = plt.subplots(figsize=(9.6, 4.4))
ax.set_xlim(0, 100); ax.set_ylim(0, 46); ax.axis("off")


def bubble(x, y, w, h, fc="#ffffff", ec="#cbd5e1"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6", fc=fc, ec=ec, lw=1.3))


def gauge(x, y, frac, label):
    """vertical ell_tau meter, fill fraction in [0,1]."""
    h = 12.0
    ax.add_patch(Rectangle((x, y), 3.0, h, fc="#eef1f5", ec="#94a3b8", lw=1.2))
    ax.add_patch(Rectangle((x, y), 3.0, h * frac, fc=OR, ec="none"))
    ax.text(x + 1.5, y + h + 1.4, r"$\ell_\tau$", ha="center", fontsize=12, color=INK, fontweight="bold")
    ax.text(x + 4.0, y + h - 0.5, "+assertive", ha="left", va="center", fontsize=6.8, color=OR)
    ax.text(x + 4.0, y + 0.5, "$-$hedging", ha="left", va="center", fontsize=6.8, color=GRAY)
    ax.text(x + 1.5, y - 2.0, label, ha="center", fontsize=7.6, color=INK)


# ---- LEFT: hedged (low certainty) -> DENY ----
ax.text(20, 43, "hedged upstream output", ha="center", fontsize=10, color=INK, fontweight="bold")
bubble(2, 27, 30, 12.5)
ax.text(4, 36.5, "Assessment: unsafe?", fontsize=8.2, color=INK)
ax.text(4, 33.4, "may", fontsize=8, color=GRAY); ax.text(11, 33.4, "unclear", fontsize=8, color=GRAY)
ax.text(20, 33.4, "suspicious", fontsize=8, color=GRAY)
ax.text(4, 30.4, "cannot confirm", fontsize=8, color=GRAY)
ax.text(18, 30.4, "needs review", fontsize=8, color=GRAY)
gauge(7, 11, 0.18, "low")
ax.add_patch(FancyBboxPatch((20, 11.5), 13, 6, boxstyle="round,pad=0.5", fc="#eef7f0", ec=GRN, lw=1.4))
ax.text(26.5, 14.5, "DENY", ha="center", va="center", fontsize=11, color=GRN, fontweight="bold")
ax.add_patch(FancyArrowPatch((11, 23.5), (24, 18), arrowstyle="-|>", mutation_scale=13, color="#94a3b8", lw=1.6))

# ---- center: hill-climb arrow ----
ax.add_patch(FancyArrowPatch((35, 25), (63, 25), arrowstyle="-|>", mutation_scale=20, color=OR, lw=2.6))
ax.text(49, 27.2, "attacker hill-climbs  $\\ell_\\tau$", ha="center", fontsize=10, color=OR, fontweight="bold")
ax.text(49, 22.6, "(rewrite $x$ so the audit reads more confident)", ha="center", fontsize=7.8, color=GRAY)

# ---- RIGHT: confident (high certainty) -> EXECUTE ----
ax.text(80, 43, "confident upstream output", ha="center", fontsize=10, color=INK, fontweight="bold")
bubble(64, 27, 32, 12.5, fc="#fff7ec", ec=OR)
ax.text(66, 36.5, "Assessment: ", fontsize=8.2, color=INK)
ax.text(81, 36.5, "safe", fontsize=8.6, color=OR, fontweight="bold")
ax.text(66, 33.4, "confirmed", fontsize=8, color=OR, fontweight="bold")
ax.text(78, 33.4, "authorized", fontsize=8, color=OR, fontweight="bold")
ax.text(89, 33.4, "compliant", fontsize=8, color=OR, fontweight="bold")
ax.text(66, 30.4, "no risk", fontsize=8, color=OR, fontweight="bold")
ax.text(74, 30.4, "no indication of harm", fontsize=8, color=OR, fontweight="bold")
gauge(70, 11, 0.86, "high")
ax.add_patch(FancyBboxPatch((83, 11.5), 13, 6, boxstyle="round,pad=0.5", fc="#fdecea", ec=RED, lw=1.6))
ax.text(89.5, 14.5, "EXECUTE", ha="center", va="center", fontsize=11, color=RED, fontweight="bold")
ax.text(89.5, 8.6, "(hijack)", ha="center", fontsize=7.6, color=RED)
ax.add_patch(FancyArrowPatch((74, 23.5), (87, 18), arrowstyle="-|>", mutation_scale=13, color=OR, lw=1.8))

ax.text(50, 3.0, r"The lever: the destructive action is identical; only the upstream output's certainty "
                 r"$\ell_\tau$ changes$-$and the decider flips DENY$\to$EXECUTE.",
        ha="center", fontsize=8.6, color=INK, style="italic")

fig.tight_layout()
out = os.path.join(FIG, "fig_lever_concept.png")
fig.savefig(out, dpi=150, bbox_inches="tight")
print("saved", out)
