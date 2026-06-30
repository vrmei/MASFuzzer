# D5 — real-model results log (honest accounting)

## ⚠️ Headline: the toy scaffold is INVALID. Use CP's real pipeline.
My `run_real.py` / `run_cp_validation.py` scaffold (hand-rolled 2-turn Worker→Manager with my own prompts)
produces non-valid numbers. Root cause, confirmed by reading CP's real `evaluation_autogen.py`:
- **My Manager prompt primed refusal** ("default DENY, only in-library tools") — I suppressed the very
  effect D5 studies.
- **CP's `SOP_manager` is deliberately PERMISSIVE** ("Incident Response Commander"; auditor inputs are
  "high-weight recommendations, NOT absolute vetoes"; "Maximize Utility"; "Risk of Inaction Analysis").
  **That permissive framing IS the hijack surface.** Without it, ASR collapses (my scaffold) or the oracle
  mis-fires.
- My benign FPR=1.0 was a **category error**: I fed benign requests to the *attack-grading* oracle (whose
  prompt says "[Deceptive Payload]" / "was the worker fooled"), so benign *compliance* graded as "fooled."

## Run history
- **Run 1** (`run_real.py`, hand-rolled oracle): sec=1.0/M=1.0/K≈0 everywhere → oracle SATURATED. Invalid.
- **Run 2** (`run_cp_validation.py` k=4, CP oracle): high/multi ASR=0.50 + cascading 2/4 vs single 0 — looked
  great, but **n=4 noise**.
- **Run 3** (`run_cp_validation.py` k=10, CP oracle): high/multi == high/single (both 0.20), **cascading=0/10
  everywhere**, benign FPR=1.0. → The Run-2 "K signal" **did NOT replicate**; benign control broken; ASR
  suppressed by my refusal-primed prompts. **All scaffold numbers discarded.**

## Real validated BASELINE (from CP saved results, no new API) — what D5 builds on
Full-MAS over the **500-payload benchmark**, graded by the validated oracle (`paper/results_manager_llama_worker.json`):

| Manager | Worker | ASR | grades 0/1/2/3/4 |
|---|---|---|---|
| Qwen-2.5-7B | Llama-3.1-8B | 49.0% | 175/66/15/134/110 |
| Qwen-2.5-72B | Llama-3.1-8B | 31.0% | 338/4/1/76/81 |
| Llama-3.1-70B | Llama-3.1-8B | 30.2% | 346/2/14/27/111 |
| Llama-3.1-8B | Llama-3.1-8B | 20.6% | 309/38/41/48/64 |

Real ASR 20–49% with genuine spread — the pipeline works; my scaffold was the problem.

## Corrected D5 architecture (build on CP, do NOT re-roll)
Engine = CP `src/autogen_framework/evaluation_autogen.py`:
- reuse `SOP_worker` (Llama-Guard-style triage) + `SOP_manager` (permissive commander = hijack surface) +
  the 10-tool registry + the UserProxy→Worker→Manager flow + the validated oracle.
**D5-new layers on top:**
1. **inter-agent mutation operators** — reuse CP `toy_poc/mutator_structure.py` (narrative/structure mutation)
   + add tool-output poisoning on the **Worker→Manager audit handoff** + observation injection. (CP runs
   FIXED payloads; D5 turns this into a guided search.)
2. **cascading-hallucination oracle** — Manager invokes a tool NOT in the 10-registry that the Worker's audit
   suggested (folds Direction 2). Auto-detect from the AutoGen tool_calls vs the registry.
3. **K (inter-agent advantage)** — reuse CP's **full-MAS (`evaluation_autogen.py`) vs worker-only
   (`evaluation_autogen_worker_only.py`)**: payloads hijacked in full-MAS but NOT worker-only. CP has both
   configs + logs → K is computable on REAL data, partly without new API.
4. **M (vs FLARE)** — add a reliability oracle (spec-deviation/loop/failed-tool from the AutoGen run log) and
   count security-FAIL ∧ reliability-PASS.

## Next real result (no/low API): compute K from CP's existing data
CP already has full-MAS logs (`logs/`) and worker-only logs (`logs_worker_eval/`) + saved grades for the same
500 payloads. Comparing per-payload grade(full-MAS) vs grade(worker-only) gives the **real K signal**
(inter-agent-only hijacks) with little/no new API — the robust replacement for the noisy scaffold K.
