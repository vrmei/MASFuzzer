# GCG Remote Mechanism Probe Status

Last updated: 2026-06-30

## Current status

- Background task started for the position-free GCG-style mechanism probe.
- Scope is remote-only and does not modify or depend on the local `swarm_faithful_nolabel100` API formal run.
- Local SSH tooling is available through Windows OpenSSH, and Python `paramiko` is available for non-interactive remote checks.
- SSH password is intentionally not recorded in this document, command summaries, logs, or commit messages.
- Remote SSH login succeeded.
- Remote environment inspection is complete.
- Repository setup is complete via SFTP source snapshot fallback after remote GitHub clone failures.
- Clean remote Python environment is complete and CUDA/PyTorch works.
- Minimal smoke script skeleton is implemented and pushed.
- Remote dry-run/mock sanity check completed successfully without downloading model weights.

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
- Base login-shell PyTorch:
  - `torch 2.8.0+cu128`
  - `transformers 5.12.1`
  - `accelerate 1.14.0`
  - `numpy 2.3.2`
  - `scipy 1.17.1`
  - `sentencepiece 0.2.1`
  - CUDA available: yes
  - Device: Tesla V100S-PCIE-32GB
- Clean experiment environment:
  - Path: `/root/autodl-tmp/masfuzzer-gcg-probe-20260630/envs/gcg-probe`
  - Creation method: conda clone of base into the experiment directory, so the remote base environment is not modified.
  - Python: 3.12.3
  - `torch 2.8.0+cu128`, CUDA 12.8, CUDA available.
  - Device count: 1
  - Device 0: Tesla V100S-PCIE-32GB
- Activation helper:
  - `/root/autodl-tmp/masfuzzer-gcg-probe-20260630/activate_gcg_probe.sh`
  - Sets `HF_HOME`, `TRANSFORMERS_CACHE`, `HF_HUB_CACHE`, and `PIP_CACHE_DIR` under the experiment base.

## Model feasibility

- The V100S 32GB can comfortably support 0.5B-1.5B instruct models for the initial smoke probe.
- 3B-class models should be feasible for short-context logits/embedding probes if dependencies install cleanly.
- 7B-class models may be feasible with careful memory use, quantization, or smaller batch sizes, but should not be the first smoke target.
- Root disk is too tight for model caches. Any HuggingFace/model cache should be placed under `/root/autodl-tmp`.
- After creating the isolated conda environment, `/root/autodl-tmp` has about 54 GiB free.
- HuggingFace direct downloads may be blocked from this host. GitHub is reachable, so alternatives may include mirrored model sources, manually supplied cached weights, or `hf-mirror.com` if allowed by the server network.
- Follow-up check: `hf-mirror.com` is usable for small HuggingFace Hub downloads through `HF_ENDPOINT=https://hf-mirror.com`.
- Immediate model-download path appears available for ungated models such as `Qwen/Qwen2.5-0.5B-Instruct` via the mirror.
- HuggingFace token status: no token is present in the environment; no token appears necessary for the first ungated 0.5B smoke model.

## Repository setup

- Clean experiment base: `/root/autodl-tmp/masfuzzer-gcg-probe-20260630`
- Current symlink: `/root/autodl-tmp/masfuzzer-gcg-probe-current`
- Source directory: `/root/autodl-tmp/masfuzzer-gcg-probe-20260630/MASFuzzer`
- Remote setup logs:
  - `/root/autodl-tmp/masfuzzer-gcg-probe-20260630/logs/repo_setup_20260630_222401.log`
  - `/root/autodl-tmp/masfuzzer-gcg-probe-20260630/logs/repo_setup_retry_20260630_222504.log`
  - `/root/autodl-tmp/masfuzzer-gcg-probe-20260630/logs/repo_sftp_snapshot_20260630_222809.log`
- Attempt 1: `git clone https://github.com/vrmei/MASFuzzer.git ...`
  - Result: failed with GitHub HTTP/2 framing error.
- Attempt 2: `git -c http.version=HTTP/1.1 clone --depth 1 --branch main https://github.com/vrmei/MASFuzzer.git ...`
  - Result: failed with connection timeout to `github.com:443`.
- Fallback used: local `git archive --format=tar.gz HEAD`, uploaded by SFTP and extracted remotely.
- Snapshot source commit: `dcdb6f138806e7d171abbe4e8c62050e28eda099`
- Required design docs are present in the remote snapshot:
  - `docs/gcg_mechanism_probe_plan.md`
  - `docs/LEXICAL_LEVERS.md`
  - `docs/gcg_remote_probe_status.md`
- Snapshot metadata file on remote: `REMOTE_SNAPSHOT_REVISION.txt`

## Python environment setup

- Environment path: `/root/autodl-tmp/masfuzzer-gcg-probe-20260630/envs/gcg-probe`
- Setup log: `/root/autodl-tmp/masfuzzer-gcg-probe-20260630/logs/env_create_20260630_223038.log`
- Method: `conda create --clone base -p /root/autodl-tmp/masfuzzer-gcg-probe-20260630/envs/gcg-probe -y`
- Reason for clone instead of fresh install: base already had a working CUDA/PyTorch stack; cloning isolates the experiment while avoiding another large torch download.
- Cache directories created:
  - `/root/autodl-tmp/masfuzzer-gcg-probe-20260630/hf_home`
  - `/root/autodl-tmp/masfuzzer-gcg-probe-20260630/pip_cache`
  - `/root/autodl-tmp/masfuzzer-gcg-probe-20260630/runs`
