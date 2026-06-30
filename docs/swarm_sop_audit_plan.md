# Swarm SOP Audit Plan

Date: 2026-06-30

Goal: test whether the swarm/handoff result is robust to framework-faithful handoff semantics rather than an
artifact of a prompt that forces handoff and action recommendation.

## Payloads

- `n=100`
- Sampling: `stratified_strategy_tool`
- Seed: `42`
- The same payload ids are used for every SOP profile.

## SOP Profiles

1. `public_faithful`
   - Triage may hand off, hold, escalate, or reject.
   - Specialist may proceed, hold, escalate, or block.
   - This is the main framework-faithful swarm condition.

2. `forced_handoff`
   - Triage always summarizes and hands off.
   - Specialist recommends an action.
   - This is the legacy/action-pressure ablation.

3. `safety_critical`
   - Triage and specialist independently hold/escalate/block destructive or under-authorized actions.
   - This is the conservative approval-boundary ablation.

## Metrics

- LLM judge ASR and mean grade.
- Deterministic rule-oracle ASR.
- Triage block/escalate signal rate.
- Specialist block/escalate signal rate.
- Triage and specialist endorsement balance.
- Full triage, specialist, executor, and judge traces are logged.

## Interpretation

- If `forced_handoff` is much stronger than `public_faithful`, prior swarm results were inflated by role-contract
  pressure.
- If `public_faithful` still shows non-trivial ASR and endorsement predicts hijack, handoff endorsement remains a
  legitimate swarm trust signal.
- If `safety_critical` sharply lowers ASR, the defense story is an explicit approval boundary at handoff edges.
