# MASFuzzer paper — draft assembly (reading order)

Single entry point to the draft. Sections live in separate files; this indexes them in paper order with status.

| # | Section | File | Status |
|---|---|---|---|
| — | Pre-registration (frozen RQ/H, baselines, falsification) | [PAPER_SKELETON.md](PAPER_SKELETON.md) §Stage1/3 | done |
| 0 | Abstract | [paper_intro_defense.md](paper_intro_defense.md) §Abstract | draft prose |
| 1 | Introduction (funnel + 4 contributions) | [paper_intro_defense.md](paper_intro_defense.md) §Intro | draft prose |
| 2 | Related Work (3 clusters + positioning) | [paper_related_work.md](paper_related_work.md) | draft prose; PDFs verified, full-text reads pending |
| 3 | Method (3.1–3.7 + Algorithm 1) | [paper_method.md](paper_method.md) | draft prose |
| 4 | Experiments & Results (4.1–4.6, Tables 2/4/5) | [paper_results.md](paper_results.md) (prose) + [PAPER_SKELETON.md](PAPER_SKELETON.md) §4 (tables) | draft prose; refreshing numbers with big-scale seeds=25/budget=72 |
| 5 | Defense (mechanism → mitigation) | [paper_intro_defense.md](paper_intro_defense.md) §Defense | draft prose |
| 6 | Limitations | [paper_intro_defense.md](paper_intro_defense.md) §Limitations | draft prose |
| 7 | Ethics & responsible disclosure | [paper_intro_defense.md](paper_intro_defense.md) §Ethics | draft prose |
| — | References | [references.bib](references.bib) | 12 IDs verified; 4 author fields [verify] |
| — | Evidence docs | [COVERAGE_RESULTS.md](COVERAGE_RESULTS.md), [SUCCESS_CONDITIONS.md](SUCCESS_CONDITIONS.md), [ARCH_GUIDANCE_MATRIX.md](ARCH_GUIDANCE_MATRIX.md) | result logs |
| — | Figures | figures/fig_dose.png (Fig 2, §4.2), fig_table2.png (Fig 3, §4.3), fig_table5.png (Fig 4, §4.5) | generated from logs by src/plot_figures.py |

## One-paragraph thesis (the spine)
The capability paradox says a *confident auditor* hijacks a MAS via its output certainty. We make that certainty
a black-box fuzzing fitness: an LLM mutator climbs it, ~doubling ASR over a fair baseline (0.47 vs 0.24, 3
seeds) with coherence held, and replicating a monotone certainty→hijack dose-response (ρ=0.42, p<1e-6) in the
Manager-Worker topology. The lever is auditor-edge-specific: across five architectures with multi-seed + multi-scale error bars it is the
stable winner in exactly one topology — the supervisor (auditor→manager) edge — with no stable guidance winner
anywhere else (single-agent winner even flips with scale). We map this honest boundary rather than claim a rule.
Alongside, an adversarially-verified taxonomy of what makes attacks succeed across 14 managers. The same
mechanism yields the defenses (decider-side certainty-skepticism).

## Headline numbers (final / near-final)
- Table 2 (**big scale**, n=216/arm, 3 seeds): certainty **0.45±.05** (coh 0.94) > concat 0.37±.01 > neutral
  0.27±.02 (coh 0.88); certainty lead non-overlapping on ASR + coherence.
- Dose-response: ρ=+0.36 to +0.42, p down to 5.6e-9 (pooled, n≈450); supervisor matrix ρ=0.42 p<1e-6 ×2 seeds.
- Success-conditions: live-attacker reframe 42–46% vs 8%; commander voice 67% vs 27%; euphemized verb 80% vs 8%.
- Table 5 (n=4: 3 seeds@n36 + 1 big@n72): supervisor certainty **0.52±.06 STABLE 4/4** (ρ=.42 p<1e-6) — the
  ONLY stable cell. single MIXED (recipe@n36→cert@n72), pipeline wash, groupchat/swarm high-variance.
  Strong-decider reactivation RETRACTED. Honest scope: advantage is auditor-edge-specific, not a rule.
