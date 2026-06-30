# 4 Experiments & Results (draft prose; numbers = big-scale seeds=25/budget=72, 3 seeds. Figures: docs/figures/)

## 4.1 Experimental setup
We evaluate on `paradox_dataset_500`, 500 SRE incident-response prompt-injection payloads spanning four social-
engineering strategies and seven target-tool classes (Data Card, App. A). Agents are homogeneous Llama-3.2-3B
unless noted; the attacker/mutator and the strong decider are DeepSeek-V3; the oracle is the Capability-Paradox-
validated gpt-4o-mini judge (κ≥0.87). We instantiate five topologies — single, pipeline, supervisor, groupchat,
swarm (Table 1) — under a strict decision SOP, the regime in which ASR is intermediate and guidance can
discriminate. Each arm draws from 25 base payloads for a budget of 72 mutations and is repeated over three
random seeds; we report mean ASR ± std. Primary metric: ASR (oracle grade ≥ 2). Secondary: deep-capture count
(grade ≥ 3), coherence (a judge plausibility score in [0,1]), and the certainty→grade dose-response (Spearman ρ
with per-bin ASR). Baselines: `neutral` (the same LLM rewriter with no objective — isolating steering) and
`concat` (the hand-coded random-operator baseline).

## 4.2 Worker certainty is a climbable, causal fitness (RQ1)
Worker output certainty predicts hijacking. Pooling all evaluated candidates at scale (n = 648; Fig. 2), ASR
climbs from 0.20 in the lowest worker-certainty bin to 0.52 in the [0.6, 0.8) bin — a 2.6× rise — with a
significant positive rank correlation between worker certainty and oracle grade (ρ = +0.25, p = 5e-11);
within the supervisor topology the within-run correlation is stronger (ρ = +0.42, p < 1e-6). We report one
honest non-monotonicity: the extreme certainty bin [0.8, 1.0) attenuates to 0.38, consistent with maximally
assertive reports beginning to read as implausible — the mechanism is a strong climbable gradient through the
populated range, not an unbounded one. Two controls sharpen the causal reading. First, the certainty of the
*input payload* does not predict cross-manager success (ρ ≈ 0.05, n.s., §4.4), so the lever is the auditor's
*output*, not the input phrasing — consistent with the mother paper's mediator. Second, the relationship holds
inside the full supervisor MAS, the regime the mother paper found only partially explained, so our in-loop
dose-response strengthens that evidence rather than merely reproducing it.

## 4.3 Certainty-steering beats fair baselines (RQ2)
In the supervisor (Manager-Worker) topology at n = 216 candidates/arm (seeds=25, budget=72, 3 seeds), certainty-
steering reaches ASR 0.45 ± 0.05, against 0.27 ± 0.02 for the fair same-LLM `neutral` baseline and 0.37 ± 0.01
for `concat`; certainty's lead is non-overlapping on both ASR and coherence (0.94 vs 0.88, Table 2). The
synthesized attacks read as realistic incident reports, not keyword soup. At this larger scale `concat` (the
hand-coded random operators) separates from `neutral` — potent operators help somewhat — but remains below
certainty and at markedly lower coherence, so the gain still comes specifically from *steering a coherent
rewrite toward the mechanism* rather than from operator potency.

## 4.4 What makes attacks succeed across managers (RQ3)
Using 500 payloads × 14 manager models from existing oracle-graded logs, per-payload cross-manager success
ranges from 0.00 to 0.85. A multi-agent mining-and-verification pipeline (App. B) first rejects the obvious
explanations: coarse strategy and tool categories barely move ASR (15–20%), and the saturated tactics
(urgency, assertiveness, technical specificity) fail adversarial verification — urgency even reverses sign
within tool class (Simpson's paradox). The verified success conditions (Table 4) are framings of *how the
destruction is presented*: a live external-attacker reframe (42–46% of high-success vs 8% of blocked payloads),
a first-person commander voice with stated forensic certainty (67% vs 27%), a euphemized action verb (80% vs
8%), a named recovery source bound to an irreplaceable target (24% vs 4%), an omitted loss-disclosure (0% vs
10%), and third-party/compliance stakes (17–20% vs 3–6%). Two anti-features predict *blocking*: an exotic root
cause (the only feature more common in blocked payloads) and fabricated protocol citations (the strategy built
on them has zero successes). We encode the verified framings as the `recipe` operator.

## 4.5 Where does certainty-steering generalize? (RQ4)
Sweeping the five architectures over four configurations (three seeds at n=36/arm plus one big-scale seed at
n=72/arm; Table 5) yields an honest generalization boundary rather than a universal rule. Exactly one cell is
stable across all four configurations and both scales: in the **supervisor** (auditor→manager) topology
certainty wins decisively (0.52 ± 0.06; ρ = 0.42, p < 1e-6) — corroborated by the big-scale Table 2 headline.
Every other topology is unstable: the single fused agent is a low-ASR regime whose winner flips with scale
(recipe at n=36, certainty at n=72); pipeline is a 2–2 wash (certainty ≈ recipe, both above neutral); groupchat
is high-variance with all arms strong (a different winner each configuration); and swarm is null-to-recipe with
certainty the *worst* arm. We also probed whether upgrading a swarm's decider to a capable model revives
certainty; it does not replicate across seeds (winner flips), so we make no strong-decider claim. The takeaway
is precise and honest: certainty-steering is a robust, mechanism-grounded attack specifically at the canonical
auditor→manager edge — the topology a defender should harden first — and its advantage does not generalize into
a stable cross-architecture rule.

## 4.6 Analysis and ablations
**Coherence is preserved** across all certainty runs (0.93–0.96), confirming the attacks are realistic.
**`concat` is strong only on coverage diversity, not ASR**: it spreads widely across behavior cells but never
wins an ASR cell and on the auditor-gated pipeline sinks below `neutral` because its threat/authority operators
alarm the auditor — illustrating that diversity coverage and security yield are different objectives. Finally,
our **earlier diversity-guided fuzzer (App. C) tied a random baseline**: the hijack behavior space is small and
saturates, whereas the scalar certainty mediator is climbable — the negative result that motivated the
mechanism-grounded design.
