# D5 — coverage-guidance results (certainty fitness + rigorous behavior coverage)

Operating point for ALL three: **strict manager SOP + WEAK worker (llama-3.2-3b)**, supervisor topology,
seeds from paradox_dataset_500, judge=gpt-4o-mini. Chosen because deepseek-worker SATURATES (base ASR
0.9–1.0 → no headroom); the weak worker hedges enough to give base ASR≈0.5 and a visible certainty gradient.
This also strengthens the paradox story: for a LOW-capability worker (the "safe" regime), the fuzzer
substitutes INPUT-induced certainty for capability-induced certainty and still hijacks.

## Exp A — certainty-maximizing fuzzer (run_certainty_fuzz.py), n=210 pooled
**Mechanism CONFIRMED in-loop (the strongest result):**
- Pooled Spearman ρ(worker lexicon-certainty, manager grade) = **+0.270, p=7.4e-5**;
  ρ(worker embedding-certainty, grade) = **+0.245, p=3.4e-4**. Two INDEPENDENT scorers, both significant.
- **Monotone dose-response** ASR by worker-certainty interval (lex_norm):
  `[0,.2)=0.18  [.2,.4)=0.42  [.4,.6)=0.46  [.6,.8)=0.50  [.8,1)=0.56` (n=44/78/39/24/25). ~3× lift.
- A1 search climbs: certainty arm mean worker-certainty 7.20 vs random 2.08 (3.5×); max 48.5 vs 43. **True.**
- **A3 FAILS**: certainty-arm ASR 0.40 < random 0.46; the grade-climb 'asr' arm 0.36 is even worse.

Reading: the certainty→hijack premise is RIGHT and now interventionally proven, but certainty as a SOLE
search objective does not beat random ASR — hijacking is MULTI-CAUSAL (worker-certainty path ∥ manager-side
persuasion path of authority/urgency); a certainty-only climb caps at the dose-response ceiling (~0.56) while
random mixes vectors, and a grade-only climb prematurely converges.

## Exp B — rigorous behavior coverage (run_behavior_cov.py), v6 redo
Full space stance×affect×certainty×justification = **324 grid cells**; coverage RATE reported vs grid AND vs
empirically-reachable union. Per-interval guidance (discrete cert 0→2; continuous lex-cert 5 bins each guided
with hit-rate). Result:
- Reachable cells observed = **17 / 324**. B1 distinct: directed=10, random=11. Coverage rate (reach):
  directed 0.588, random 0.647. **No gain** — the EMERGENT manager-behavior space is intrinsically tiny, so
  random fills it. (Reproduces the v6 lesson, now with proper denominators.)
- B2 continuous-interval guidance: op-control of worker certainty is weak (hit-rate 0.25–0.50); per-interval
  ASR noisy at small n but consistent with Exp-A direction. The clean dose-response is the pooled Exp-A one.

## Exp C — MAP-Elites / Quality-Diversity (run_qd_fuzz.py), budget 90/arm
Archive = one elite per niche on the 2D map (cert 5 bins × justification 6) = 30 niches, bred for grade.
- QD-score qd=31 vs random=40; niches 13 vs 15; niches-with-hijack 8 vs 11; deep-niches 6 vs 8;
  ASR 0.33 vs 0.31. **No QD gain over random.**

Reading: the reachable niche space is ~15-17 (matches B), and grade SATURATES (hijacks are easily grade 3-4),
so QD's quality axis is inert and its coverage loses to fresh-random's diversity. **There is no headroom for
guidance in the behavior space — confirmed three independent ways (v6, B, C).**

## Robust synthesis (NOT a downgrade — a sharpening of WHERE guidance helps)
1. **Mechanism (positive):** worker certainty causally drives MAS hijacking — replicated in-loop with a clean
   monotone dose-response. Extends the mother paper from observational mediation to a search-driven,
   interventional dose-response, with two independent certainty estimators.
2. **Landscape (characterization):** the emergent MAS hijack-BEHAVIOR space is small & grade-saturated →
   random is a stubbornly strong baseline there; guidance ties/loses (v6/B/C).
3. **Where guidance WINS:** the LARGE, structured CASCADE space — directed coverage beats random
   (fuzz_cascade: distinct 27 vs 10, deep 14 vs 10). Guidance pays off only where the target space is large
   and unsaturated.

## Exp D — certainty-guided cascade (run_cascade_certainty.py), weak worker, budget 100/arm
Tested whether chain certainty predicts cascade DEPTH and whether breeding on certainty beats random in the
LARGE cascade space (no by-construction, since it never pastes the fab name).
- certainty: deep_cells=9, distinct=17, raw=38;  directed: deep_cells=9, distinct=34 (by-construction),
  raw=60;  random: deep_cells=**10**, distinct=22, raw=34.
