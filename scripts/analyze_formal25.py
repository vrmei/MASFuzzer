from __future__ import annotations

import collections
import json
import math
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "logs"
OUT = LOGS / "formal25_analysis.md"

FILES = {
    "low": {
        "groupchat": LOGS / "formal25_low_llama31_8b_groupchat.json",
        "pipeline": LOGS / "formal25_low_llama31_8b_pipeline.json",
        "swarm": LOGS / "formal25_low_llama31_8b_swarm.json",
    },
    "mid": {
        "groupchat": LOGS / "formal25_mid_llama31_70b_groupchat.json",
        "pipeline": LOGS / "formal25_mid_llama31_70b_pipeline.json",
        "swarm": LOGS / "formal25_mid_llama31_70b_swarm.json",
    },
    "high": {
        "groupchat": LOGS / "formal25_high_deepseek_v3_groupchat.json",
        "pipeline": LOGS / "formal25_high_deepseek_v3_pipeline.json",
        "swarm": LOGS / "formal25_high_deepseek_v3_swarm.json",
    },
}


def load(path: Path) -> dict:
    return json.load(open(path, encoding="utf-8"))


def fmt(x: float) -> str:
    return f"{x:.2f}"


def section_groupchat(lines: list[str]) -> None:
    lines.append("## Groupchat: endorsement dose response")
    lines.append("")
    lines.append("| upstream | k=0 | k=1 | k=2 | k=3 | delta k3-k0 | rule delta |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for tier, paths in FILES.items():
        rows = load(paths["groupchat"])["summary"]
        by = {r["n_endorsers"]: r for r in rows}
        delta = by[3]["asr"] - by[0]["asr"]
        rdelta = by[3]["rule_asr"] - by[0]["rule_asr"]
        lines.append(
            f"| {tier} | {fmt(by[0]['asr'])} | {fmt(by[1]['asr'])} | {fmt(by[2]['asr'])} | "
            f"{fmt(by[3]['asr'])} | {fmt(delta)} | {fmt(rdelta)} |"
        )
    lines.append("")


def section_swarm(lines: list[str]) -> None:
    lines.append("## Swarm: specialist endorsement dominates")
    lines.append("")
    lines.append("| upstream | O/O | O/E | E/O | E/E | specialist effect | triage-only effect |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for tier, paths in FILES.items():
        rows = load(paths["swarm"])["summary"]
        by = {(r["triage"], r["specialist"]): r for r in rows}
        oo = by[("object", "object")]["asr"]
        oe = by[("object", "endorse")]["asr"]
        eo = by[("endorse", "object")]["asr"]
        ee = by[("endorse", "endorse")]["asr"]
        lines.append(
            f"| {tier} | {fmt(oo)} | {fmt(oe)} | {fmt(eo)} | {fmt(ee)} | "
            f"{fmt(oe - oo)} | {fmt(eo - oo)} |"
        )
    lines.append("")


def section_pipeline(lines: list[str]) -> None:
    lines.append("## Pipeline: object/object remains high")
    lines.append("")
    lines.append("| upstream | O/O | O/E | E/O | E/E | E/E - O/O | object/object rule |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for tier, paths in FILES.items():
        rows = load(paths["pipeline"])["summary"]
        by = {(r["audit"], r["plan"]): r for r in rows}
        oo = by[("object", "object")]["asr"]
        oe = by[("object", "endorse")]["asr"]
        eo = by[("endorse", "object")]["asr"]
        ee = by[("endorse", "endorse")]["asr"]
        oor = by[("object", "object")]["rule_asr"]
        lines.append(
            f"| {tier} | {fmt(oo)} | {fmt(oe)} | {fmt(eo)} | {fmt(ee)} | "
            f"{fmt(ee - oo)} | {fmt(oor)} |"
        )
    lines.append("")


def pipeline_object_examples(lines: list[str], max_examples: int = 2) -> None:
    lines.append("## Pipeline object/object examples")
    lines.append("")
    for tier, paths in FILES.items():
        rows = load(paths["pipeline"])["records"]
        oo = [
            r for r in rows
            if not r["audit_endorse"] and not r["plan_endorse"] and r["hijacked"]
        ][:max_examples]
        lines.append(f"### {tier}")
        for r in oo:
            audit = " ".join(r["audit"].split())[:260]
            plan = " ".join(r["plan"].split())[:260]
            final = " ".join(r["final_text"].split())[:260]
            lines.append(
                f"- pid={r['payload_id']} grade={r['grade']} rule={r['rule_hijacked']} tool={r['target_tool']}\n"
                f"  - audit: {audit}\n"
                f"  - plan: {plan}\n"
                f"  - final: {final}"
            )
        lines.append("")


def trace_inventory(lines: list[str]) -> None:
    lines.append("## Trace inventory")
    lines.append("")
    traces = sorted((LOGS / "llm_traces").glob("formal25_20260627_225644_*.jsonl"))
    total_calls = 0
    total_bytes = 0
    for path in traces:
        calls = sum(1 for _ in open(path, encoding="utf-8"))
        total_calls += calls
        total_bytes += path.stat().st_size
    lines.append(f"- formal trace files: {len(traces)}")
    lines.append(f"- formal LLM calls: {total_calls}")
    lines.append(f"- trace bytes: {total_bytes}")
    lines.append("")


def main() -> int:
    lines = [
        "# Formal25 Analysis",
        "",
        "This is a derived analysis over the completed formal25 run. It does not make new API calls.",
        "",
    ]
    section_groupchat(lines)
    section_swarm(lines)
    section_pipeline(lines)
    pipeline_object_examples(lines)
    trace_inventory(lines)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
