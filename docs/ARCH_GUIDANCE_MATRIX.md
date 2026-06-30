# Which guidance for which architecture — the MASFuzzer master table

We fuzz 5 REAL MAS topologies with 3 mutation-guidance strategies and record which guidance maximizes ASR per
architecture. This turns the stage-dependence finding (Exp F/G) into an actionable rule.

**Guidance arms** (same LLM mutator, same budget, identical otherwise — only the rewrite OBJECTIVE differs):
- `certainty` — rewrite so the FIRST agent emits a confident, assertive-"safe" output (the mother-paper
  mediator); breed top-certainty elites. *Calm, low-alarm, scrutiny-EVADING.*
- `recipe` — rewrite using the verified manager-persuasion success conditions (live-attacker reframe, first-
  person commander voice, euphemistic verb, named recovery, strip protocol-citations/exotic-cause; see
  SUCCESS_CONDITIONS.md); breed top-grade elites. *Incident-reframing PERSUASION.*
- `neutral` — same LLM rewriter, NO objective (fair control).

## Master table (homogeneous llama-3.2-3B, strict SOP, seeds=10, budget=36/arm)

`concat` = the historical hand-coded RANDOM-operator baseline (chain 1–3 random attack ops). Included for
fairness because it dominated the early COVERAGE-DIVERSITY experiments — but on ASR it never wins any
architecture (low coherence 0.89, cannot climb certainty); the LLM-guided arms beat it everywhere.

| Architecture | gate structure | certainty | recipe | neutral | concat(random) | **WINNER** | ρ(cert,grade) |
|---|---|---|---|---|---|---|---|
| **single** | one fused decider, no auditor | 0.06 | **0.31** | 0.03 | 0.06 | **recipe** | −0.04 |
| **pipeline** | audit→plan→decide (auditor first) | **0.42** | 0.31 | 0.31 | 0.14 | **certainty** | +0.13 |
| **supervisor** | worker-audit→manager (auditor first) | **0.44** | 0.17 | 0.28 | 0.22 | **certainty** | +0.29 (p=.002) |
| **swarm** | triage→specialist→executor | 0.36 | **0.50** | 0.31 | 0.36 | **recipe** | −0.07 |
| **groupchat** | analyst/ops/safety broadcast→decide | 0.69 | **0.83** | 0.58 | 0.67 | **recipe** | +0.10 |

**On `random`/concat:** it was "strongest" only on the COVERAGE-DIVERSITY metric (distinct behavior/cascade
cells) — random op-chaining spreads wide. On ASR (the bug-finding metric that matters) it is the WEAKEST guided
arm: never wins a cell, and on the auditor-gated `pipeline` it sinks to 0.14 (below neutral 0.31) because its
`threat`/`authority` ops ALARM the auditor. LLM-guided certainty/recipe dominate it on every architecture.

## Strong-decider variant (Exp ③: swarm/groupchat with a deepseek decider, weak upstream agents)
Re-running the two recipe-winning NON-auditor topologies with a STRONG decider tests rule ③:

| Architecture (strong decider) | certainty | recipe | neutral | concat | **WINNER** | vs weak-decider |
|---|---|---|---|---|---|---|
| **swarm** | **0.72** | 0.47 | 0.61 | 0.69 | **certainty** | FLIPPED (was recipe 0.50>cert 0.36) |
| **groupchat** | 0.42 | 0.44 | 0.31 | — | recipe≈cert | recipe edge collapses (was 0.83 vs 0.69) |

swarm **cleanly flips**: a capable decider scrutinizes, so certainty (0.72) wins and recipe BACKFIRES below
neutral (0.47 < 0.61) — exactly as on the strong supervisor manager (Exp b). groupchat (broadcast mesh) only
partly follows: with a strong decider both arms collapse toward ~0.43 (the decider reads the full debate
including the safety reviewer), so the recipe's broadcast advantage evaporates but no clean certainty win
emerges. Confirms rule ③ for chain/handoff topologies; broadcast is the resistant case.

## The rule
**Certainty-steering wins IFF a SCRUTINIZING evaluator sits in the decision path; otherwise the incident-
reframing recipe wins.**
- `supervisor`, `pipeline` route the payload through a Llama-Guard **security AUDITOR** whose certainty gates
  the decision → calm confident-"safe" framing (certainty) makes the auditor wave it through; the recipe's
  live-attacker framing ALARMS the auditor (trips S14/S15) and LOSES (supervisor recipe 0.17 < neutral 0.28).
- `single`, `swarm`, `groupchat` have NO dedicated security auditor; weak agents act on the incident frame
  rather than auditing the security claim → the persuasion recipe wins, and certainty-steering gives little
  (single 0.06; in groupchat/swarm certainty doesn't even climb — mean_lex negative).
- groupchat (broadcast mesh) is the MOST hijackable topology overall (0.58–0.83); recipe adds the most.

## Decider capability — the recipe is a DOUBLE-EDGED sword (Exp b: manager-gated, STRONG decider)
Relay (non-auditing) worker + **strong deepseek manager**, strict SOP, budget=48 (n=144):

| arm | ASR | mean_lex | note |
|---|---|---|---|
| certainty | **0.85** | 29.77 | evades the capable manager's scrutiny |
| neutral | 0.79 | 0.94 | base already high (strong mgr complies w/ potent payloads) |
| recipe | **0.54** | 0.48 | **BACKFIRES −0.25 vs neutral** — attacker-framing invites scrutiny |

Dose-response monotone 0.40→0.70→0.71→0.80→**0.93** (ρ=+0.25, p=.003). A capable manager SCRUTINIZES like an
auditor: the recipe's live-attacker frame makes it MORE careful (0.54), while calm confident-"safe" certainty
evades it (0.85). Contrast the WEAK strict decider (`single`, llama-3.2-3B) where the SAME recipe WINS (0.31 vs
certainty 0.06) — weak agents are persuaded by the incident frame, not alarmed by it.

## Unifying principle + guidance-selection rule
The recipe's attacker-reframing is **persuasive to naive agents but ALARMING to scrutinizing ones**.
Certainty-steering (confident-safe, low-alarm) is the **scrutiny-evading** lever that wins wherever a careful
evaluator gates. So:
1. Architecture has a security AUDITOR in path (supervisor, pipeline) → **certainty-steering**.
2. No auditor AND decider is weak/compliant (single/swarm/groupchat on small models) → **recipe**.
3. No auditor BUT decider is a capable model → **certainty-steering** (recipe backfires on it).
**Against any scrutinizing evaluator, EVADE with confident-safe framing; against a compliant one, PERSUADE
with incident-reframing.** The architecture + decider capability pick which lever — that is the table's payoff,
and a STAGE/SCRUTINY-AWARE attack-synthesis result no prior MAS fuzzer reports.