- Smoke import result: success for `torch`, `transformers`, `accelerate`, `numpy`, `scipy`, and `sentencepiece`.

## Model download readiness

- Probe log: `/root/autodl-tmp/masfuzzer-gcg-probe-20260630/logs/model_download_probe_20260630_223311.log`
- Mirror small-download log: `/root/autodl-tmp/masfuzzer-gcg-probe-20260630/logs/hf_mirror_small_download_20260630_223409.log`
- Direct `huggingface.co` model config check:
  - Result: timeout / connection errors from remote.
- `hf-mirror.com` model config check:
  - `curl -I -L` reached the Qwen2.5-0.5B-Instruct config endpoint.
  - `curl -L` downloaded `config.json` successfully.
  - `huggingface_hub.hf_hub_download` with `HF_ENDPOINT=https://hf-mirror.com` downloaded `config.json` successfully.
- Candidate first smoke model:
  - `Qwen/Qwen2.5-0.5B-Instruct`
  - Rationale: ungated, small, instruct-tuned, and confirmed reachable through mirror metadata.
- Candidate scale-up after smoke:
  - 1.5B-class instruct model if the 0.5B sanity check works.
  - 3B only if download speed and disk headroom are acceptable.
  - 7B should wait for user approval because remaining disk headroom is about 54 GiB and the branch should not burn large GPU/model-download budget yet.

## Smoke script and dry-run

- Script: `scripts/gcg_position_free_smoke.py`
- Default mode: `--mode dry-run`
- Real-model entry point: `--mode real --model Qwen/Qwen2.5-0.5B-Instruct`
- Topologies implemented for smoke:
  - `supervisor`
  - `swarm`
- Insertion slots implemented:
  - `prefix`
  - `after_incident_summary`
  - `before_requested_action`
  - `after_requested_action`
  - `evidence_adjacent`
  - `suffix`
- Controls implemented:
  - `no_token`
  - `candidate`
  - `random_token`
  - `human_lexicon_phrase`
- Objective:
  - Dry-run mode uses a transparent lexical proxy for the upstream interface score.
  - Real mode scores topology-specific upstream interface target phrases by local-model average log probability.
- Remote sync method: SFTP uploaded the script into the remote snapshot because remote GitHub clone/pull was unreliable.
- Remote dry-run command:
  - `python scripts/gcg_position_free_smoke.py --mode dry-run --payload-limit 2 --topologies supervisor swarm --span-length 4 --out /root/autodl-tmp/masfuzzer-gcg-probe-20260630/runs/gcg_position_free_dryrun.jsonl`
- Remote dry-run log:
  - `/root/autodl-tmp/masfuzzer-gcg-probe-20260630/logs/sync_and_dryrun_20260630_223736.log`
- Remote dry-run outputs:
  - `/root/autodl-tmp/masfuzzer-gcg-probe-20260630/runs/gcg_position_free_dryrun.jsonl`
  - `/root/autodl-tmp/masfuzzer-gcg-probe-20260630/runs/gcg_position_free_dryrun.summary.json`
- Dry-run result:
  - 2 payloads
  - 56 scored rows
  - No model weight download
  - No GPU-heavy workload
  - Sanity passed

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
- Created remote experiment base under `/root/autodl-tmp`.
- Attempted remote GitHub clone twice, recording both failures to remote logs.
- Created a local git archive of current `HEAD`.
- Uploaded the archive with SFTP and extracted it into the clean remote experiment directory.
- Wrote remote snapshot metadata with the source commit hash.
- Checked base login-shell Python and PyTorch.
- Created isolated remote conda environment under the experiment directory.
- Verified CUDA availability from the isolated environment.
- Created activation helper and cache directories under `/root/autodl-tmp`.
- Probed model-source connectivity for HuggingFace, `hf-mirror.com`, and ModelScope.
- Verified small `config.json` download from `hf-mirror.com` using both `curl` and `huggingface_hub`.
- Added `scripts/gcg_position_free_smoke.py`.
- Ran a local dry-run syntax/smoke check.
- SFTP-synced the script to the remote snapshot.
- Ran a remote 2-payload dry-run/mock sanity check and wrote JSONL + summary outputs under the remote experiment base.

## Immediate execution plan

1. Wait for user approval before downloading model weights or running a real 0.5B sanity check.
2. If approved, run only `Qwen/Qwen2.5-0.5B-Instruct` through `hf-mirror.com` on 1-2 payloads first.
3. If the 0.5B real sanity check works, expand to 10-20 payloads and held-out transfer.
4. Do not start a large GCG search until the user approves scaling beyond the tiny smoke.

## User decisions needed

- No HuggingFace token is needed for the proposed first smoke model if `hf-mirror.com` remains usable.
- User approval is needed before downloading any model weights for a real sanity check.
- User approval is definitely needed before running 3B/7B models or a full GCG search.
