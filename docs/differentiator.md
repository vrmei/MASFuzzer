# Differentiator — Direction 5: Security-oriented MAS fuzzing (HUB)

## One-line RQ
Can a coverage/feedback-guided MAS fuzzer with a **security oracle** (goal hijack / trust-boundary
violation / cascading hallucination / system-level ASR) and **attack-semantic inter-agent mutation
operators** (hijack-narrative mutation, tool-output poisoning, observation injection, inter-agent
message/protocol mutation) discover security failures that FLARE's reliability oracle marks PASS,
and inter-agent failures that single-agent fuzzers (AgentFuzzer / ChainFuzzer) cannot reach?

## Hypothesis
On N MAS apps the framework finds **M** failures that FLARE's functional oracle labels PASS, and
**K** inter-agent trust-boundary / cascading-hallucination failures unreachable by single-agent
AgentFuzzer / ChainFuzzer.

## Falsification criterion (sharp — a result that kills the direction)
If **EITHER**:
1. every security failure found is *already* caught by FLARE's functional oracle (i.e. M = 0, no
   PASS→security-fail cases — the security oracle is redundant with reliability), **OR**
2. every finding is reachable by single-agent AgentFuzzer / ChainFuzzer (K = 0, no genuinely
   inter-agent failure — the multi-agent target buys nothing),

then the framework has **no independent value → DEAD**. Both M > 0 and K > 0 must hold to live.

## VERDICT (faithful, including the narrowed parts)
**STRONGEST / hub. ALIVE; the four-property combination is OPEN — but NO LONGER greenfield.** The
honest narrative is *not* "first MAS fuzzer." It is **"first coverage/feedback-guided MAS fuzzer with
a SECURITY oracle and attack-semantic INTER-AGENT mutation operators,"** and it must differentiate
against **three named neighbors at once** (reviewers will know them):

- **FLARE** (2604.05289) — same MAS-fuzzing substrate, but a *reliability* oracle (spec deviation,
  loops, failed tool calls), benign mutation, and prompt injection *explicitly out of scope*.
- **ChainFuzzer** (2603.12614) — a *security* greybox fuzzer with sink oracles + payload mutation,
  but *single-agent multi-tool* source-to-sink, not multi-agent.
- **AgentFuzzer / AgentVigil** (2505.05849, Dawn Song) — MCTS black-box fuzzer, oracle = indirect
  prompt-injection success, but *single-agent*, mutating injected prompts not the inter-agent
  protocol.

Multi-agent *security* work exists only as **fixed attacks/analyses** (FuncPoison 2509.24408 cross-
agent hijack propagation; TOMA 2512.04129 topology-aware multi-hop), **not as a fuzzing search**.
The terrain is **open-in-combination but crowded at the edges** — partially-occupied, not greenfield.

## Nearest incumbent + precise diff
- **vs FLARE (nearest, same substrate):** keep the MAS-fuzzing loop; **swap reliability oracle →
  security oracle** and **benign mutation → attack-semantic inter-agent mutation**. The whole claim
  rests on showing PASS→security-fail cases FLARE's oracle misses by construction.
- **vs ChainFuzzer / AgentVigil:** **lift the security oracle from single-agent to the MULTI-AGENT
  level**, where the *novel* oracles live — inter-agent trust-boundary crossing, cascading
  hallucination, system-level ASR over an agent handoff — which have no single-agent analogue.
- **vs FuncPoison / TOMA:** turn **fixed hand-crafted attacks into a coverage/feedback-guided
  fuzzing search** that discovers new instances rather than demonstrating one.

## Oracle design (the commanding height — concrete, auto-decidable)
1. **Goal hijack** — final behavior deviates from the original user goal. Auto via goal-embedding /
   task-completion judge comparing achieved-state to original-goal-state.
2. **Authorization / trust-boundary crossing** — a tool outside the trust boundary is invoked.
   **REUSE the mother-paper Grade ≥ 2 rubric** (κ ≥ 0.87 methodology) as the oracle.
3. **Cascading hallucination** — one agent's hallucination is accepted and amplified downstream.
   **FOLDS DIRECTION 2**: an out-of-library tool fabricated by agent A is called by agent B. Auto-
   detect via library-membership + downstream-propagation check.
4. **Deadlock / loop** — FLARE already covers this; **EXPLICITLY do not duplicate.**

## Architecture comparison (item 5.8)
| Axis | FLARE (2604.05289) | ChainFuzzer (2603.12614) | AgentFuzzer (2505.05849) | **This proposal** |
|---|---|---|---|---|
| Target | multi-**agent** | single-agent, multi-**tool** | **single-agent** | multi-**agent** |
| Input mutation strategy | benign input perturbation | sink-targeted payload mutation | MCTS over injected prompts | **attack-semantic inter-agent ops** (hijack-narrative, tool-output poisoning, observation injection, message/protocol) |
| Coverage / feedback signal | agent-interaction coverage | source-to-sink dataflow | injection-success reward (MCTS) | **agent-interaction + trust-boundary-crossing + propagation coverage** |
| Oracle type | **reliability** | **security** (sink) | **security** (injection) | **security** (multi-agent) |
| Failure classes | spec deviation, loops, failed tool calls | tool-sink vulns | indirect prompt injection | **goal hijack, trust-boundary crossing, cascading hallucination, system-level ASR** |
| Adversarial-oriented? | NO (PI explicitly out of scope) | YES (intra-agent) | YES (single-agent) | **YES (inter-agent)** |

## Hub role
This direction **absorbs Direction 2** (cascading-hallucination class = hallucinated-tool squatting,
become a security-oracle signal) and **Direction 1** (confidence steering, become either a mutation
operator or an oracle/feedback signal). It is the strongest because it is the integration point.

## Honest risk register
- **Edge-crowding risk:** three strong neighbors means reviewers will demand the diff be *measured*,
  not asserted — hence the falsification ties survival to M > 0 *and* K > 0 empirically.
- **Oracle-soundness risk:** the security oracles must hit the mother-paper bar (κ ≥ 0.87 vs human)
  or the PASS→security-fail claim is contestable.
- **FLARE-availability risk:** the headline comparison needs FLARE (or a faithful re-implementation
  of its reliability oracle) on the *same* MAS apps; if FLARE's artifact is unavailable we must
  re-implement its oracle, which weakens the head-to-head. (Tracked in data_availability.md.)