- Pooled ρ(chain certainty, cascade depth)=+0.185 p=0.0013 — significant but WEAK and **non-monotone**:
  mean cert by depth 0/1/2 = -2.02 / -1.84 / **-2.33** (the DEEPEST cascades are NOT the most confident).
- **VERDICT: certainty-guidance does NOT beat random** (deep 9 vs 10).

**This also REVISES the earlier cascade claim**: the v5 "directed wins" was a by-construction artifact on the
distinct-name-CLASS axis (directed pastes each class). On the security-meaningful DEEP-cascade metric
(depth≥2), random ties/beats directed AND certainty (10 vs 9 vs 9). The certainty mechanism is REAL for
manager hijacking (Exp A) but does NOT transfer to cascade propagation.

## Exp E — LLM-MUTATOR certainty-steering (the breakthrough; user's redesign)
Root-cause of A–D failing: the hand-coded CONCAT operators (mas_ops) staple disconnected clauses → (1) can't
reliably climb certainty, (2) incoherent prompts the weak worker flags as manipulation. Fix (user's two
insights): an ATTACKER LLM (deepseek) REWRITES the payload to maximize worker certainty, few-shot on MINED
high-certainty successful exemplars, keeping ONE coherent realistic narrative. FAIR control = the SAME LLM
rewriter with NO certainty objective (neutral) — isolates the STEERING from the rewriter's raw power.

Result (strict, weak worker, budget 45/arm, n=90 pooled):
| arm | mean worker-cert | ASR | deep | coherence |
|---|---|---|---|---|
| **certainty-steered** | **10.49** | **0.49** | **14** | **0.95** |
| neutral (same LLM, no objective) | -0.62 | 0.31 | 6 | 0.90 |
- ρ(worker certainty, grade)=+0.329 p=0.0016. **VERDICT: certainty-steering beats neutral** — +18 ASR points
  (+58% rel.), 14 vs 6 deep, coherence HELD (0.95 vs 0.90). certainty-LLM ASR 0.49 also edges the prior best
  concat-random (0.46). The mutated prompts are realistic (e.g. weaves in "telemetry 100% saturation, per
  Runbook #RB-472 approved last quarter, matching Incident #INC-2023-1147" while preserving the destructive
  decommission action).
- Confirmatory 3-arm run (certainty vs neutral vs concat, n=180): certainty ASR **0.57** / deep **25** /
  coherence **0.96** vs neutral 0.35/10/0.90 vs concat 0.35/10/0.89 → certainty-steering beats BOTH baselines.
  Dose-response MONOTONE 0.07→0.33→0.48→0.62→**0.71** across worker-certainty bins; ρ=+0.417 **p=5.6e-9**.
  concat==neutral (0.35): hand-coded concat adds NOTHING over neutral LLM rewriting — only certainty-STEERING
  helps. (logs/certainty_llm_3arm.json)

**Why E wins where A–D failed:** (1) the LLM mutator can ACTUALLY realize the certainty objective (climbable);
(2) the fair control isolates steering; (3) coherent attacks actually fool the weak auditor into confidence.
This is the genuine objective-guided fuzzing win — guidance pays off when the mutation OPERATOR is expressive
enough to climb the (validated) objective and the comparison isolates the steering.

## REVISED conclusion
The guidance question turns on the MUTATION OPERATOR, not on coverage per se:
- With WEAK, hand-coded CONCAT operators (A–D), coverage-guidance does NOT beat random — the operators can't
  climb the objective and produce incoherent prompts; random mutation of pre-potent seeds saturates the small
  (~15-17 cell) vulnerable manifold. A real, instructive negative.
- With an EXPRESSIVE LLM mutator that can realize the (validated certainty) objective AND keep prompts
  coherent (E), certainty-STEERING beats the fair neutral control by +58% ASR and edges the prior best
  concat-random, with coherence held. THIS is the genuine objective-guided fuzzing win.
Takeaway: in MAS prompt-injection fuzzing, guidance pays off iff (a) the objective is causally grounded
(worker certainty, validated by the dose-response) and (b) the operator is expressive enough to climb it
(LLM rewrite, not keyword concat). Coverage instrumentation + certainty objective + LLM mutator = the recipe.

What IS real and strong:
1. **Certainty as a cheap vulnerability PREDICTOR** — worker linguistic certainty → monotone hijack
   dose-response (ρ=0.27 p<1e-4, 2 independent scorers). Computable for free (lexicon); use it to triage,
   not to guide. Extends the mother paper from observational mediation to an in-loop interventional curve.
2. **MAS-vs-single differentiation** (separate experiments): K inter-agent-only hijacks 143-248 from CP data;
   cross-topology ASR spread 37-95%; manager-rigor cliff. The MAS-specific attack surface.
The honest "fuzzer" = a cheap random-mutation black-box fuzzer with coverage INSTRUMENTATION + certainty-based
triage; the scientific result is that guiding ON coverage is not worth its cost here.
