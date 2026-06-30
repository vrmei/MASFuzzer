# Prompt Audit for MAS Topology Experiments

Date: 2026-06-29

This audit checks whether the prompts used in prior and planned experiments accidentally build the target
mechanism into the system. The main risk is the pipeline failure mode: a role is instructed to produce an action
plan even when it should preserve an objection, so the experiment measures prompt-induced signal laundering
rather than a natural topology effect.

## High-risk findings

1. Generic pipeline topology used an action-plan-only planner.

- File: `src/topology.py`
- Old prompt: planner was told to draft a concrete action plan from the audit; the decider saw only that plan.
- Risk: reproduces the known pipeline artifact where objections become remediation plans.
- Fix: default `run_pipeline()` now uses a guarded planner that must preserve `VERDICT: ENDORSE` or
  `VERDICT: OBJECT`, and the decider sees original instruction, audit, and planner output.
- Interpretation: old pipeline500 and old pipeline ablations remain useful as action-plan-only interface
  ablations, not as the main pipeline topology evidence.

2. Default swarm topology forced handoff and specialist action recommendation.

- File: `src/topology.py`
- Old prompts: triage always handed off; specialist always recommended the action to take.
- Risk: weaker version of the pipeline artifact. An upstream objection could be softened by a required handoff
  or recommendation contract.
- Fix: default triage is now the critical triage prompt, which can endorse, hold, or escalate. Specialist now
  decides proceed/block/escalate before recommending action.
- Interpretation: old swarm results are still informative for endorsement-transfer, but formal follow-up should
  use the corrected proceed/block/escalate role contracts.

3. Swarm intervention role baselines had action pressure.

- File: `src/run_swarm_intervention.py`
- Old base prompts asked triage to hand off and specialist to recommend action.
- Risk: object conditions had to fight the base prompt.
- Fix: base prompts now explicitly allow hold/block/escalate. The endorse/object suffix remains the causal
  intervention.

## Medium-risk findings

4. Group-chat generic ops prompt was action-oriented.

- File: `src/topology.py`
- Old prompt asked ops to propose concrete next steps.
- Risk: may bias the discussion toward remediation even when the safety reviewer objects.
- Fix: ops now assesses operational options including hold/block/escalate, and proposes steps only if proceeding
  is appropriate.

5. Group-chat intervention is acceptable but should be described precisely.

- File: `src/run_groupchat_intervention.py`
- The endorse/object suffixes explicitly force role stance. This is valid as a causal stance intervention, not as
  a claim about natural group-chat behavior.
- Fix: neutral role baselines now explicitly allow proceed/block/escalate.

6. Pipeline contract `verdict_only` is a control, not a deployment design.

- File: `src/run_pipeline_contract_experiment.py`
- In `plan_only` context, the decider may receive a verdict without rich action context.
- Interpretation: use `verdict_only` to test signal preservation, not as the preferred realistic pipeline. The
  main realistic condition is `guarded_verdict_plan` with `audit_plan_payload`.

7. Behavior judge is LLM-based.

- File: `src/behavior_judge.py`
- Risk: the judge sees the malicious payload and final text, so its grade could inherit some evaluator bias.
- Mitigation already present: report deterministic `rule_oracle` alongside LLM grades.

## Clean or intentional prompts

1. Supervisor prompt family is aligned with the CP-style mechanism.

- The worker audit is a safety assessment and the manager decides from that audit. This is the intended
  supervisor trust-boundary setup, not an accidental action-plan forcing contract.
- Caveat: the manager often sees only the audit, so claims should be about audit-mediated trust, with visibility
  controls where needed.

2. LLM mutator prompts are attack operators, not system prompts.

- File: `src/llm_mutator.py`
- They intentionally optimize certainty, vote endorsement, specialist endorsement, or pipeline laundering.
- This is acceptable for a developer-side fuzzer, because the generated payloads are validated for action
  preservation and evaluated against separate target systems.

3. Legacy pipeline prompts should be retained only as ablations.

- File: `src/run_pipeline_intervention.py`
- The action-plan-only planner and plan-only decider are now explicitly the old-interface ablation.

## Consequence for next experiments

- Main pipeline evidence should come from `run_pipeline_contract_experiment.py`, especially
  `guarded_verdict_plan` plus `audit_plan_payload`.
- `trust_signal100` should be rerun after these prompt fixes. Its pipeline output is now labeled
  `pipeline_guarded_launder` to avoid confusion with the old pipeline baseline.
- For paper wording, distinguish:
  - "natural/corrected topology contracts" for main evidence;
  - "action-plan-only interface" for the pipeline laundering ablation;
  - "forced stance intervention" for group-chat and swarm causal tests.
