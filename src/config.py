"""D5 real-run configuration. Edit via env vars; defaults reuse the mother-paper stack.

OpenRouter (inherited): key OPENROUTER_API_KEY_2 (or OPENROUTER_API_KEY); local proxy 127.0.0.1:7890.
Planner/agents: deepseek/deepseek-chat (V3). Judge/extractor: openai/gpt-4o-mini.
"""
from __future__ import annotations
import os

OPENROUTER_BASE = os.environ.get(
    "OPENROUTER_BASE", "https://openrouter.ai/api/v1/chat/completions"
)

# OpenRouter model slugs (black-box agents + judge). Override with env to test other models.
MODELS = {
    "worker":  os.environ.get("D5_WORKER_MODEL",  "deepseek/deepseek-chat"),
    "manager": os.environ.get("D5_MANAGER_MODEL", "deepseek/deepseek-chat"),
    "judge":   os.environ.get("D5_JUDGE_MODEL",   "openai/gpt-4o-mini"),
}

# Local HF defaults (for the open-weight Worker path on a 4090; gated -> needs HF token).
HF_WORKER  = os.environ.get("D5_HF_WORKER",  "meta-llama/Llama-3.1-8B-Instruct")
EMBED_MODEL = os.environ.get("D5_EMBED_MODEL", "BAAI/bge-small-en-v1.5")
HF_CACHE   = os.environ.get("HF_HOME", r"Z:\study\project\AS\hf_cache")

# Capability tiers to sweep (drives the capability-paradox axis). For OpenRouter, map a tier label
# to a real model slug; for HF/mock, capability is a [0,1] proxy.
CAPABILITY_TIERS = {
    # label : (openrouter_slug, mock_capability_proxy)
    "low":  (os.environ.get("D5_TIER_LOW",  "meta-llama/llama-3.2-3b-instruct"), 0.30),
    "mid":  (os.environ.get("D5_TIER_MID",  "meta-llama/llama-3.1-8b-instruct"), 0.60),
    "high": (os.environ.get("D5_TIER_HIGH", "deepseek/deepseek-chat"),            0.90),
}


def openrouter_key() -> str | None:
    return os.environ.get("OPENROUTER_API_KEY_2") or os.environ.get("OPENROUTER_API_KEY")
