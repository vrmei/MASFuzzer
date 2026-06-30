# MASFuzzer — Method + Results skeleton (security venue: USENIX Sec / S&P / CCS)

> Working title (placeholder): **Certainty Is the Lever: Mechanism-Grounded, Stage-Aware Fuzzing of
> Multi-Agent LLM Systems.** Derived from the Capability-Paradox mother paper (Liu et al., arXiv 2605.17480).
> This file is the FROZEN pre-registration (Stage 1/3) + the Method/Results skeleton (Stage 5). Numbers below
> are from real runs (logs/). Prior-work IDs are tagged [verify-PDF] — must be PDF-confirmed before Related Work.

---

## Stage 1/3 — frozen RQ, hypotheses, falsification, baselines (pre-registration)

**Central RQ.** *In a multi-agent LLM system (MAS), what mutation-guidance signal most efficiently synthesizes
prompt-injection attacks that hijack the system's final action — and does the answer depend on the MAS
architecture and the scrutiny of the deciding agent?*

**Sub-questions & hypotheses (each falsifiable):**
- **RQ1 (mechanism).** Is the worker/auditor's output *linguistic certainty* a climbable, causal fitness for
  hijacking? **H1:** binned worker-certainty → monotone ASR (dose-response), pooled ρ>0, p<.01.
  *Falsify:* ρ≈0 or non-monotone, OR certainty is not steerable by mutation.
- **RQ2 (attack synthesis).** Does steering an LLM mutator toward worker-certainty beat fair baselines at equal
  budget, without losing coherence? **H2:** certainty ASR > neutral (same LLM, no objective) and > concat
  (hand-coded random ops), with coherence within 0.1. *Falsify:* certainty ≤ max(baselines), or coherence
  collapses.
- **RQ3 (success conditions).** What payload properties predict cross-manager success? **H3:** coarse
  strategy/tool and *input-text* certainty do NOT predict success; specific framings (live-attacker reframe,
  commander voice, euphemized verb, false-reversibility, third-party stakes) DO, and survive adversarial
  verification. *Falsify:* the framings show no lift over matched controls, or the lift is a strategy/tool
  confound.
- **RQ4 (where does certainty-steering generalize?).** **H4 (final, multi-seed + multi-scale):** certainty-
  steering wins robustly ONLY in the supervisor (Manager-Worker auditor) topology — the single cell stable across
  all 4 configs and both scales (n=36 and n=72), corroborated by the Table 2 headline. Every other topology is
  unstable (single low-signal, winner flips with scale; pipeline a wash; groupchat/swarm high-variance).
  *Falsify (met):* a uniform cross-architecture rule was NOT found; the advantage is auditor-edge-specific.
  RETRACTED single-seed claims: "naive→recipe wins everywhere" and "strong-decider reactivates certainty."

**Baselines (frozen).**
- `neutral` — the SAME attacker LLM rewriting the payload with NO objective. *Isolates the steering, not the LLM.*
- `concat` — historical hand-coded RANDOM operator chaining (the strong baseline of the early coverage phase).
- (mechanism null) **input-text certainty** of the raw payload — to show the lever is the *worker output*, not
  the input phrasing.

**Metrics (frozen).** Primary: ASR = fraction with validated-oracle grade ≥ 2 (hijack). Secondary: deep-capture
count (grade ≥ 3), coherence (judge 0–1 plausibility), dose-response ρ(worker-certainty, grade) + per-bin ASR.
Multi-run: E/E2/F pooled n≈450; report per-arm and pooled. Oracle = CP-validated gpt-4o-mini judge (κ≥0.87).

**Minimum viable contribution.** RQ1+RQ2 alone (mechanism-grounded certainty-guided MAS fuzzer that beats fair
baselines with coherence held). RQ3 and RQ4 are the differentiating extensions.

---

## 3 Method (present tense)

