# Related Work — Direction 5: Security-oriented MAS fuzzing

Structured by method-line. Each cluster gives the core hypothesis it embodies, representative
works (arXiv id + year/month), and the shared limitation that leaves our four-property combination
open. All arXiv ids below were supplied as verified for this run; none are fabricated.

---

## Cluster A — Coverage/feedback-guided fuzzing of MAS (the substrate, RELIABILITY oracle)

**Core hypothesis.** A multi-agent system is a stateful program whose agent-interaction trace can
be treated as a coverage surface; a fuzzing loop guided by that coverage finds *functional* failure
modes faster than scripted tests.

**Representative work.**
- **FLARE** — *Agentic Coverage-Guided Fuzzing for LLM-Based Multi-Agent Systems.* Hui, Li et al.,
  arXiv 2604.05289 (2026-04). The strongest incumbent and the direct substrate match: a real
  coverage-guided fuzzing loop over a genuine multi-agent target.

**Shared limitation (and the seam we exploit).** FLARE's oracle is a **reliability/functional**
oracle — it flags spec deviation, infinite loops, and failed tool calls. Its mutation is **benign**
(it perturbs benign inputs to expose robustness bugs), and it **explicitly scopes prompt injection
OUT**. So the substrate exists, but the *security* failure surface (goal hijack, trust-boundary
crossing, cascading hallucination, system-level ASR) is unmeasured by construction. A trial that
completes the task without crashing is PASS to FLARE even if the agent was hijacked.

---

## Cluster B — Security greybox fuzzing of LLM agents (SECURITY oracle, but SINGLE-agent)

**Core hypothesis.** An LLM agent's tool-use path is an attack surface; a security oracle attached
to sinks (or to injection success) plus payload mutation turns the agent into a fuzzable target for
*exploitable* — not merely buggy — behavior.

**Representative work.**
- **ChainFuzzer** — *Greybox Fuzzing for Workflow-Level Multi-Tool Vulnerabilities in LLM Agents.*
  arXiv 2603.12614 (2026). Sink-specific security oracles + payload mutation, source-to-sink
  dataflow. Genuinely *security*-oriented, genuinely greybox. But the target is a **single agent
  orchestrating multiple TOOLS**, not multiple autonomous agents.
- **AgentFuzzer / AgentVigil** — *Generic Black-Box Fuzzing for Indirect Prompt Injection against
  LLM Agents.* arXiv 2505.05849 (2025, Dawn Song group). MCTS black-box search; oracle = indirect
  prompt-injection success. Strong security-fuzz reference, but again **single-agent**, and it
  mutates the *injected prompt*, not the inter-agent protocol.

**Shared limitation.** Both lift a security oracle onto a *single* agent. The failure classes that
only exist *between* agents — one agent's output crossing into another's trust boundary, a
hallucination accepted and amplified downstream, system-level ASR over a manager–worker handoff —
are out of reach because there is no second agent to cross into. The mutation vocabulary is
prompt/payload, not inter-agent message/protocol.

---

## Cluster C — Multi-agent SECURITY as FIXED attacks/analyses (no search loop)

**Core hypothesis.** Multi-agent topologies have emergent security failures (cross-agent hijack
propagation, multi-hop influence) that can be *demonstrated* with hand-crafted attacks.

**Representative work.**
- **FuncPoison** — *Poisoning Function Library to Hijack Multi-Agent Autonomous Driving Systems.*
  arXiv 2509.24408 (2025). Cross-agent hijack propagation via a poisoned shared function library —
  a fixed attack construction.
- **TOMA** (*Tipping the Dominos*) — *Topology-Aware Multi-Hop Attacks on LLM-Based Multi-Agent
  Systems.* arXiv 2512.04129 (2025). Topology-aware multi-hop attack; a fixed, analytically-derived
  construction.
- **AgentSafe** — structural access-control / provenance defense for MAS. arXiv 2503.04392 (2025).
  The defense-side counterpart (G0.2 context): structural trust boundaries one would *fuzz against*.

**Shared limitation.** These prove the *existence* of inter-agent security failures but deliver
them as **fixed, hand-crafted attacks or analyses** — there is no coverage/feedback-guided search
that *discovers* new instances. They give us the failure taxonomy and the oracle semantics; they do
not give us a fuzzer.

---

## Cluster D — MAS-as-engine and agent-as-hardener (orthogonal; rules out confusable cites)

**Core hypothesis (theirs).** Multi-agent LLMs are a good *engine* for fuzzing something else, or a
fuzzing agent is a good *hardener* of generated artifacts.

**Representative work.**
- **MALF** — *A Multi-Agent LLM Framework for Intelligent Fuzzing of Industrial Control Protocols.*
  Ning et al., arXiv 2510.02694 (2025-10). MAS is the *engine*; the target is ICS protocols.
- **AutoSafeCoder** — *A Multi-Agent Framework for Securing LLM Code Generation.* Nunez et al.,
  arXiv 2409.10737 (2024). A fuzzing agent hardens *generated code*, not the MAS itself.
- **Hybrid Fuzzing with LLM-Guided Input Mutation and Semantic Feedback.** S. Lin, arXiv 2511.03995
  (2025-11). Traditional C/C++ software fuzzing; LLM is the mutation heuristic.

**Shared limitation (why these do NOT pre-empt us).** In all three the MAS is *never the target of
the fuzzer*. They are listed to forestall the reviewer reflex "isn't MAS-fuzzing already done?" —
yes, MAS appears in fuzzing papers, but as engine or as code-hardener, never as the system-under-
test for a *security* search.

---

## The four-property test (what no single system satisfies)

| System | (a) fuzz/search loop | (b) multi-AGENT target | (c) SECURITY oracle | (d) attack-semantic INTER-AGENT mutation |
|---|---|---|---|---|
| FLARE (2604.05289)        | YES | YES | NO (reliability) | NO (benign) |
| ChainFuzzer (2603.12614)  | YES | NO (multi-tool, single agent) | YES | NO (payload, intra-agent) |
| AgentFuzzer (2505.05849)  | YES | NO (single agent) | YES | NO (injected-prompt mutation) |
| FuncPoison (2509.24408)   | NO (fixed attack) | YES | YES (implicit) | partial (fixed, not searched) |
| TOMA (2512.04129)         | NO (fixed attack) | YES | YES (implicit) | partial (fixed, not searched) |
| MALF / AutoSafeCoder / Lin | YES | engine/N-A | mixed | N-A (MAS not the target) |
| **This proposal**         | **YES** | **YES** | **YES** | **YES** |

No published row has all four cells filled. The combination is what is open.

---

## Terrain verdict

**Open-in-combination but crowded at the edges** (partially-occupied). The four-property
combination — feedback-guided search × multi-AGENT target × SECURITY oracle × attack-semantic
inter-agent mutation — is unoccupied, but every individual edge has a named, recent, strong
incumbent (FLARE, ChainFuzzer, AgentFuzzer) plus fixed-attack multi-agent security work
(FuncPoison, TOMA). This is **not greenfield**; the contribution must be framed as *the first
coverage/feedback-guided MAS fuzzer with a security oracle and inter-agent mutation operators*, and
must differentiate against three neighbors at once.
