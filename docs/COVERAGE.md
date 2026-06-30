# Coverage in MASFuzzer — how to compute it, how it guides the search, and how it differs by architecture

## 1. What coverage is FOR (the feedback loop)
In greybox fuzzing, coverage is the **feedback signal that steers mutation toward unexplored behavior**:
keep a coverage map; a mutated input that hits a NEW cell is retained as a seed and given more energy;
inputs that add nothing are deprioritized. Coverage answers "have we been here before?"; the **oracle**
answers "is this a failure?". MASFuzzer needs BOTH: coverage to explore, the security oracle to detect.

## 2. There is no code coverage in an LLM MAS → use a behavioral/security state space
- Traditional fuzzers use branch/line coverage. An LLM agent has no branches to instrument.
- **FLARE's answer = behavioral coverage**: extract a behavioral space from agent definitions, measure
  inter-agent coverage (96.9%) + intra-agent coverage (91.1%). But this rewards exploring NORMAL behavior.
- **MASFuzzer needs SECURITY-relevant coverage**: a space whose cells correspond to distinct
  (attack-vector × inter-agent-interaction × failure-mode) regions, so that maximizing it drives the search
  toward DIVERSE security failures, not just diverse benign behavior. This is the core design choice.

## 3. The MASFuzzer coverage map (cells)
A "cell" is a discretized, security-relevant signature of one trial's trace. Coverage = set of hit cells;
new cell => keep + energize the seed. Proposed cell schema (per inter-agent step):

```
cell = ( operator,                # which mutation produced it (narrative / tool-poison / obs-inject / proto / topology)
         edge,                    # which inter-agent edge it acted on (A->B, B->C, ...)
         target_tool_class,       # sensitive-tool family targeted (sql / fs / financial / k8s / fabricated)
         strategy,                # payload strategy (SRE-urgency / data-integrity / security-containment ...)
         decision_state,          # agent decision at that edge (approve / deny / escalate / wavered)
         failure_class )          # oracle verdict at that edge (none / goal-hijack / trust-boundary / cascading)
```

Three nested coverage criteria (report all three):
- **C1 behavioral/state** (FLARE-style): (edge, decision_state) tuples reached — "did we exercise this
  inter-agent interaction at all?"
- **C2 attack-surface**: (operator × edge × target_tool_class × strategy) — "did we try this attack kind on
  this edge against this tool under this narrative?" This is the denominator the SEARCH maximizes.
- **C3 failure-mode**: (failure_class × edge[/path]) — "did we discover this failure type at this location?"
  New C3 cells are the most valuable (a genuinely new security failure).

## 4. How coverage GUIDES (correctly)
Greybox loop with a multi-objective fitness:
1. Seeds = initial attacks (paradox_dataset_500). Energy schedule favors seeds that recently unlocked new cells.
2. Pick seed -> apply a mutation operator -> run the MAS -> parse trace -> compute hit cells (C1/C2/C3) +
   run the security oracle.
3. **Retain & energize** the mutated input iff it hits a NEW cell (esp. a new C3 failure cell) OR triggers a
   new failure; otherwise deprioritize. Fitness = w1*new_C2 + w2*new_C3 + w3*failure_severity.
4. Iterate. Report coverage(hit/reachable) per C1/C2/C3 and unique failures.

**Correct guidance = the metric must be discriminative.** The coverage-criteria literature warns that a
coverage metric that does NOT correlate with finding new failures is useless (neuron-coverage critique;
arXiv 2408.15207 / RACA 2602.02280). So MASFuzzer MUST validate its coverage with a falsifiable test:
> **Kill-criterion:** if coverage-guided search finds no more unique security failures (and no higher
> diversity) than an ASR-only / random baseline at equal budget, the coverage signal adds nothing — drop it.
The right "denominator" is C2/C3 (security space), NOT C1 alone: maximizing benign-behavioral coverage (C1)
can be high while security coverage (C3) is near zero — that is exactly FLARE's blind spot.

## 5. The two architectures differ in WHERE coverage lives (the key design point)

### Architecture A — hierarchical Manager-Worker (CP / mother-paper; one trust boundary)
Worker-auditor -> Manager-decision. **A single trust-boundary chokepoint** (the Manager).
- Behavioral space is TINY (2 agents, 1 decision edge). C1 is almost trivially saturated.
- The attack surface is concentrated at ONE edge -> coverage is **low-dimensional**:
  `(operator × target_tool_class × strategy × manager_decision_state)`.
- "New coverage" = a new manager-decision pattern / a narrative that flips the single Manager.
- The guided search optimizes **DEPTH at one edge**: which narratives push the Manager from deny->approve.
- Dominant failure class = trust-boundary crossing (Grade>=2). Cascading hallucination is shallow (1 hop).
- K (inter-agent advantage) = "Manager hijacked but Worker not" at that one boundary (measured: K=143-248).

### Architecture B — flat / peer / pipeline / graph MAS (FLARE-style apps; many edges)
Multiple peer agents, round-robin / group-chat / multi-hop pipeline. **No single chokepoint; many edges.**
- Behavioral space is LARGE; C1 needs FLARE-style spec/space extraction from the app graph.
- Coverage is **high-dimensional**: `(edge × hop_depth × message_type × operator × failure_class ×
  propagation_path)`. Failures CASCADE across hops (A->B->C), so coverage must track PROPAGATION PATHS.
- "New coverage" = a new propagation path / a new edge-failure / a DEEPER cascade (hop-depth d+1).
- The guided search optimizes **BREADTH + DEPTH across the graph**: which mutations open new failure paths;
  topology mutation becomes a first-class operator (TOMA's topology-aware multi-hop lives here).
- Cascading hallucination and multi-hop goal-drift are NATIVE to B (they need >=2 hops to exist).
- K generalizes from "1 boundary" to "any inter-agent path the failure traverses that a single agent can't".

### Side-by-side
| | A: Manager-Worker (hierarchical) | B: peer/pipeline/graph |
|---|---|---|
| trust boundaries | 1 chokepoint (Manager) | many edges, distributed |
| coverage dimensionality | low (decision-state × tool × strategy) | high (edge × hop-depth × path × failure) |
| "new coverage" means | new manager-decision flip | new propagation path / deeper cascade |
| search optimizes | depth at one edge | breadth + depth across the graph |
| native failure classes | trust-boundary crossing | cascading hallucination, multi-hop goal-drift |
| topology mutation | N/A (fixed 2-agent) | first-class operator |
| coverage denominator | enumerable directly | needs FLARE-style behavioral-space extraction |
| K | hijacked-Manager vs safe-Worker | failure path no single agent reproduces |

**Design implication:** start on A (the CP pipeline — small, controllable, where K is already measured) to
validate that security-coverage guidance beats ASR-only; then lift to B (FLARE's AutoGen app graphs), where
the coverage machinery (paths, hop-depth, topology mutation) is where the real novelty + impact lives, and
where MASFuzzer most differentiates from FLARE (security paths) and from single-agent fuzzers (multi-hop).