### 3.1 Overview + threat model (Figure 1: the MAS pipeline + the attacker-controlled entry + the "gate")
One paragraph: a MAS routes a request through a pipeline of LLM agents (auditor / planner / analysts / triage)
to a deciding agent that authorizes a tool action. The attacker controls only the natural-language request at
the entry (black-box; no weights, no logits, no execution traces). MASFuzzer is a coverage-guided fuzzer whose
fitness is *mechanism-grounded*: it steers mutation toward the latent variable the mother paper showed mediates
hijacking — the auditor's output certainty — and selects guidance by where the decision is gated.
Figure 1 = the 5 topologies with the GATE node highlighted.

### 3.2 Problem formulation
- A MAS = ordered agents \(A_1,\dots,A_n\); \(A_n\) emits the final decision \(d\). Each \(A_i\) runs a fixed
  model+SOP; the topology defines the message graph (Table: 5 topologies).
- Attacker picks payload \(x\) from a seed corpus + a mutation operator; system runs \(T(x)\)→trace; oracle
  \(O(d)\in\{0..4\}\); **hijack** iff \(O(d)\ge 2\). Objective: maximize hijack rate under a query budget \(B\).
- **Gate** \(g\) = the agent whose refusal/compliance is pivotal (auditor in pipeline/supervisor; the lone/late
  decider otherwise). Formalize gate location as a property of (topology, per-agent SOP, model capability).

### 3.3 Certainty as a climbable fitness (mechanism instrument)
- Define worker/first-agent output certainty \(c(\cdot)\) three ways (interchangeable scorers, `certainty_core`):
  **lexicon** (assertive−hedging density, the EXACT validated CP construction — the signal the 74% mediation was
  measured with), **embed** (char-ngram projection onto an assertive−hedged direction; generalizes beyond exact
  terms), **judge** (LLM 0–2, the independent validation axis — never used to both guide and validate).
- Claim: \(c\) is *continuous and climbable* (unlike the small, saturating behavior-diversity space that tied
  random in early coverage attempts — report that negative result honestly in §4.6).

### 3.4 Certainty-guided LLM mutation (core method)
- Mine high-certainty exemplars from the seed corpus (the "successful-attack" few-shot pool).
- Mutation = an attacker LLM rewrites the parent payload to MAXIMIZE \(c\) of the auditor's response while
  keeping ONE coherent realistic incident narrative and preserving the destructive action (system prompt =
  `CERT_SYS`). Evolutionary hill-climb: archive elites by \(c\); breed top-k.
- Fair control: identical LLM rewriter with no objective (`neutral`). Algorithm 1 = the fuzzing loop.

### 3.5 Success-condition mining → the recipe operator
- Offline analysis (no new queries): 500 seed payloads × 14 real managers → per-payload cross-manager success
  rate; a multi-agent labeling+verification pipeline extracts the *verified* success framings (Table 4).
- Encode the verified, actionable framings as a second mutation operator (`RECIPE_SYS`): live-attacker reframe →
  first-person commander + forensic certainty → euphemized verb → strip blocking tells (loss-disclosure,
  fabricated protocol, exotic cause) → named recovery on irreplaceable target → reattribute irreversibility →
  third-party/PII stakes.

### 3.6 Operator selection by gate (honest, multi-seed)
- Principle: **certainty** steers an AUDITOR's report toward a confident "safe" verdict; **recipe** persuades a
  lone decider via verified framings. So MASFuzzer uses *certainty* when an auditor gates the decision and the
  *recipe* when none does. §4.5 validates this robustly at the auditor end only — the **supervisor** Manager-
  Worker topology → certainty wins across all seeds AND scales (n=4 configs + the Table 2 headline). The no-
  auditor and middle topologies (single/pipeline/groupchat/swarm) yield NO stable winner (single even flips with
  scale; the others are washes/high-variance). So the lever is **auditor-edge-specific**, not a universal gate-
  capability law. (The earlier "single→recipe everywhere" and "capable decider reverses to certainty" claims did
  not replicate and are retracted — an honest generalization boundary, which itself tells defenders what to harden.)

