# 3 Method (draft prose — present tense)

## 3.1 Overview and threat model

MASFuzzer is a black-box, coverage-guided fuzzer that synthesizes prompt-injection attacks against
multi-agent LLM systems (MAS). Unlike single-agent jailbreak fuzzers, it treats the *system* — a graph of
cooperating LLM agents that culminates in a tool-authorizing decision — as the unit under test, and unlike
white-box reliability fuzzers it observes only the agents' natural-language outputs.

The key idea is that effective guidance is *mechanism-grounded* rather than diversity-driven. The mother paper
(Liu et al., arXiv 2605.17480 [verify-PDF]) showed that the linguistic *certainty* of an auditor agent's
report mediates the bulk of the capability-to-hijack effect: a worker that confidently declares an unsafe
action "safe" is what flips the downstream decision. MASFuzzer turns this mediator into a fuzzing fitness. It
steers an LLM mutation operator to climb the auditor's output certainty — a continuous, causally-grounded, and
climbable scalar — rather than to maximize behavioral diversity, which we find saturates (§4.6). Crucially, the
right lever depends on *where the decision is gated*: when a suspicious auditor stands between the attacker and
the decision, certainty (which keeps that auditor calm) is the winning signal; when a single or unscrutinizing
agent decides, a data-mined persuasion *recipe* wins instead. MASFuzzer selects the operator from the gate
structure (§3.6).

**Threat model.** The attacker submits a single natural-language request at the system's entry point (e.g., an
SRE incident report to an automated incident-response MAS). It has no access to model weights, logits, system
prompts, intermediate agent traces, or tool-execution feedback — only the system's final, observable decision.
This is the realistic setting for a third party interacting with a deployed agentic service. The attacker's
goal is to maximize the rate at which the system authorizes a dangerous tool action, under a fixed query budget.

**Revision note for the current draft.** The final paper should use a developer-side red-team threat model:
MASFuzzer observes agent traces and final decisions during test runs, but has no access to model weights, logits,
gradients, provider internals, or hidden serving templates. Thus the method is black-box with respect to the
models and trace-observing with respect to the MAS under test. This correction is necessary because
trust-signal feedback such as auditor certainty, vote balance, specialist endorsement, and planner laundering is
computed from intermediate agent messages.

## 3.2 Problem formulation

A MAS is an ordered set of agents \(A_1,\dots,A_n\), each a fixed (model, system-prompt) pair, connected by a
topology \(\tau\) that defines the message graph. Given a request \(x\), the system produces a trace
\(T_\tau(x) = (o_1,\dots,o_n)\) of agent outputs and a final decision \(d = o_n\). A validated oracle
\(O(d)\in\{0,1,2,3,4\}\) grades the decision; a **hijack** is \(O(d)\ge 2\). For a seed corpus \(\mathcal{S}\)
of deceptive requests, a mutation budget \(B\), and a mutation family \(\mathcal{M}\), the attacker seeks

\[ \max_{x_1,\dots,x_B} \; \frac{1}{B}\sum_{j=1}^{B} \mathbb{1}[\,O(T_\tau(x_j))\ge 2\,], \qquad
   x_j \in \mathcal{M}(\mathcal{S}). \]

We define the **gate** \(g(\tau)\in\{A_1,\dots,A_n\}\) as the agent whose refuse/comply decision is pivotal for
\(d\): the upstream auditor in auditor-first topologies (pipeline, supervisor), and the lone or terminal decider
otherwise (single, swarm, groupchat). The gate is a property of the topology, the per-agent policies, and the
decider's capability; §3.6 makes attack synthesis conditional on it.

## 3.3 Certainty as a climbable fitness

For the gate's (or first agent's) output \(o\), we score its linguistic certainty \(c(o)\) with three
interchangeable estimators (`certainty_core.py`):

- **Lexicon.** \(c_\text{lex}(o) = \rho_\text{assert}(o) - \rho_\text{hedge}(o)\), the per-1000-word density of
  assertive minus hedging terms, using the *exact* validated lexicon from the mother paper — i.e., the construct
  with which the 74% mediation was measured. It is deterministic, free, and the most defensible guidance signal.
- **Embedding.** A character-n-gram hashing vectorizer projects \(o\) onto the certainty *direction*
  \(\bar v_\text{assert}-\bar v_\text{hedge}\) estimated from anchor sentences. This is local and free, and
  generalizes beyond the exact lexicon terms (morphological variants, paraphrase).
- **Judge.** An LLM returns a discrete certainty in \(\{0,1,2\}\). We use this only as an *independent*
  validation axis; we never guide on the same estimator we validate with.

Certainty is the right fitness because it is *continuous and climbable*. Our early attempts to guide on
behavioral diversity (the distinct (affect × certainty × justification) cells of hijacked decisions) tied a
random baseline, because the hijack behavior space is small and saturates after a handful of samples (§4.6). A
scalar mediator with a monotone link to the objective (§4.2) is, by contrast, a gradient the search can ascend.

