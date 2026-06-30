# MASFuzzer — security-oriented coverage-guided fuzzing for LLM multi-agent systems (D5)

First coverage/feedback-guided MAS fuzzer with a **security oracle** + **attack-semantic inter-agent
mutation operators**. Differentiates from FLARE (reliability oracle, benign mutation), ChainFuzzer/
AgentFuzzer (single-agent security), FuncPoison/TOMA (fixed multi-agent attacks). See `docs/`.

## Layout
```
src/
  config.py            model slugs + env (OpenRouter key/proxy, capability tiers)
  llm_client.py        unified LLM backend: OpenRouter / local-HF / offline-mock (seed>=1, retries, json mode)
  cp_oracle.py         VALIDATED oracle, vendored from CP gpt4o_oracle (gpt-4o-mini, Grade>=2 = hijack)
  mas_core.py          Manager-Worker core + Attack dataclass
  mutators.py          inter-agent mutation operators (+ single-agent subset for the K baseline)
  security_oracles.py  security oracle bank (goal-hijack / trust-boundary / cascading) + FLARE-style reliability oracle
  real_mas.py          real Manager-Worker runner + judges -> MASTrace
  fuzzer.py            campaign loop (mutate -> run -> score), multi vs single scope
  run.py               mock plumbing smoke test (free)
  run_real.py          real-backend run (OpenRouter/HF), default=mock cost guard
  run_cp_validation.py CP-oracle calibration (attack ASR vs benign FPR)
  run_manager_rigor.py Manager-rigor ablation (strict/medium/permissive SOP) <- current experiment
  compute_real_k.py    REAL K signal from CP existing logs (zero new API)
docs/   SETUP / ARTIFACTS / RESULTS / differentiator / mve_plan / related_work / data_availability / COVERAGE
logs/   run logs
```

## Status (2026-06-18)
- Real OpenRouter pipeline working; validated CP oracle integrated.
- **Real K (no API)**: inter-agent-only hijacks dominate (Llama-8B worker: K=143-248 vs worker-only ~3%).
- Scaffold's own toy-prompt runs were INVALID (saturated / refusal-primed) and are discarded — see docs/RESULTS.md.
- Next: build the coverage-guided search ON CP's real `evaluation_autogen.py` (see docs/COVERAGE.md).

## Run
```
cd src
python run.py                                          # free mock plumbing check
python run_manager_rigor.py --backend openrouter --k 30   # manager-rigor ablation (real)
python compute_real_k.py                               # real K from CP logs (no API)
```
Needs `OPENROUTER_API_KEY_2` in env. See docs/SETUP.md for hardware/models.
