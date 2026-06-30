# Position-Free GCG Mechanism Probe Plan

Date: 2026-06-30

Purpose: add an interpretable, open-weight mechanism probe alongside the black-box API experiments. This is not
a replacement for the current formal runs. The API experiments measure whether topology-specific trust signals
work in realistic black-box MAS settings; the GCG-style probe asks whether similar levers can be discovered and
interpreted at the token/embedding level in an open-weight sandbox.

## Core Question

Can a short token span, inserted at an optimized position inside a payload, reliably push a given topology's
trusted inter-agent interface toward its failure mode?

Examples:

- supervisor: auditor safe-certainty increases;
- swarm: triage routes to specialist and specialist continues;
- groupchat: endorsement balance shifts positive;
- pipeline: objections are converted into an executable remediation plan.

## Why It Can Run in Parallel

The current formal `swarm_faithful_nolabel100` run is API-bound and mostly waits on network/model responses. It
does not use the local GPU. A local mechanism probe can therefore run in parallel if it uses a separate Python
environment and does not modify the active API experiment process.

Current local hardware observed:

- GPU: NVIDIA GeForce RTX 4060 Laptop GPU
- VRAM: 8 GB
- Current API experiment: still running in a background PowerShell process, not using GPU
- Current Python torch environment: not immediately usable for CUDA, because importing torch fails with a
  `c10.dll` initialization error. Use a fresh environment rather than repairing the active one in place.

## Resource Tiers

| tier | hardware | feasible model scale | what it can support | recommended use |
| --- | --- | --- | --- | --- |
| local smoke | RTX 4060 Laptop 8 GB | 0.5B-1.5B instruct, possibly 3B with tight batching | position-free discrete search, logit scoring, embedding-neighbor interpretation | first mechanistic smoke test |
| remote single GPU | 24 GB GPU such as RTX 4090 / L4 / A10G | 7B-8B instruct in fp16/bf16 or efficient 8-bit | stronger GCG-style optimization across more payloads/topologies | paper-grade mechanism appendix |
| larger remote | 40-80 GB GPU | 14B+ or multi-model comparison | robustness across model families | optional, not needed for first submission |

## Minimum Viable Local Experiment

Use the 8 GB GPU only for a small, interpretable sandbox:

- model: a 0.5B-1.5B open instruct model first;
- payloads: 10-20 total;
- topologies: start with supervisor and swarm only;
- insertion slots: prefix, after incident summary, before requested action, after requested action, before
  evidence, suffix;
- span length: 4-8 tokens;
- search budget: 50-100 update steps per topology;
- objective: upstream interface score, not only final hijack;
- controls: random tokens, random positions, human lexicon phrases, and no-token baseline.

Expected runtime on local 8 GB GPU: hours, not days, if batching is conservative. This is enough to answer
whether the idea has signal before renting a larger GPU.

## Paper-Grade Version

If the local smoke test shows stable transfer:

- move to a 24 GB GPU;
- use a 7B-8B instruct model;
- run all major topologies;
- optimize on a training payload split and evaluate on held-out payloads;
- report transfer rate, interface-score shift, final ASR shift, and embedding-nearest lexicon cluster.

The key paper criterion is not just finding a token string. It must satisfy:

1. improves the target topology on held-out payloads;
2. does not equally improve unrelated topologies;
3. clusters near a human-readable lexicon direction in embedding space;
4. beats random-token and random-position controls.

## Interpretation Rule

- Stable token spans near the expected lexicon support a real topology lever.
- Effective but semantically uninterpretable strings are adversarial artifacts, useful for robustness but weak as
  mechanism evidence.
- Effects that only work for one open-weight model should be framed as model-specific.

## Recommendation

Do not pause the current API experiments. Run the GCG-style probe as a parallel, smaller mechanistic branch after
creating a clean CUDA environment. Treat the first local run as a go/no-go smoke test; only scale to 24 GB if it
finds transferable, semantically interpretable token directions.
