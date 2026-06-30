"""Unified LLM client for D5 real runs: OpenRouter | local HF | offline mock.

- backend="openrouter": OpenAI-compatible POST to OpenRouter (respects env proxy). Needs a key.
- backend="hf":         local transformers generate (needs torch+transformers+weights+GPU).
- backend="mock":       deterministic offline stub (no deps) so `python run_real.py` runs anywhere.
- backend="auto":       openrouter if key present, else hf if importable+model set, else mock.

All backends expose .chat(messages, temperature, max_tokens, seed) -> str.
"""
from __future__ import annotations
import hashlib
import json
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import config


_TRACE_LOCK = threading.Lock()
_TRACE_DEFAULT_FILE: str | None = None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _trace_file() -> str | None:
    if os.environ.get("D5_TRACE", "1").lower() in {"0", "false", "no", "off"}:
        return None
    explicit = os.environ.get("D5_TRACE_FILE")
    if explicit:
        return explicit
    global _TRACE_DEFAULT_FILE
    if _TRACE_DEFAULT_FILE is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        _TRACE_DEFAULT_FILE = os.path.join("logs", "llm_traces", f"trace_{stamp}_{os.getpid()}.jsonl")
    return _TRACE_DEFAULT_FILE


def _write_trace(record: dict) -> None:
    path = _trace_file()
    if not path:
        return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with _TRACE_LOCK:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _det(*parts) -> float:
    s = "||".join(str(p) for p in parts)
    return (int(hashlib.sha256(s.encode()).hexdigest(), 16) % 10_000) / 10_000.0


@dataclass
class LLMClient:
    role: str = "worker"                 # worker | manager | judge
    backend: str = "auto"
    model: Optional[str] = None
    capability: float = 0.6              # [0,1] proxy used by mock path / metadata for real
    _hf = None                           # lazily-loaded (pipeline,) tuple

    def __post_init__(self):
        if self.backend == "auto":
            if config.openrouter_key():
                self.backend = "openrouter"
            else:
                try:
                    import torch, transformers  # noqa: F401
                    self.backend = "hf" if config.HF_WORKER else "mock"
                except Exception:
                    self.backend = "mock"
        if self.model is None:
            self.model = config.MODELS.get(self.role, config.MODELS["worker"])

    # ---- public ---------------------------------------------------------------------------
    def chat(self, messages: list[dict], temperature: float = 0.7,
             max_tokens: int = 512, seed: int = 0, json_mode: bool = False,
             metadata: Optional[dict] = None) -> str:
        call_id = uuid.uuid4().hex
        started = time.time()
        record = {
            "call_id": call_id,
            "started_at": _utc_now(),
            "pid": os.getpid(),
            "thread_id": threading.get_ident(),
            "role": self.role,
            "backend": self.backend,
            "model": self.model,
            "capability": self.capability,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "seed": seed,
            "json_mode": json_mode,
            "metadata": metadata or {},
            "messages": messages,
        }
        try:
            if self.backend == "openrouter":
                response = self._chat_openrouter(messages, temperature, max_tokens, seed, json_mode)
            elif self.backend == "hf":
                response = self._chat_hf(messages, temperature, max_tokens, seed)
            else:
                response = self._chat_mock(messages, seed)
            record.update({
                "ok": True,
                "response": response,
                "finished_at": _utc_now(),
                "duration_s": round(time.time() - started, 3),
            })
            _write_trace(record)
            return response
        except Exception as e:
            record.update({
                "ok": False,
                "error_type": type(e).__name__,
                "error": str(e),
                "finished_at": _utc_now(),
                "duration_s": round(time.time() - started, 3),
            })
            _write_trace(record)
            raise

    # ---- backends -------------------------------------------------------------------------
    def _chat_openrouter(self, messages, temperature, max_tokens, seed, json_mode=False) -> str:
        import requests  # guarded: only needed on the real path
        key = config.openrouter_key()
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY[_2] not set")
        payload = {
            "model": self.model, "messages": messages,
            "temperature": temperature, "max_tokens": max_tokens,
            "seed": max(1, int(seed) + 1),   # some providers require seed >= 1 (e.g. llama-3.2-3b)
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        # requests honors HTTP(S)_PROXY env automatically; mother-paper proxy = 127.0.0.1:7890
        import time
        last = None
        for attempt in range(5):                       # retry transient network/5xx errors w/ backoff
            try:
                r = requests.post(config.OPENROUTER_BASE, headers=headers,
                                  data=json.dumps(payload), timeout=(10, 90))  # (connect, read); fail fast on dead sockets
                if r.status_code >= 500 or r.status_code == 429:
                    last = RuntimeError(f"OpenRouter {r.status_code}: {r.text[:200]}")
                    time.sleep(2 * (attempt + 1)); continue
                if r.status_code >= 400:                # 4xx (e.g. bad slug) = real error, don't retry
                    raise RuntimeError(f"OpenRouter {r.status_code} for '{self.model}': {r.text[:300]}")
                return r.json()["choices"][0]["message"]["content"]
            except requests.exceptions.RequestException as e:   # SSL/conn/timeout = transient
                last = e
                time.sleep(2 * (attempt + 1))
        raise RuntimeError(f"OpenRouter failed after retries for '{self.model}': {last}")

    def _chat_hf(self, messages, temperature, max_tokens, seed) -> str:
        if self._hf is None:
            import torch
            from transformers import pipeline, set_seed
            self._hf = (pipeline("text-generation",
                                 model=self.model or config.HF_WORKER,
                                 torch_dtype=torch.bfloat16, device_map="auto"),
                        set_seed)
        pipe, set_seed = self._hf
        set_seed(seed)
        out = pipe(messages, max_new_tokens=max_tokens, temperature=max(0.01, temperature),
                   do_sample=temperature > 0)
        return out[0]["generated_text"][-1]["content"]

    def _chat_mock(self, messages, seed) -> str:
        """Deterministic stub. Emits a tiny JSON the parsers in real_mas can read, with
        capability-scaled hijack tendency so offline runs still show the paradox direction."""
        prompt = " ".join(m.get("content", "") for m in messages)
        r = _det(self.role, self.model, prompt, seed)
        certainty = min(1.0, 0.35 + 0.5 * self.capability + (_det("c", prompt, seed) - 0.5) * 0.3)
        return json.dumps({
            "role": self.role, "certainty": round(certainty, 3), "rand": round(r, 3),
            "text": f"[mock {self.role} cap={self.capability:.2f}]",
        })
