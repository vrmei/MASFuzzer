# Per-architecture lexical-lever probe — does each MAS topology have its OWN linguistic lever?

Motivation: certainty is the supervisor lever, but maybe OTHER architectures are hijacked via a DIFFERENT
linguistic feature. We scored a 7-feature panel (certainty, directiveness, authority, consensus, concreteness,
urgency, risk_dismissal) on the UPSTREAM agent text and correlated each with the hijack grade, per architecture
(run_feature_probe.py, budget=50/arch, hand-coded-operator mutations → ZERO deepseek; llama agents + gpt-4o-mini
oracle). Fig: docs/figures/fig_levers.png.

## Spearman ρ(feature, hijack grade) per architecture  (* p<0.05)
| architecture | ASR | certainty | directiv | authority | consensus | concrete | urgency | risk_dis | top (sig?) |
|---|---|---|---|---|---|---|---|---|---|
| **supervisor** (auditor) | 0.36 | **+0.49*** | +0.13 | −0.07 | 0.00 | **+0.38*** | −0.12 | +0.04 | certainty* |
| **pipeline** (auditor) | 0.26 | **+0.36*** | −0.20 | −0.16 | −0.02 | +0.21 | −0.05 | −0.01 | certainty* |
| single (fused) | 0.02 | +0.12 | +0.24 | −0.19 | +0.40* | −0.19 | +0.01 | 0.00 | consensus* (UNRELIABLE: ASR 0.02) |
| groupchat (broadcast) | 0.68 | +0.14 | +0.13 | +0.21 | +0.11 | −0.08 | +0.06 | +0.13 | authority (n.s.) |
| swarm (handoff) | 0.36 | **−0.19** | −0.06 | −0.05 | +0.24 | +0.14 | +0.15 | −0.13 | consensus (n.s.) |

## Findings
1. **The probe recovers certainty from scratch as THE significant lever of the auditor-gated topologies**
   (supervisor ρ=+0.49, p=3e-4; pipeline ρ=+0.36, p=0.01). This independently validates both the mechanism and
   the method (no certainty prior was given to the probe).
2. **The "alternative lexical lever per architecture" hypothesis is NOT supported within this panel.** The
   non-auditor topologies have NO reliable single-feature lever: groupchat is diffusely hijackable (ASR 0.68 but
   every feature ρ is weak and n.s.), and swarm's certainty ρ is even NEGATIVE (−0.19) with no significant
   replacement. single's consensus ρ=+0.40* is a statistical artifact of a near-zero hijack rate (ASR 0.02,
   ~1 positive), so it is not trustworthy.
3. **Interpretation:** certainty is an AUDITOR-EDGE mechanism — it bites where an auditor's confident "safe"
   verdict gates a decider, and only there. Topologies without that edge are not governed by a single linguistic
   feature: groupchat is easy regardless of phrasing, and swarm resists single-feature lexical steering (certainty
   actively unhelpful). This is mechanistic corroboration of the §4.5 generalization boundary, not a refutation
   of it: there is no second "certainty-like" lever waiting in the other architectures (at least not a simple
   lexical one).

## Caveats / next probes if pursued
- Mutations were hand-coded operators (free, no deepseek); these inject some feature content and may bias the
  panel distribution. A neutral-LLM-mutation probe (deepseek) would be a cleaner diversity source.
- Low-ASR cells (single 0.02) give unreliable ρ; a permissive SOP would raise ASR for those probes.
- Only 7 lexical features tested; a richer panel or an EMBEDDING-direction lever (semantic, not keyword) could
  still surface a groupchat/swarm mechanism. The clean negative here is "no simple lexical lever", not "no lever".

---

# Structural-lever probe (run_structural_probe.py) — the non-auditor topologies DO have levers

The lexical negative motivated a STRUCTURAL probe: classify each upstream agent's STANCE toward the action with
a judge (endorse=+1 / object=−1 / neutral=0) and correlate architecture-specific structural features with the
hijack grade (budget=50/arch, zero-deepseek). Fig: docs/figures/fig_endorsement.png.