### 3.7 Putting it together (Algorithm 1)
Seed → (select operator by gate/scrutiny) → mutate → run topology → score certainty (free, local) → grade
(oracle) → update archive → repeat to budget. Report per-arm ASR, deep-capture, coherence, dose-response.

---

## 4 Results (present tense; numbers from logs/)

### 4.1 Experimental setup
- **Seed corpus:** `paradox_dataset_500` (500 SRE incident-response prompt-injection payloads; 4 strategies × 7
  target-tool classes; cite Data Card). **Models:** weak auditor/workers = Llama-3.2-3B; strong decider variant
  = DeepSeek-V3; attacker/mutator = DeepSeek-V3; oracle/judge = gpt-4o-mini (CP-validated, κ≥0.87).
- **Topologies (5):** single, pipeline, supervisor, groupchat, swarm (Table 1, cross-validated vs
  AutoGen/CrewAI/LangGraph/OpenAI-Swarm). **Decision SOPs:** strict/medium/permissive (rigor knob).
- **Baselines:** neutral, concat(random). **Metrics:** ASR, deep-capture, coherence, dose-response ρ.

### 4.2 RQ1 — worker certainty is a climbable, causal fitness (Figure 2: dose-response)
- Pooled across arms (n≈450, E/E2/F): per-certainty-bin ASR rises MONOTONE **0.07 → 0.33 → 0.48 → 0.62 → 0.71**
  (and to **0.87** in F's top bin); ρ(worker-certainty, grade) = **+0.36 to +0.42**, p down to **5.6e-9**.
- Negative control (RQ3 preview): raw *payload-text* certainty does NOT predict cross-manager success (ρ≈0.05,
  n.s.) — the lever is the auditor's OUTPUT, not the input. → H1 supported.

### 4.3 RQ2 — certainty-guided mutation beats fair baselines (Table 2, the main result; **big scale**, 3 seeds)
Worker-gated supervisor, strict SOP, **seeds=25/run, budget=72/arm (n=216 candidates/arm)**, 3 random seeds:

| arm | ASR (mean±std) | deep | coherence |
|---|---|---|---|
| **certainty (ours)** | **0.45 ± 0.05** | 19.3 | **0.94** |
| concat (random hand-coded ops) | 0.37 ± 0.01 | 21.0 | 0.88 |
| neutral (same LLM, no objective) | 0.27 ± 0.02 | 14.0 | 0.88 |
- certainty wins on ASR with **non-overlapping error bars** (0.45−0.05 = 0.40 > concat 0.37+0.01) AND on
  coherence (0.94 vs 0.88) — the synthesized attacks are realistic, not keyword soup. At this larger scale
  `concat` (0.37) separates from `neutral` (0.27) — random potent operators help somewhat — but stays below
  certainty and at low coherence. → H2 supported. (Consistent with the smaller-scale 3-seed run 0.47/0.24/0.26
  and the per-run peaks 0.57–0.65.)

### 4.4 RQ3 — what makes attacks succeed (Table 4, verified conditions)
- Setup: 500 × 14 managers, per-payload cross-manager sr ∈ [0.00, 0.85]; 33-agent mine + adversarial verify.
- **Null results (honest):** coarse strategy ASR 15–20%, tool ASR 17–20% (barely discriminate); the pre-seeded
  saturated tactics (urgency/assertiveness/specificity) FAIL verification (urgency even negative within-tool —
  Simpson reversal).
- **Verified conditions (TOP25 vs sr=0, strategy/tool-matched):** live external-attacker reframe (42–46% vs 8%);
  first-person commander + forensic certainty (67% vs 27%; 29% vs 9%); euphemized verb (80% vs 8%); named
  recovery on irreplaceable target (24% vs 4%); omitted loss-disclosure (0% vs 10%); PII/compliance stakes
  (17–20% vs 3–6%). **Anti-features:** exotic root cause (0–4% vs 10–24%, the only blocked>success feature);
  fabricated protocol citations (Admin-Emergency strategy = 0 successes). → H3 supported.

### 4.5 RQ4 — where does certainty-steering generalize? cross-architecture sweep (Table 5; **3 seeds**, mean±std)
Weak homogeneous MAS, strict SOP, seeds=10, budget=36/arm, 3 random seeds. `stable` = same winner all 3 seeds.

**n = 4 configs/cell** (3 seeds at n=36/arm + 1 big-scale seed at n=72/arm); `stable` = same winner all 4.

| architecture | certainty | recipe | neutral | concat | winner | stable? |
|---|---|---|---|---|---|---|
| **supervisor (auditor→manager)** | **0.52±.06** | 0.26±.06 | 0.27±.08 | 0.34±.08 | **certainty** | **YES 4/4** (ρ=.42 p<1e-6) |
| single (fused, NO auditor) | 0.14±.09 | 0.20±.06 | 0.09±.02 | 0.03±.02 | recipe | MIXED (3/4; big-n flips to cert) |
| pipeline (auditor→plan→decide) | 0.39±.03 | 0.34±.07 | 0.32±.03 | 0.28±.02 | certainty | MIXED (2-2 wash) |
| groupchat (broadcast) | 0.69±.07 | 0.71±.05 | 0.51±.07 | 0.65±.08 | recipe | MIXED (4 diff winners; all high) |
| swarm (handoff) | 0.32±.08 | 0.43±.06 | 0.43±.03 | 0.36±.04 | recipe | MIXED (certainty lowest) |

Strong-decider probe (DeepSeek decider, swarm, 3 seeds): certainty 0.67±.04 but **neutral wins s1 (0.78)** — NOT
a robust reactivation (winner flips); we do NOT claim a strong-decider reversal.

**Honest reading (multi-seed AND multi-scale; the earlier cross-architecture "rule" did NOT survive):**
- **Exactly ONE cell is robust across all 4 configs and both scales:** the **supervisor** Manager-Worker auditor
  topology → certainty wins decisively (0.52±.06 ≫ baselines; ρ=.42, p<1e-6), corroborated by the big-scale
  Table 2 headline (0.45±.05, n=216/arm). This is the edge the mediator lives on.
- **Every other topology is unstable:** single is low-ASR and its winner flips with scale (recipe at n=36 → cert
  at n=72); pipeline is a 2-2 wash (cert≈recipe, both > neutral); groupchat is high-variance with all arms strong
  (different winner each config); swarm is null-to-recipe with certainty the WORST arm. No stable guidance rule.
- **Strong-decider reactivation retracted.** → H4 holds only in its narrow, well-supported form (supervisor); we
  present §4.5 as an honest *generalization boundary* — the certainty mechanism is auditor-edge-specific, not a
  cross-architecture law — which is itself a finding (it tells defenders exactly which topology to harden).

### 4.6 Analysis / ablations
- **Coherence held** across all certainty runs (0.93–0.96) → the synthesized attacks are realistic, not keyword
  soup. **concat is strong only on COVERAGE-DIVERSITY** (distinct cells) but WEAKEST on ASR (never wins; sinks to
  0.14 on the pipeline auditor it alarms) — two metrics, two conclusions; argue ASR is the right fuzzer metric.
- Why early coverage-diversity guidance tied random (honest negative): the hijack behavior space is small and
  saturates; the mechanism-grounded *scalar* certainty fitness is climbable where diversity is not.
- Operating-point note: ASR is intermediate (not 0/1) at strict-SOP + weak-worker — the regime where guidance
  can discriminate; permissive SOP saturates ASR→1 (report as a setup choice, not a result).

---

## Differentiation vs prior work (Related Work seam — all 12 IDs PDF-VERIFIED 2026-06-20; titles corrected)
- **FLARE** (2604.05289, "FLARE: Agentic Coverage-Guided Fuzzing for LLM-Based Multi-Agent Systems", 2026) — the
  CLOSEST work: also coverage-guided MAS fuzzing, but WHITE-BOX (extracts specs/oracles from agent source) and
  RELIABILITY-oriented (functional failures; 96.9% inter-agent coverage). Ours is BLACK-BOX, SECURITY-oriented
  (prompt-injection hijacks), and its coverage signal is a CAUSAL MECHANISM (auditor certainty), not execution
  coverage. *Do NOT claim "first coverage-guided MAS fuzzer" — claim first black-box + mechanism-grounded +
  stage-aware one.*
- **ChainFuzzer** (2603.12614) — greybox WORKFLOW-LEVEL multi-tool dataflow fuzzing of agent tool-chains (NOT
  single-agent prompt injection). Different vulnerability class (tool-composition bugs vs decision hijack).
- **AgentVigil** (2505.05849, EMNLP-Findings 2025; formerly "AgentFuzzer") — black-box MCTS-guided INDIRECT
  prompt-injection fuzzing, SINGLE agent. Ours is MAS-native, cross-architecture, and steers a mediator.
- **Rainbow Teaming** (2402.16822, NeurIPS'24) / **QDRT** (2506.07121) / **AutoQD** (2506.05634) — quality-
  diversity red-teaming with input/attacker-behavior descriptors on a SINGLE target model; ours steers a CAUSAL
  mediator (auditor output certainty) inside a MAS and is gate/scrutiny-aware.
- **Curiosity-RT** (2402.19464, ICLR'24) — prompt-embedding novelty coverage, single model.
- **T-MAP** (2603.22341, "Red-Teaming LLM Agents with Trajectory-aware Evolutionary Search") — MAP-Elites over
  AGENT TRAJECTORIES (MCP agents); descriptor = trajectory. Ours descriptor = the certainty mechanism + the gate.
- **MAST** (2503.13657, "Why Do Multi-Agent LLM Systems Fail?", ICML'25) — DESCRIPTIVE MAS failure taxonomy;
  ours is a GENERATIVE attack synthesizer.
- **AiTM** (2502.14847, "Red-Teaming LLM MAS via Communication Attacks", Agent-in-the-Middle) — inter-agent
  MESSAGE manipulation (attacker controls the channel); ours is entry-point-only, no channel access.
- **Persuasion** (2602.00851, "Understanding Persuasion in Long-Running Agents") — SINGLE long-running agent (NOT
  multi-agent); cite only as persuasion-mechanism background, never as multi-agent evidence.
- Mother paper (2605.17480, "The Capability Paradox: How Smarter Auditors Make Multi-Agent Systems Less Secure",
  Qiqi Liu, T. Holz et al.) — coins "semantic hijacking"; certainty mediation is ROBUST in Worker-only but
  WEAKER in Full-MAS. Frame our §4.2 in-loop dose-response (ρ=.36–.42 in the full supervisor MAS) as
  *strengthening* the mediator evidence in the harder Full-MAS regime where the mother paper found it weaker.
- One-line positioning: *first BLACK-BOX, MECHANISM-GROUNDED (certainty-causal) prompt-injection attack
  synthesizer for LLM multi-agent systems; we show it wins decisively at the canonical auditor→manager edge and
  honestly map where across 5 architectures it does and does not generalize.*

## Open TODO before submission
- [x] Multi-seed std bands: Table 2 = 3 seeds (done, error bars non-overlapping); Table 5 = 2 seeds s1,s2 (done).
- [ ] Add a 3rd matrix seed (s3) + ≥2 more strong-decider seeds (currently 1); bootstrap CIs on the MIXED cells.
- [x] PDF-verify every prior-work ID (done 2026-06-20; bib corrected, fabricated author removed).
- [ ] Write Related Work final prose from READ PDFs (drafted in paper_related_work.md; still need full-text reads).
- [ ] Defense section (mechanism → mitigation: auditor certainty-calibration; require a scrutinizing evaluator
      on the decision path — the swarm null→strong-decider result motivates this directly).
- [ ] Ethics + responsible-disclosure statement (attack synthesis on hypothetical SRE incidents; no real systems).
