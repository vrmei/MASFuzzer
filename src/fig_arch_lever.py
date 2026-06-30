"""Figure 1 (architecture-first): different MAS architectures are hijacked by different levers.
Per-architecture BEST lever rho (from the feature/structural probes), colored by lever type, ordered by
safety-judgment outsourcing; certainty rho shown as a reference. Certainty is the special case at an auditor edge.
"""
import os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

FIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "figures")

archs = ["single", "swarm", "groupchat", "pipeline", "supervisor"]
gate = ["no auditor\n(fused)", "no auditor\n(handoff)", "broadcast\n+safety", "auditor\n+plan",
        "auditor\n(Manager-Worker)"]
lever = ["(none)", "endorsement\n(handoff)", "vote balance", "certainty", "certainty"]
rho = [0.05, 0.45, 0.26, 0.36, 0.49]      # best-lever rho per architecture
cert = [0.01, 0.08, 0.23, 0.36, 0.49]     # certainty rho (reference)
ltype = ["none", "endorsement", "vote", "certainty", "certainty"]
COL = {"certainty": "#1f77b4", "endorsement": "#9467bd", "vote": "#ff7f0e", "none": "#bdbdbd"}

x = np.arange(len(archs))
fig, ax = plt.subplots(figsize=(7.6, 4.2))
ax.bar(x, rho, 0.6, color=[COL[t] for t in ltype], edgecolor="k", lw=.4)
ax.plot(x, cert, "D", color="#555", ms=6)
for i, (r, l) in enumerate(zip(rho, lever)):
    ax.text(i, r + 0.012, l, ha="center", va="bottom", fontsize=8.2, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels([f"{a}\n[{g}]" for a, g in zip(archs, gate)], fontsize=8.3)
ax.set_ylabel(r"$\rho$(lever, hijack grade)")
ax.set_ylim(0, 0.62)
ax.grid(axis="y", alpha=.3)
leg = [Patch(facecolor=COL["certainty"], label="certainty (auditor)"),
       Patch(facecolor=COL["endorsement"], label="endorsement (handoff)"),
       Patch(facecolor=COL["vote"], label="vote balance (broadcast)"),
       Patch(facecolor=COL["none"], label="no lever"),
       plt.Line2D([], [], marker="D", color="#555", ls="", label=r"certainty $\rho$ ref")]
ax.legend(handles=leg, fontsize=7.6, loc="upper left")
ax.annotate("increasing safety-judgment OUTSOURCING  -->", (2, 0.57), ha="center", fontsize=8.5, color="#666")
ax.set_title("Different MAS architectures are hijacked by different levers\n"
             "(certainty is the special case at an auditor edge; the lever shifts with the gate)", fontsize=10)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_arch_lever.png"), dpi=150)
print("saved fig_arch_lever.png")