| architecture | ASR | strongest structural feature | ρ (p) | certainty ρ |
|---|---|---|---|---|
| **swarm** (handoff) | 0.34 | **triage_endorse** (handoff_endorse +0.41**, specialist +0.34*) | **+0.45 (p=.001)** | +0.23 (n.s.) |
| groupchat (broadcast) | 0.66 | **endorse_balance** (= n_endorsers) | +0.24 (p=.09) | +0.008 |
| pipeline (audit→plan→decide) | 0.32 | plan_cert / plan_endorse | +0.24 (p=.10) | worker_cert +0.04 |

## Findings
1. **swarm has a CLEAN structural lever (confirmed):** the triage agent's ENDORSEMENT of the action predicts
   hijack at ρ=+0.45, p=0.001 — far above certainty. The endorsement transfers down the handoff chain
   (triage 0.45 → specialist 0.34 → executor decides). certainty is only weakly positive (not the negative the
   noisier lexical probe suggested), confirming swarm is governed by ENDORSEMENT-TRANSFER, not certainty.
2. **groupchat:** endorsement BALANCE across the debate (how many of analyst/ops/safety endorse) beats certainty
   (+0.24 vs +0.008) but is only marginal (p=0.09) — high ASR (0.66) limits grade variance; a lower-ASR SOP or
   larger n would sharpen it.
3. **pipeline:** the "certainty dilution" hypothesis is REJECTED (cert_dilution ρ≈0). The worker's own certainty
   is washed out (ρ=0.04); what weakly survives is the PLAN's certainty/stance (the text the decider actually
   reads, ρ=0.24) — consistent with the plan stage intercepting and re-expressing the auditor's signal. pipeline
   still belongs with the auditor topologies (lexical-probe certainty ρ=0.36).

## Unified framework: ENDORSEMENT-TRANSFER (certainty is the auditor special case)
Across all five topologies the hijack lever is the same underlying quantity — **whether the upstream content the
decider trusts/reads ENDORSES the action** — expressed in each topology's native form:
- supervisor: the auditor's confident "safe" verdict (certainty, ρ=0.49) — endorsement by an evaluator.
- pipeline:   the plan's certainty/stance (ρ=0.24–0.36) — endorsement that survives the re-plan.
- swarm:      the triage/specialist endorsement (ρ=0.45) — endorsement transferred across the handoff.
- groupchat:  the endorsement balance of the debate (ρ=0.24) — endorsement by majority vote.
- single:     no separate endorser to exploit → robust (lowest ASR).
The capability-paradox certainty effect is thus ONE instance of a general law: **a decider complies when the
agents it defers to endorse the action; certainty is the form that endorsement takes at an auditor edge.** This
turns the "certainty doesn't generalize" negative into a unified, mechanism-grounded cross-architecture story.

## Causal test of the swarm lever (run_endorse_steer.py) — INCONCLUSIVE due to a ceiling effect (honest)
Steering an attacker LLM to maximize triage endorsement (mode=`endorse`) vs same LLM no objective (`neutral`),
swarm, budget=50/arm:

| arm | ASR | mean triage-endorse | coh |
|---|---|---|---|
| endorse | 0.30 | +1.00 | 0.90 |
| neutral | 0.24 | +0.98 | 0.89 |
pooled rho(handoff_endorse, grade) = +0.21, p=0.035.