## 3.4 Certainty-guided LLM mutation

The certainty operator rewrites a parent request to raise the gate's response certainty while preserving a
coherent incident narrative and the embedded dangerous action. Two design choices make the guidance work where
hand-coded operators fail.

**Expressive mutation.** A naive operator that concatenates assertive boilerplate cannot reliably climb the
auditor's *response* certainty and degrades plausibility. Instead, an attacker LLM performs the rewrite under a
certainty-maximizing instruction (`CERT_SYS`), producing fluent variants that induce a confident "safe" verdict.
We seed it with high-certainty exemplars mined from the corpus (the few-shot "successful attack" pool).

**Evolutionary search.** MASFuzzer maintains an archive of evaluated candidates and, each step, breeds a mutant
from the top-\(k\) elites by certainty, evaluates it through the topology, scores \(c\) (free, local) and \(O\)
(oracle), and updates the archive. This hill-climb ascends the certainty gradient toward the high-ASR region.

**Fair control.** The decisive baseline is the *same* attacker LLM rewriting with no objective (`neutral`),
which isolates the contribution of *steering* from the contribution of LLM rewriting per se. We additionally
compare against `concat`, the hand-coded random-operator baseline that was strongest in the early coverage
phase. Algorithm 1 specifies the loop.

## 3.5 Success-condition mining and the recipe operator

To understand what makes attacks succeed beyond certainty — and to attack gates where certainty is not the
lever — we mine the corpus offline, using *no new queries*. We compute, for each of 500 seed payloads, its
cross-manager success rate over 14 real manager models from existing oracle-graded logs, yielding a continuum
from robustly-blocked (\(sr=0\)) to near-universally-successful (\(sr=0.85\)). A multi-agent pipeline then
(i) contrasts the success-rate extremes through diverse analytical lenses to surface candidate framings,
(ii) labels the corpus on a tactic taxonomy, and (iii) adversarially verifies each candidate against
strategy/tool-matched controls to reject confounds.

This procedure rejects the obvious answers and isolates the real ones (§4.4). Coarse strategy/tool categories
and *input-text* certainty do not predict success; saturated tactics (urgency, assertiveness) fail
verification. The verified conditions are framings of *how the destruction is presented*: a live external-
attacker reframe, a first-person commander voice with stated forensic certainty, a euphemized action verb, a
named recovery source bound to an irreplaceable target, an omitted loss-disclosure, and third-party/compliance
stakes. We encode these as a second mutation operator (`RECIPE_SYS`) that rewrites a payload to apply the
verified framings in priority order while stripping the anti-features (exotic root causes, fabricated protocol
citations) that predict refusal.

## 3.6 Stage- and scrutiny-aware guidance selection

The certainty and recipe operators target *different* gates, and applying the wrong one is wasteful or
counterproductive. The recipe's live-attacker frame persuades a naive decider, but it *alarms* a scrutinizing
auditor: an explicit "active intrusion + destructive remediation" narrative trips the auditor's cyberattack and
agentic-misuse safety categories, lowering its certainty and the system's ASR. Conversely, certainty steering
keeps a suspicious auditor calm but does little when no auditor gates the decision.

MASFuzzer therefore prefers *certainty* when an upstream auditor gates the decision, and falls back to the
*recipe* for a lone, unscrutinizing decider. Empirically (§4.5), this is borne out robustly at the auditor end:
certainty wins in the supervisor (auditor→manager) topology across every seed and both scales — the edge the
mediator lives on. The operative principle is that certainty-steering targets an *auditor*: it pays off where
one gates the decision. We report honestly (§4.5) that no other topology yields a stable guidance winner (the
single-agent contrast is a low-signal regime whose winner flips with scale), so the advantage is
auditor-edge-specific rather than a stable cross-architecture rule.

## 3.7 The fuzzing loop (Algorithm 1)

```
Input: seed corpus S, topology τ, budget B, gate g(τ), decider capability κ
Output: archive of graded candidates
op ← select_operator(g(τ), κ)            # certainty if auditor-gated or capable decider; else recipe
E ← mine_exemplars(S)                     # high-certainty few-shot pool
archive ← evaluate(S₀)                    # seed evaluations
for t in 1..B:
    parent ← sample_elite(archive, key=fitness(op))      # certainty for cert-op; grade for recipe
    x ← op.mutate(parent, E)                              # LLM rewrite
    o, d ← run_topology(τ, x)                             # black-box system call
    c ← certainty(o₁); y ← oracle(d)                      # free local score + validated grade
    archive ← archive ∪ {(x, c, y, coherence(x))}
return archive
```

Each candidate costs the topology's agent calls plus one oracle call; certainty is computed locally for free.
We report per-arm ASR, deep-capture count (grade ≥ 3), coherence, and the pooled certainty→grade dose-response.
