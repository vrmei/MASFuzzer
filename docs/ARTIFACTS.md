# D5 baselines & testbed — artifact availability + fallback plan (verified 2026-06-18)

> Confirmed via arXiv + GitHub search (allowed_domains scoped). Bottom line: **neither baseline's code is
> public as of now, but both are reproducible — you are not blocked.**

## 1. FLARE (arXiv 2604.05289) — the reliability-fuzzer incumbent
- **Code + 16 apps: NOT found public.** The "FLARE" GitHub namespace is all unrelated (mandiant flare-floss,
  jzbjyb/FLARE = retrieval-augmented gen, flare-foundation, etc.). Paper is on arXiv; no artifact link surfaced.
- **Reproducible because**: the 16 apps are **AutoGen-based**, selected from top GitHub repos via keywords
  `autogen-application` / `autogen-extension`, spanning code-generation / video-production / data-analysis /
  deep-research, 80–550 LOC each, with external tool invocation + knowledge retrieval + nested group chats.
- **What you must do anyway**: reimplement FLARE's **functional/reliability oracle** (spec-deviation /
  failed-tool-call / loop) on YOUR app set — this is required to compute **M = count(reliability PASS AND
  security FAIL)**. It's already stubbed in `mve_skeleton/security_oracles.py::reliability_oracle`; wire it to
  the AutoGen run log (`spec_deviation`, `failed_tool_call`, `looped`).
- **Action**: (a) email the FLARE authors for code/app list (cite the arXiv id); (b) in parallel build the
  fallback app set below so you don't wait.

## 2. AgentFuzzer / AgentVigil (arXiv 2505.05849, Dawn Song group) — single-agent security-fuzz baseline
- **Code: NOT located public.** Renamed AgentVigil; method clearly described: MCTS seed-selection + mutation
  loop over injected attack instructions; ~71% ASR on a GPT-4 agent.
- **Reproducible**: reimplement as the single-agent baseline. In the skeleton, the single-agent scope is
  already modeled as `SINGLE_AGENT_OPERATORS` (the non-inter-agent operator subset) — replace its mutation
  loop with an MCTS seed selector over single-agent injection to make the baseline faithful.

## 3. Fallback testbed (use immediately; don't wait on FLARE)
Assemble ~8–16 AutoGen MAS apps spanning FLARE's categories:
- **code-gen**: AutoGen `AssistantAgent`+`UserProxyAgent` coding loop; MetaGPT-style dev team.
- **data-analysis**: AutoGen data-analyst + executor group chat.
- **deep-research**: planner→searcher→writer multi-agent (AutoGen `RoundRobinGroupChat` / `Swarm`).
- **tool-augmented**: agents with a fixed tool registry (matches `ToolLibrary` in the skeleton).
Pick from the official `microsoft/autogen` examples + top `autogen-application` repos; record each app's
spec (for the reliability oracle) and trust boundary (for the Grade>=2 oracle). Log the exact app set +
commit hashes in `data_availability.md` so the comparison is reproducible.

## 4. Net effect on the plan
- Head-to-head still works: run YOUR security-oriented fuzzer AND a reimplemented FLARE-functional-oracle +
  AgentFuzzer-single-agent baseline on the SAME fallback apps. Report M (PASS→security-fail) and K
  (inter-agent-only), exactly as `run_real.py` computes.
- Honesty note for the paper: state the baselines are reimplemented from the papers' descriptions (code not
  released at submission time) and pin app commit hashes — reviewers accept faithful reimplementation when
  the original artifact is unavailable, provided it is disclosed.

## 5. Confirmed-available (no blocker)
- Mother-paper AutoGen Manager-Worker pipeline + 500-sample gated benchmark + Grade>=2 oracle rubric — yours.
- OpenRouter stack (DeepSeek-V3 agents + GPT-4o-mini judge), proxy 127.0.0.1:7890 — inherited.
- The runnable skeleton (`mve_skeleton/`, mock + real backends).