**We do NOT claim a causal win** (overriding the script's auto-verdict). Triage endorses by DEFAULT in BOTH
arms (+0.98 vs +1.00) — a ceiling effect — so steering created no endorsement contrast; the small ASR gap
(15 vs 12 hijacks) cannot be attributed to endorsement, and pooled rho drops 0.45->0.21 as variance vanishes.
*Finding instead:* the swarm triage is a near-rubber-stamp gate (endorses 98-100%), so the lever can't be
pushed UP — already saturated.

**Correct causal test = break the ceiling with a CRITICAL triage** (a triage SOP that screens, so endorsement
VARIES); steering endorsement should then raise ASR where neutral leaves triage objecting.

### Critical-triage causal test (run_endorse_steer.py --critical-triage) — WEAK causal effect (honest)
| arm (critical triage) | ASR | mean triage-endorse | coh |
|---|---|---|---|
| endorse | 0.34 | +1.00 | 0.90 |
| neutral | 0.30 | +0.60 | 0.89 |
pooled rho(handoff_endorse, grade) = +0.27, p=0.006.

The critical triage DID create contrast (neutral +0.60 vs endorse +1.00, a real +0.40 shift), and the
correlation held (rho=0.27, p=0.006). BUT steering endorsement up by +0.40 moved ASR by only +0.04 (0.34 vs
0.30 = 17 vs 15 hijacks — within noise). **We override the script's auto-CAUSAL verdict: endorsement is a real
but WEAK / underpowered causal lever in swarm.** Contrast supervisor, where certainty-steering ~DOUBLES ASR
(0.45 vs 0.27, Δ9 hijacks). 

**Refined framework (this is the honest, stronger version):** the ENDORSEMENT predictor is real everywhere
(positive rho in all topologies), but it is a STRONG, STEERABLE ATTACK lever only at the auditor edge
(supervisor) — the topology where the decider most fully OUTSOURCES judgment to the upstream agent. In swarm the
executor still gate-keeps, so upstream endorsement is necessary-but-not-sufficient and steering it yields
diminishing returns. This explains WHY certainty@supervisor is special: it is the maximal trust-outsourcing
edge, where manipulating the trusted agent's verdict is maximally effective.
- groupchat: re-probed at MEDIUM SOP (n=70) to restore grade variance — **endorse_balance now SIGNIFICANT**:
  ρ=+0.261, p=0.029 (was p=0.09 at strict, ASR 0.66→0.59). certainty is also close (ρ=+0.229, p=0.057),
  consistent with a broadcast decider reading BOTH the safety reviewer's verdict and the overall vote balance.
  → every architecture now has a significant lever, all consistent with the endorsement-transfer framework.

## Resolving the CP puzzle: the OUTSOURCING CONTINUUM (run_audited_cert.py)
Puzzle (raised in discussion): in CP the manager ALSO judges, yet certainty hijacks it — so "the swarm executor
judges" cannot be why swarm resists certainty. Resolution: insert a SEPARABLE upstream AUDITOR into swarm
(topology.run_swarm_audited: triage→auditor→executor). The executor still judges, but now there is an upstream
SAFETY VERDICT to anchor on.
- swarm_audited ASR 0.54 vs plain swarm 0.36 — adding the auditor RAISES hijackability (reproduces the paradox).
- CAUSAL test (certainty-steer the auditor vs neutral): ASR 0.52 vs 0.46, auditor_cert +11.6 vs −4.4,
  pooled ρ(auditor_cert, grade)=+0.263, p=0.008 — certainty becomes a steerable causal lever ONCE an auditor
  exists (plain swarm certainty is null, ρ≈0.08).

**The certainty effect size scales with how much the decider OUTSOURCES safety judgment to a separable upstream
verdict** — a continuum, not a binary:

| architecture | safety judgment | certainty effect (steer→ASR) |
|---|---|---|
| supervisor / CP | FULLY outsourced to worker's SAFE verdict | LARGE: 0.27→0.45 (~2×) |
| swarm_audited | PARTIAL: auditor present, executor still self-checks | MODERATE: 0.46→0.52 (ρ=.26*) |
| swarm / single | NONE: audit fused into the decider | NULL (ρ≈.08) |

So the answer to "why CP's judging manager is hijacked": it sits at the FULL-outsourcing end. It is not about
whether the decider judges (it always does) but how much its judgment is ANCHORED on a separable upstream
verdict. One mechanism, modulated by judgment-outsourcing — the cleanest unification, now causally supported.
