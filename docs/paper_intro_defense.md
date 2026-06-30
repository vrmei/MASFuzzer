# Abstract / Introduction / Defense / Ethics (draft prose)

## Abstract (4-sentence structure)
[1] Multi-agent LLM systems (MAS) increasingly authorize consequential actions, and a recent measurement
showed a *capability paradox*: a more capable auditor agent can make such a system *more* hijackable, mediated
by the auditor's linguistic certainty. [2] Yet existing fuzzers for these systems are either white-box and
reliability-oriented (FLARE) or single-agent (AgentVigil), and quality-diversity red-teaming optimizes
input-side descriptors against a single model — none guides search by the *causal mechanism* of the hijack.
[3] We present MASFuzzer, a black-box, coverage-guided fuzzer that steers an LLM mutation operator to climb the
auditor's output certainty — the mechanism the mother paper identified — and selects its guidance by whether a
scrutinizing evaluator gates the decision. [4] Certainty-steering roughly doubles attack success over a fair
same-LLM baseline (0.45 vs 0.27 ASR, non-overlapping error bars over 3 seeds at n=216/arm) while preserving narrative
coherence, with a replicated dose-response (ρ=0.42, p<1e-6) in the Manager-Worker topology; a multi-seed
cross-architecture sweep shows the advantage is specific to the auditor→manager edge (a stable certainty win in
the supervisor topology, with no stable guidance winner in any other architecture), and we contribute an
adversarially-verified taxonomy of the framings that make such attacks succeed across 14 manager models.

## Introduction (funnel)

**Para 1 — background → problem.** LLM multi-agent systems now triage incidents, write to databases, and call
infrastructure tools with limited human oversight. A central safety assumption is that an upstream auditor or
reviewer agent will catch a malicious or mistaken request before a decider acts on it. The capability paradox
[liu2026capabilityparadox] unsettles this assumption: a *more* capable auditor can make the system *more*
hijackable, because a confidently-worded "safe" verdict is precisely what persuades the decider to comply —
a failure mode they term *semantic hijacking*, mediated by the auditor's linguistic certainty.

**Para 2 — why it is hard / why prior work is insufficient.** Turning this observation into a systematic attack
generator is non-trivial and unaddressed. White-box MAS fuzzers (FLARE [flare2026]) need agent source and target
functional reliability, not security; single-agent prompt-injection fuzzers (AgentVigil [agentvigil2025]) do not
model the multi-agent decision path; and quality-diversity red-teaming (Rainbow Teaming [rainbow2024], QDRT
[qdrt2025], Curiosity-RT [curiosity2024]) searches input- or behavior-side descriptors against a single model.
None steers by the causal mediator of the failure, and none asks how the right attack depends on the MAS
architecture and the scrutiny of the deciding agent.

**Para 3 — our approach.** We make the mediator the fuzzing fitness. MASFuzzer is black-box — it observes only
agents' text — and an attacker LLM rewrites the request to *raise the auditor's output certainty* while
preserving a coherent incident narrative, hill-climbing this continuous, causally-grounded signal. Because the
certainty mechanism bites at the auditor→decider edge, we ask where across MAS architectures the lever pays off,
and find — honestly — that it dominates exactly one topology: the canonical Manager-Worker (auditor→manager)
edge the mediator lives on.

**Para 4 — contributions.**
1. We turn the capability-paradox mediator into a fuzzing fitness and confirm, *in the attack loop*, a
   significant certainty→hijack dose-response (ρ=0.42, p<1e-6 within the Manager-Worker topology; positive and
   monotone through the populated range pooled at scale) — strengthening the mediator evidence in the full-MAS
   regime where the original study found it weakest.
2. We build a black-box, mechanism-grounded LLM-mutation fuzzer whose certainty-steering roughly doubles ASR
   over a fair same-LLM baseline (0.45±.05 vs 0.27±.02, non-overlapping over 3 seeds at n=216/arm) with
   coherence held (0.94).
