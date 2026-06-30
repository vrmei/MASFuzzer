# Real MAS architectures — taxonomy + what MASFuzzer implements (recon 2026-06-18)

Cross-validated across AutoGen / CrewAI / LangGraph / OpenAI-Agents-SDK(Swarm) / Anthropic "Building
effective agents" + MAS-security surveys (FLARE 2604.05289, agentic-SoK 2602.19555, TOMA 2512.04129).
Motivation: the single (Manager-Worker) ASR result does NOT generalize — security failure is
architecture-dependent, so D5 must cover the real topology space.

## The canonical topologies (by real-world prevalence)
| topology | prevalence | edge structure | who decides | trust boundary | native security failure |
|---|---|---|---|---|---|
| **sequential-pipeline** (chain) | HIGH | role1→role2→…→roleN, each sees prior output | fixed last/role | each handoff edge | cascading hallucination / error amplification (no critic gate); injection laundering down the chain |
| **supervisor / router** (star) | HIGH (dominant) | central router ↔ workers; router reads all, dispatches | the supervisor/router | router's prompt (reads untrusted transcript) + worker tools | routing/goal hijack; selector-prompt injection; **decider overrides detector** (the CP Manager-Worker case) |
| **group-chat / debate** (broadcast mesh) | MED (HIGH in AutoGen) | one shared broadcast context, round-robin/selector turns; all-to-all read | termination cond / closing decider | the flat shared context = single trust pool | one agent's poison propagates to ALL turns; speaker/voice spoofing; termination-token spoofing (DoS/runaway) |
| **swarm / handoff** (digraph) | MED, rising | directed handoff edges; control transfers peer→peer | the currently-speaking agent | each handoff edge = trust-delegation; handoff is a tool call | handoff abuse / confused-deputy across hops (A→B→A to evade guards); context smuggling in the handoff payload; misrouted/stuck handoff |
| **hierarchical teams** (tree) | MED | nested supervisors (teams of teams) | top supervisor | every inter-team boundary | cross-team propagation; nested trust laundering (inner team's output trusted wholesale) |
| **orchestrator-workers / blackboard** (shared memory) | MED-HIGH | orchestrator spawns workers, shared state/memory | orchestrator | the shared memory/state store | memory poisoning persisted across workers; spawned-worker authority creep (≈ supervisor variant) |

Frameworks: AutoGen RoundRobinGroupChat / SelectorGroupChat / Swarm / SocietyOfMind / two-agent UserProxy;
CrewAI Process.sequential / Process.hierarchical / Flows; LangGraph supervisor / hierarchical-teams /
swarm(network) / create_react_agent; OpenAI Agents SDK handoffs; Anthropic prompt-chaining / routing /
parallelization(sectioning,voting) / orchestrator-workers / evaluator-optimizer.

## What MASFuzzer implements now (`src/topology.py`, homogeneous model isolates topology)
- `single`     — ONE fused agent (the correct baseline: same model+policy+task, NO inter-agent handoff).
- `pipeline`   — audit → plan → decide (sequential chain).
- `supervisor` — auditor worker → supervisor decides (= CP Manager-Worker, generalized; the single point we'd measured).
- `groupchat`  — analyst/ops/safety share one context R rounds → decider closes (broadcast mesh / debate).
- `swarm`      — triage → specialist → executor via handoffs (decentralized digraph).
(hierarchical-teams = composition of `supervisor`; orchestrator-workers ≈ `supervisor` + shared state — add next.)

Each `run_*` returns a unified `Trace`; `final_text` = the system's decision, graded by the validated
oracle (`cp_oracle.grade_manager`, Grade≥2 = hijack). The mutation operators + security-oracle bank consume
the same `Trace`, so the fuzzer is architecture-agnostic.

## The experiment (`src/run_topology_compare.py`)
Fix model (deepseek-chat) + decision policy (rigor); vary ONLY topology; k payloads from the 500-set:
- **ASR by architecture** → is the security failure architecture-dependent?
- **Δ vs single** (per-payload) → does this architecture make it MORE hijackable than one fused agent?
- **K = #(topology hijacked ∧ single NOT)** → failures that exist ONLY because of the multi-agent structure
  (the correct MAS-vs-single signal, fused-single baseline — fixes the earlier mis-baselined head-to-head).

## Why this matters for D5
Turns "ASR on one Manager-Worker pipeline" into "**security failure is architecture-dependent; here is which
topologies are most fragile and a fuzzer that works across them**" — the generalization that lifts D5 from a
single-point result toward a real (and more publishable) contribution. Per-topology coverage/oracle design in
`docs/COVERAGE.md` (Architecture A vs B).
