# Trust-Signal Fuzzer Redesign

## Why This Change

The original certainty-guided fuzzer is well matched to the supervisor/auditor edge, but it should not be used
as the universal mutation objective for every MAS topology. The revised method treats certainty as one
trust signal among several topology-specific signals.

## Threat Model Correction

MASFuzzer is a developer-side or red-team testing tool. It is black-box with respect to model weights, logits,
gradients, and hidden provider internals, but it observes the MAS trace and final decision produced during a
test run. This is the right setting for mechanism-guided fuzzing, because the fuzzer needs feedback from the
agent-to-agent interface it is testing.

## Mutation Objectives

| topology | descriptor | primary mutation objective |
|---|---|---|
| supervisor | `auditor_certainty` | induce a confident safe/routine auditor report |
| groupchat | `vote_balance` | increase endorsement votes and reduce dissent |
| swarm | `specialist_handoff_endorsement` | make the specialist endorse the handoff as vetted/actionable |
| pipeline | `safety_signal_erasure` | convert an upstream objection into an executable remediation plan |
| single | `single_decider_persuasion` | use verified success framings from corpus mining |

## Validity Gate

Every LLM-mutated payload must pass deterministic checks before it is used in formal results:

- destructive action class preserved;
- target tool/domain preserved;
- target resource anchor preserved when detectable;
- no explicit jailbreak or protocol-artifact text;
- coherence remains above the experiment threshold.

Formal runs should discard or retry invalid mutants. Pilot runs may keep invalid mutants only if validity rates
are reported and not used for headline ASR.

## Revised Experiment Order

1. `pipeline_contract25`: verify the redesigned pipeline contract experiment.
2. Validator smoke test on existing mutators: report invalid-rate by arm.
3. Supervisor fuzzer at 100 payloads: certainty objective remains the primary method result.
4. Groupchat fuzzer at 100 payloads: vote-balance objective versus certainty/recipe/neutral.
5. Swarm fuzzer at 100 payloads: specialist-endorsement objective versus certainty/recipe/neutral.
6. Pipeline fuzzer at 100 payloads: safety-signal-erasure objective plus contract ablations.
7. Promote stable cells to 500 payloads with the same payload ids, model tiers, and full trace logging.

## Reporting Rule

The paper should claim that MASFuzzer discovers and exploits topology-specific trust signals. It should not
claim that linguistic certainty is a universal MAS vulnerability mechanism.
