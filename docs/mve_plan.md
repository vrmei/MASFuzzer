# MVE Plan — Direction 5: Security-oriented MAS fuzzing

Minimal falsifiable experiment. Goal: in the cheapest possible setting, show the two survival
conditions (M > 0 and K > 0) are *measurable*, and that the framework's security oracle flags trials
a FLARE-style functional oracle passes. The mock skeleton proves the plumbing; this plan states the
real run.

## Independent variables
- **V1 — oracle type:** `reliability` (FLARE-style functional oracle) vs `security` (our oracle
  bank: goal-hijack, trust-boundary, cascading-hallucination, system-level ASR). *Within-subjects*:
  the same trial trace is scored by both oracles, so M = #(reliability=PASS ∧ security=FAIL) is a
  paired quantity.
- **V2 — target scope:** `single-agent` (AgentFuzzer/ChainFuzzer reachability — mutate the injected
  prompt / payload only) vs `multi-agent` (our inter-agent mutation operators). K = #(failures
  reachable only in multi-agent scope).
- **V3 — mutation operator family** (within `security` arm): {hijack-narrative mutation, tool-output
  poisoning, observation injection, message/protocol mutation} — for the operator-ablation.

## Fixed / controlled
- Same N MAS apps (manager–worker AutoGen pipeline; mother-paper infra). MVE: N = 3 small apps.
- Same fuzzing budget (trials per app) across all arms.
- Same backbone LLMs (DeepSeek-V3 planner, GPT-4o-mini judge/oracle) across arms.

## Named recent strong baselines (>= 1 required; we name two)
1. **FLARE** (2604.05289) — *failure-type coverage on the SAME MAS apps* using its reliability
   oracle. The primary head-to-head; M (PASS→security-fail count) is computed against it.
2. **AgentFuzzer / AgentVigil** (2505.05849) — *single-agent security fuzz* reference; gives the
   single-agent reachable set against which K (inter-agent-only failures) is computed.

## Metrics
- **M** = security-unique failures over FLARE = #(reliability oracle = PASS ∧ security oracle = FAIL).
  *Primary.* (Survival needs M > 0.)
- **K** = inter-agent failures unreachable by single-agent baselines = #(failures found in multi-
  agent scope ∧ not found in single-agent scope). *Primary.* (Survival needs K > 0.)
- **Security-unique failures found** (count + rate per trial budget), broken down by oracle class.
- **Oracle-vs-human agreement**: Cohen's κ of each security oracle against human labels on a
  held-out sample. Target **κ ≥ 0.87** (reuse mother-paper methodology). Soundness gate.
- **System-level ASR** per app (mother-paper primary metric) for the goal-hijack/trust-boundary
  classes.

## Statistical test
- **>= 3 seeds** (seeds vary fuzzer RNG + mutation sampling). Report **mean ± std** for every rate.
- **Paired test** on the within-subjects oracle contrast: per app, per seed, the reliability and
  security oracles score the *same* trace → **Wilcoxon signed-rank** (paired) on failure-rate
  difference, with **Cliff's δ / rank-biserial** effect size. Bonferroni across the oracle classes.
- For the M and K counts: report bootstrap 95% CI over seeds; survival claim = CI lower bound > 0.
- Mann-Whitney (unpaired) only where arms are not trace-aligned (e.g. multi- vs single-agent
  reachable-set sizes).

## Operator ablation
Leave-one-out over V3's four mutation operators; report the drop in security-unique failures (M)
when each operator is removed — establishes that the *inter-agent* operators (not just narrative
mutation) carry the K signal.

## Compute estimate
- MVE scale: N = 3 apps × 4 arms (rel/sec × single/multi) × 3 seeds × ~150 trials/arm ≈ **5.4k
  trials**. With caching and small backbones (V3 + 4o-mini), ~2–4 LLM calls/trial → ~15–22k calls.
- At OpenRouter small-model rates this is a low-tens-of-dollars run; **< 1 GPU-day equivalent** if
  any local model is used for the planner. No training. Fits the inherited OpenRouter stack.
- The **mock skeleton** in `mve_skeleton/` reproduces the full M/K/paired-test reporting loop at
  **zero API cost** to de-risk plumbing before any real spend.

## Decision rule (ties to falsification)
Run → if bootstrap-CI lower bound of **both** M and K > 0 with κ ≥ 0.87 oracles → proceed to full
paper. If **either** M or K collapses to 0 → direction is DEAD per the differentiator's sharp
falsifier; do not paper it.
