# GCG Remote Mechanism Probe Status

Last updated: 2026-06-30

## Current status

- Background task started for the position-free GCG-style mechanism probe.
- Scope is remote-only and does not modify or depend on the local `swarm_faithful_nolabel100` API formal run.
- Local SSH tooling is available through Windows OpenSSH, and Python `paramiko` is available for non-interactive remote checks.
- SSH password is intentionally not recorded in this document, command summaries, logs, or commit messages.
- Remote SSH login succeeded.
- Remote environment inspection is complete.
- Repository setup is pending.

## Remote environment check

- Host: `autodl-container-30da119afa-3d5f29d4`
- User: `root`
- OS: Ubuntu 22.04.5 LTS, Linux kernel `5.15.0-86-generic`
- Remote timestamp observed: `2026-06-30T22:22:11+08:00`
- CPU/RAM: 629 GiB RAM, 567 GiB available at check time, no swap.
- Root filesystem: 30 GiB overlay, 25 GiB used, 5.6 GiB available.
- Data/work filesystem: `/root/autodl-tmp`, 350 GiB xfs, 289 GiB used, 62 GiB available.
- Shared public filesystem: `/autodl-pub`, 3.9 TiB nfs4, 528 GiB available.
- Network checks:
  - `github.com`: reachable over HTTPS.
  - `huggingface.co`: HTTPS connection refused from the remote host during the check.

## SSH status

- Target: `root@region-9.autodl.pro` on port `39585`
- Status: success with Python `paramiko`.

## GPU / CUDA / Python / PyTorch

- GPU: NVIDIA Tesla V100S-PCIE-32GB
- Total VRAM: 32,768 MiB
- Free VRAM at check time: 32,495 MiB
- Driver: 580.105.08
- `nvidia-smi` reported CUDA runtime compatibility: 13.0
- CUDA directories present: `/usr/local/cuda`, `/usr/local/cuda-12`, `/usr/local/cuda-12.8`
- `nvcc`: not on the default remote shell `PATH`.
- Default non-login shell `PATH` does not expose Python or conda.
- Login shell (`bash -lc`) exposes Miniconda:
  - Python: `/root/miniconda3/bin/python3`, version 3.12.3
  - Conda: `/root/miniconda3/bin/conda`, version 24.4.0
  - Pip: `/root/miniconda3/bin/pip`
- PyTorch status: not yet checked inside the login shell or a clean environment. The first non-login check failed because `python3` was not on `PATH`.

## Model feasibility

- The V100S 32GB can comfortably support 0.5B-1.5B instruct models for the initial smoke probe.
- 3B-class models should be feasible for short-context logits/embedding probes if dependencies install cleanly.
- 7B-class models may be feasible with careful memory use, quantization, or smaller batch sizes, but should not be the first smoke target.
- Root disk is too tight for model caches. Any HuggingFace/model cache should be placed under `/root/autodl-tmp`, which currently has about 62 GiB free.
- HuggingFace direct downloads may be blocked from this host. GitHub is reachable, so alternatives may include mirrored model sources, manually supplied cached weights, or `hf-mirror.com` if allowed by the server network.

## Repository setup

Pending.

## Executed command summary

- Checked local availability of `ssh.exe` and `scp.exe`.
- Checked local availability of Python packages for SSH automation: `paramiko` is available.
- Checked git remote: `origin` points to `https://github.com/vrmei/MASFuzzer.git`.
- Connected to the remote host with `paramiko`.
- Ran remote identity and OS checks: `whoami`, `hostname`, `date -Is`, `uname -a`, `/etc/os-release`, `uptime`.
- Ran remote storage and memory checks: `df -hT`, `lsblk`, `du -sh /root/autodl-tmp`, `free -h`.
- Ran GPU checks: `nvidia-smi`, then `nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv,noheader,nounits`.
- Ran CUDA/runtime path checks: `nvcc --version`, `ls -d /usr/local/cuda*`.
- Ran Python/conda checks in both default shell and login shell.
- Ran network checks with `curl -I -L --max-time 15` for HuggingFace and GitHub.

## Immediate execution plan

1. Create a clean remote experiment directory under `/root/autodl-tmp`.
2. Clone `https://github.com/vrmei/MASFuzzer.git`.
3. Create a clean Python environment for the open-weight probe, with caches directed to `/root/autodl-tmp`.
4. Check PyTorch in that clean environment.
5. Prepare only a minimal smoke plan for supervisor + swarm, 10-20 payloads, six insertion slots, 4-8 token spans, and controls.
6. If the environment is smooth, scaffold or run only a tiny dry-run / 1-2 payload sanity check.

## User decisions needed

- Need a model-download decision if HuggingFace remains unreachable from the remote host. A HuggingFace token alone may not fix the current issue because the observed failure was connection refused, not authentication denied.
- No decision needed before repository clone and clean environment creation.