3. From 500 payloads × 14 manager models we mine and *adversarially verify* the framings that make attacks
   succeed (live-attacker reframe, commander voice with forensic certainty, euphemized verb, false reversibility,
   third-party stakes) — and show coarse categories and input-text certainty do *not* predict success.
4. We sweep five MAS architectures with multi-seed and multi-scale error bars and honestly bound where
   certainty-steering generalizes: it is the stable winner in exactly one topology — the supervisor (auditor→
   manager) edge (4/4 configs across two scales) — while every other architecture yields no stable guidance
   winner. The advantage is auditor-edge-specific, not a universal cross-architecture rule, which itself tells a
   defender precisely which topology to harden.

## Defense (mechanism → mitigation)
The attack exploits a single trust relationship: deciders *defer to confidently-worded auditor verdicts*. Our
results point to defenses at that relationship, not at agent capability (raising capability makes it worse).
- **Certainty-decorrelated decision policy.** Instruct/train the decider so that an auditor's expressed
  confidence does not increase compliance; weight the decision on independent evidence and treat an unusually
  assertive "all-clear" as a *yellow flag* rather than reassurance. (Directly targets the ρ=0.42 channel.)
- **Independent re-derivation.** Require the decider to re-derive the safety judgment from the raw request and
  tool semantics, not from the auditor's summary — removing the single-point certainty channel.
- **Steering-signature detection.** Monitor for the mined attack signatures — anomalously high auditor
  certainty co-occurring with a euphemized destructive verb, an omitted loss-disclosure, and a live-attacker
  frame — as an injection detector (the success-condition taxonomy doubles as a defense feature set).
- **Gate-aware hardening.** The supervisor (Manager-Worker) topology is where certainty-steering most reliably
  succeeds; it should receive the strongest decider-side certainty-skepticism. Hardening belongs at the
  certainty-trust policy (the ρ=0.42 channel), not at agent capability — raising auditor capability is what
  creates the paradox in the first place.

## Limitations (honest)
- **Operating point.** Our regime is a strict decision SOP with a weak auditor, chosen because it yields an
  *intermediate* ASR where guidance can discriminate; a permissive SOP saturates ASR→1 and a fully robust one
  drives it to 0. Results characterize the discriminating regime, not all deployments.
- **Model and topology scope.** Weak agents are Llama-3.2-3B, the strong decider and attacker are DeepSeek-V3,
  and the oracle is gpt-4o-mini; we abstract five topologies homogeneously rather than instrumenting full
  AutoGen/CrewAI/LangGraph deployments. Broader model and framework sweeps remain.
- **Partial cross-architecture generalization.** The certainty win is robust in the supervisor (Manager-Worker)
  auditor topology and reactivated by a capable decider, but is marginal (pipeline), tied with the recipe
  (groupchat), or null (weak swarm) elsewhere — we report this rather than a blanket rule. Some MIXED cells
  still have wide error bars at 2–3 seeds.
- **Descriptive recipe.** The mined success-condition *recipe* operator does not robustly beat certainty in any
  multi-agent topology; we present it as a verified *characterization* of cross-manager success and as a
  detection feature set, not as a superior mutation operator.
- **Success-condition mining.** Cross-manager success rates come from existing logs with a single fixed worker
  (Llama-3.1-8B); the verified framings should be re-checked across worker models.
- **Certainty estimator.** We guide on the validated lexicon construct; the embedding and judge estimators are
  secondary and used for validation, not steering.

## Ethics & responsible disclosure
- **No real systems.** All experiments run on a synthetic corpus of hypothetical SRE incidents against models
  via a research API; no real infrastructure, credentials, or deployed agent is targeted.
- **Dual-use, net-defensive.** MASFuzzer is an attack synthesizer, but the same mechanism yields the defenses
  above; we release the defense recipe and detection signatures alongside, and argue the net effect is to let
  MAS builders test and harden the certainty-trust channel before deployment.
- **Disclosure.** We coordinate with the maintainers of the agent frameworks whose topologies we model before
  release, and withhold any turnkey end-to-end exploit script.
- **LLM-assistance disclosure.** We disclose any LLM assistance in writing per venue policy; all reported
  numbers come from logged runs with fixed seeds.
