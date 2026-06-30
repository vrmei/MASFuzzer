# Data & Model Availability — Direction 5: Security-oriented MAS fuzzing

## MAS apps (the systems-under-test)
- **Primary (mother-paper infra):** the AutoGen **Manager–Worker** pipeline from the Capability
  Paradox project, with the 500-sample benchmark. **Access:** GATED behind a responsible-use
  agreement; the recon team are authors → likely direct access. **License/use restriction:**
  responsible-use / non-redistribution; treat as **NC-equivalent** — do not republish the gated
  benchmark, only derived metrics.
- **Public-rebuild fallback (if gated access is unavailable for a given reviewer/repro):**
  `danluu/post-mortems` public repo as the seed corpus + the same Gemini-mutation pipeline to
  regenerate scenario inputs. This reproduces the *shape* of the benchmark without the gated file.
- **Additional MAS apps for N ≥ 3:** small open AutoGen / multi-agent example pipelines (manager +
  ≥2 workers + a shared tool library). Built in-house from the skeleton; no external license.

## Baseline artifacts
- **FLARE** (arXiv 2604.05289) — needed for the head-to-head failure-type-coverage comparison on the
  **same** MAS apps. **Risk:** if the FLARE artifact/code is not released, we must **re-implement its
  reliability oracle** (spec deviation / loop / failed-tool-call detectors) faithfully; this is
  tracked as the "FLARE-availability risk" in differentiator.md. Check the paper page for a code
  link before committing to the head-to-head framing.
- **AgentFuzzer / AgentVigil** (arXiv 2505.05849, Dawn Song group) — needed as the single-agent
  security-fuzz reference (computes the single-agent reachable set for K). Dawn Song group artifacts
  are often released; verify license before redistribution. Black-box MCTS fuzzer; if unavailable,
  approximate its reachable set by restricting our fuzzer to single-agent prompt mutation (the V2 =
  `single-agent` arm in the MVE plan already does this as a controlled proxy).
- **ChainFuzzer** (arXiv 2603.12614) — referenced for the multi-tool single-agent contrast; not
  strictly required to run if AgentFuzzer covers the single-agent reachability reference.

## Models
- **Planner / agent backbone:** `deepseek/deepseek-chat` (DeepSeek-V3) via OpenRouter
  (`OPENROUTER_API_KEY_2`, proxy 127.0.0.1:7890) — inherited stack.
- **Judge / oracle extractor:** `openai/gpt-4o-mini` via OpenRouter — used for goal-embedding /
  task-completion judging and oracle scoring.
- **Open-weight tier (capability-paradox replication, optional):** DeepSeek-R1, Llama-3.1 family —
  open weights, activations accessible (needed if confidence-steering from Direction 1 is folded in
  as a mutation operator). Llama-3.1 carries the **Llama Community License** (use restrictions on
  >700M-MAU; fine for research). DeepSeek weights under their MIT-style/DeepSeek license — verify
  per-checkpoint before any redistribution.

## Human-label data for oracle validation (κ ≥ 0.87)
- A held-out sample of fuzzer-found trials, dual-annotated by ≥2 humans against the four security-
  oracle classes, to establish Cohen's κ vs the auto oracle. **Source:** generated in-house from our
  own runs; no external dataset or license. This reuses the mother-paper rubric and κ methodology.

## Download / access path summary
| Asset | Path / source | License / restriction |
|---|---|---|
| Mother-paper MAS + 500-benchmark | Team gated repo (authors have access) | Responsible-use, NC-equivalent, no redistribution |
| Public-rebuild fallback corpus | `danluu/post-mortems` (public GitHub) | Public repo; check repo license for redistribution |
| FLARE | arXiv 2604.05289 page → code link (verify exists) | TBD; re-implement oracle if unreleased |
| AgentFuzzer/AgentVigil | arXiv 2505.05849 page → code link | TBD; verify before redistribution |
| DeepSeek-V3 / 4o-mini | OpenRouter API | Pay-per-token; no redistribution of weights |
| DeepSeek-R1 / Llama-3.1 | HF hub | DeepSeek license / Llama Community License |
| Human oracle labels | Generated in-house | None |

## NC / gating flags (call-outs)
- The **gated 500-sample benchmark** is the one NC-equivalent asset — report derived metrics only.
- **FLARE and AgentFuzzer code availability are unverified** as of this recon; both are flagged as
  risks, with concrete fallbacks (oracle re-implementation; single-agent-scope proxy) so the MVE is
  not blocked by either.
