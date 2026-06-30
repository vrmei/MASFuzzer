# GCG Remote Probe Control Panel

Date: 2026-06-30

This file is the user-visible control surface for the remote GPU / position-free GCG mechanism-probe branch.
It exists because the background Codex thread may not be visible in the sidebar.

## Background Thread

- thread id: `019f18e4-617f-7281-9de7-48d60b2bca1f`
- role: remote GPU mechanism-probe worker
- repo worktree: separate Codex worktree, based on `main`
- rule: do not interfere with the local `swarm_faithful_nolabel100` API formal run

## Where Progress Should Appear

The background worker has been instructed to write and push progress here:

- `docs/gcg_remote_probe_status.md`

Expected contents:

- remote SSH/GPU environment check;
- GPU model and VRAM;
- CUDA/Python/PyTorch status;
- clean environment setup status;
- feasible model size;
- exact smoke-test plan;
- commands executed, summarized without secrets;
- blockers or decisions needed from the user.

## Task Boundary

The remote worker should first perform an environment check and a small smoke test only. It should not burn large
GPU budget until the user approves scaling.

Initial smoke target:

- topology: supervisor and swarm;
- payloads: 10-20, or 1-2 for a first sanity check;
- open-weight model: start with 0.5B-1.5B if uncertain, scale only if VRAM allows;
- search: position-free short token span;
- objective: upstream interface score rather than final hijack only;
- controls: no-token, random token, random position, human lexicon phrase.

## Main-Thread Responsibility

The current main thread remains responsible for:

- monitoring the local API formal run;
- reading the pushed status document;
- relaying user instructions to the background thread when needed.
