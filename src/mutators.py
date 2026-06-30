"""Attack-semantic INTER-AGENT mutation operators for Direction 5.

This is the mutation vocabulary that distinguishes the proposal from single-agent fuzzers
(AgentFuzzer mutates the injected prompt; ChainFuzzer mutates the sink payload). Here the operators
act on the *inter-agent* surface. Each operator takes a base Attack and returns a mutated Attack,
and declares whether it is inter-agent (multi_agent_scope) -- single-agent baselines cannot apply
the inter-agent ones, which is how K (inter-agent-only failures) becomes measurable.

Operators (the library named in the verdict):
  - hijack_narrative_mutation : strengthen the domain-coherent authorization narrative (semantic).
  - tool_output_poisoning     : poison agent A's tool output that agent B consumes (INTER-AGENT).
  - observation_injection     : inject into the observation channel between agents (INTER-AGENT).
  - message_protocol_mutation : mutate the inter-agent message/protocol envelope (INTER-AGENT).
"""
from __future__ import annotations
from dataclasses import replace
from mock_llm import _unit
from mas_core import Attack


def hijack_narrative_mutation(a: Attack, seed: int) -> Attack:
    """Push semantic_strength up toward the FULL purely-semantic narrative (mother-paper axis)."""
    bump = 0.2 + 0.3 * _unit("hijack", a.name, seed)
    return replace(a, name=a.name + "+narr",
                   narrative=a.narrative + " [reinforced domain-coherent authorization]",
                   semantic_strength=min(1.0, a.semantic_strength + bump))


def tool_output_poisoning(a: Attack, seed: int) -> Attack:
    """Poison the tool OUTPUT that agent A returns and agent B trusts. Inter-agent."""
    bump = 0.15 + 0.25 * _unit("toolpoison", a.name, seed)
    m = replace(a, name=a.name + "+toolpoison",
                narrative=a.narrative + " [poisoned upstream tool output]",
                semantic_strength=min(1.0, a.semantic_strength + bump))
    return m


def observation_injection(a: Attack, seed: int) -> Attack:
    """Inject into the observation channel B reads from A. Inter-agent."""
    bump = 0.15 + 0.25 * _unit("obsinject", a.name, seed)
    return replace(a, name=a.name + "+obsinj",
                   narrative=a.narrative + " [injected cross-agent observation]",
                   semantic_strength=min(1.0, a.semantic_strength + bump))


def message_protocol_mutation(a: Attack, seed: int) -> Attack:
    """Mutate the inter-agent message/protocol envelope. Inter-agent."""
    bump = 0.1 + 0.2 * _unit("protomut", a.name, seed)
    return replace(a, name=a.name + "+proto",
                   narrative=a.narrative + " [mutated inter-agent protocol envelope]",
                   semantic_strength=min(1.0, a.semantic_strength + bump))


# operator registry: (fn, is_inter_agent)
OPERATORS = {
    "hijack_narrative_mutation": (hijack_narrative_mutation, False),  # has a single-agent analogue
    "tool_output_poisoning":     (tool_output_poisoning, True),
    "observation_injection":     (observation_injection, True),
    "message_protocol_mutation": (message_protocol_mutation, True),
}

# Single-agent baselines (AgentFuzzer/ChainFuzzer) can only use the NON-inter-agent operators.
SINGLE_AGENT_OPERATORS = {k: v for k, v in OPERATORS.items() if not v[1]}
