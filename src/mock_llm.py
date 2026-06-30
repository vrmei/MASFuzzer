"""Deterministic mock LLM for MVE skeletons (no API burned).

Every direction's mve_skeleton/ can import this. The point of a mock is to prove the
EXPERIMENT PLUMBING runs end-to-end: prompts flow, an oracle auto-judges, baselines share
an interface, seeds vary. Swap MockLLM -> a real OpenRouter client to run for real.

Design:
- Output is a deterministic function of (model_name, prompt, seed) via a hash, so runs are
  reproducible and ">=3 seeds, mean+/-std" is demonstrable without randomness from the network.
- `capability` in [0,1] lets us SIMULATE the capability paradox: higher-capability mocks are
  tuned to be more fluent/assertive and (per the mother paper) more hijackable, so skeletons
  can show the expected monotonic trend before any real model is plugged in.
"""
from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from typing import Optional


def _h(*parts: object) -> int:
    s = "||".join(str(p) for p in parts)
    return int(hashlib.sha256(s.encode("utf-8")).hexdigest(), 16)


def _unit(*parts: object) -> float:
    """Deterministic pseudo-uniform in [0,1) from the parts."""
    return (_h(*parts) % 10_000) / 10_000.0


@dataclass
class MockLLM:
    name: str
    capability: float = 0.5          # proxy for MMLU tier, in [0,1]
    # optional steering knob used by direction 1 (alpha<0 => suppress confidence-inflation dir)
    confidence_steer_alpha: float = 0.0

    def complete(self, prompt: str, seed: int = 0, system: str = "") -> str:
        """Return a short mock completion. Deterministic in (name, prompt, seed)."""
        r = _unit(self.name, system, prompt, seed)
        tag = "assertive" if self._assertiveness(prompt, seed) > 0.5 else "hedged"
        return f"[{self.name}|cap={self.capability:.2f}|{tag}|r={r:.3f}] mock-response"

    # --- signals the oracles/skeletons read -------------------------------------------------
    def _assertiveness(self, prompt: str, seed: int) -> float:
        """Simulated linguistic-certainty (assertive minus hedging), the mother-paper mediator.

        Rises with capability (capability paradox) and falls with negative confidence steering
        (direction 1's intervention). Instance-specific noise keeps it from being a flat shift,
        which is the whole point vs blanket uncertainty injection.
        """
        base = 0.35 + 0.5 * self.capability
        instance = (_unit(self.name, prompt, seed) - 0.5) * 0.3   # instance residual
        steer = -0.25 * max(0.0, -self.confidence_steer_alpha)    # alpha<0 lowers certainty
        return max(0.0, min(1.0, base + instance + steer))

    def hijack_susceptibility(self, attack_strength: float, prompt: str, seed: int) -> float:
        """P(this Worker is fooled) given an attack's semantic strength in [0,1].

        Mirrors the mother paper: semantic attacks scale with capability via certainty.
        Steering (alpha<0) lowers certainty -> lowers susceptibility, instance-specifically.
        """
        certainty = self._assertiveness(prompt, seed)
        return max(0.0, min(1.0, attack_strength * (0.2 + 0.8 * certainty)))


@dataclass
class ToolLibrary:
    """A deliberately gap-y tool catalogue for direction 2 (hallucinated-tool squatting)."""
    tools: list[str] = field(default_factory=list)
    # names a strong model is tempted to "fill the gap" with (not in `tools`)
    plausible_missing: list[str] = field(default_factory=list)

    def contains(self, name: str) -> bool:
        return name in self.tools
