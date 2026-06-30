# Related Work (draft prose — all citations PDF-verified 2026-06-20)

> Positioning, not a catalogue. Each cluster: core assumption → representative works → limitation that opens our
> seam. Final paragraph returns to our contribution. Fields still needing PDF-level confirmation tagged [v].

## Fuzzing and coverage-guided testing of LLM agents
The closest line treats an LLM agent or agent system as software under test and applies fuzzing. **FLARE**
[flare2026] is the nearest neighbor: it brings *coverage-guided* fuzzing to LLM-based *multi-agent* systems,
extracting specifications and oracles from agent source code and driving inputs to maximize inter- and
intra-agent execution coverage. FLARE is, however, *white-box* (it reads agent source) and *reliability*-
oriented (it surfaces functional failures), and its coverage signal is execution structure. **ChainFuzzer**
[chainfuzzer2026] fuzzes a different surface — workflow-level, multi-tool dataflow vulnerabilities in an agent's
tool-chain — rather than the decision-hijacking we target. **AgentVigil** [agentvigil2025] (formerly AgentFuzzer)
is black-box and security-oriented like us, using MCTS to search indirect-prompt-injection triggers, but it
targets a *single* agent and offers no account of *why* an injection succeeds. None of these guides search by a
causal mechanism of the failure, and none studies how the right attack depends on the multi-agent topology.

## Quality-diversity and curiosity-driven red-teaming
A second line generates diverse adversarial prompts for a single target model via quality-diversity (QD) or
novelty search. **Rainbow Teaming** [rainbow2024] casts red-teaming as MAP-Elites over attack-style × risk-
category descriptors; **QDRT** [qdrt2025] and **AutoQD** [autoqd2025] extend the descriptor design and automate it;
**Curiosity-RT** [curiosity2024] drives coverage by prompt-embedding novelty. **T-MAP** [tmap2026] is the first to
apply MAP-Elites to *agents*, but its descriptor is the agent's execution *trajectory* and its target is a
single (MCP) agent. These methods share two assumptions we break: the search descriptor is an *input-* or
*behavior-side* surface feature (not a causal mediator of the failure), and the target is a single model. We
show empirically (§4.2, §4.4) that the input-side certainty these methods could optimize does *not* predict
multi-agent success — the causal lever is the *auditor's output* certainty — and that the effective descriptor
in a MAS is the mechanism together with the *gate*.

## Multi-agent system security and failure analysis
A third line characterizes MAS failures and inter-agent attacks. **MAST** [mast2025] provides a descriptive
taxonomy of why multi-agent systems fail, but does not synthesize attacks. **AiTM** [aitm2025] (Agent-in-the-
Middle) attacks the inter-agent *communication channel*, assuming the attacker can intercept or alter messages;
we assume only entry-point access and no channel control. Work on persuasion in agents [persuasion2026] studies a
*single* long-running agent and is relevant only as background on persuasion mechanisms, not as multi-agent
evidence. Most directly, the *Capability Paradox* [liu2026capabilityparadox] establishes the phenomenon we weaponize —
*semantic hijacking*, in which a more capable auditor makes the system *less* secure — and identifies the
auditor's linguistic *certainty* as a mediator (robust in the worker-only setting, weaker in the full MAS). It
is a measurement study, not an attack generator, and explicitly leaves the full-MAS mediation only partially
explained.

## Our positioning
We turn the Capability-Paradox mediator into a *fitness*: a black-box, coverage-guided fuzzer whose search
climbs the auditor's output certainty (§3.4), strengthening the mediator's evidence precisely in the full-MAS
regime where [liu2026capabilityparadox] found it weakest (§4.2). Unlike FLARE we are black-box and security-oriented and our
coverage is a causal mechanism rather than execution structure; unlike the QD red-teaming line we steer a
mediator inside a *multi-agent* system rather than an input-side descriptor on a single model; and unlike all of
the above we make attack synthesis *stage- and scrutiny-aware*, showing across five architectures that whether
certainty-steering or a data-mined persuasion recipe wins is determined by where the decision is gated and how
capable the deciding agent is (§4.5). To our knowledge this is the first black-box, mechanism-grounded,
stage-aware prompt-injection attack synthesizer for LLM multi-agent systems.
