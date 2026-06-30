from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "logs"
OUT = LOGS / "pipeline_ablation25_analysis.md"

BASELINE = {
    "low": LOGS / "formal25_low_llama31_8b_pipeline.json",
    "mid": LOGS / "formal25_mid_llama31_70b_pipeline.json",
    "high": LOGS / "formal25_high_deepseek_v3_pipeline.json",
}

VISIBILITY = {
    "low": LOGS / "pipeline_ablation25_visibility_low_llama31_8b.json",
    "mid": LOGS / "pipeline_ablation25_visibility_mid_llama31_70b.json",
    "high": LOGS / "pipeline_ablation25_visibility_high_deepseek_v3.json",
}

REFUSAL_ONLY = {
    "low": LOGS / "pipeline_ablation25_refusal_only_low_llama31_8b.json",
    "mid": LOGS / "pipeline_ablation25_refusal_only_mid_llama31_70b.json",
    "high": LOGS / "pipeline_ablation25_refusal_only_high_deepseek_v3.rerun.json",
}


def load(path: Path) -> dict:
    return json.load(open(path, encoding="utf-8"))


def fmt(x) -> str:
    return "NA" if x is None else f"{x:.2f}"


def by_cond(path: Path) -> dict:
    rows = load(path)["summary"]
    out = {}
    for r in rows:
        out[(r["audit"], r["plan"])] = r
    return out


def oo(path: Path) -> dict:
    return by_cond(path)[("object", "object")]


def ee(path: Path) -> dict:
    return by_cond(path)[("endorse", "endorse")]


def main() -> int:
    lines = [
        "# Pipeline Ablation25 Analysis",
        "",
        "Baseline is formal25 pipeline. Ablations use the same 25 stratified payloads and upstream tiers.",
        "",
        "## Object/Object ASR",
        "",
        "| upstream | baseline ASR | visibility ASR | refusal-only ASR | baseline rule | visibility rule | refusal-only rule | refusal-only judged/errors |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for tier in ("low", "mid", "high"):
        b = oo(BASELINE[tier])
        v = oo(VISIBILITY[tier])
        r = oo(REFUSAL_ONLY[tier])
        judged = f"{r.get('n_judged', r.get('n', 0))}/{r.get('n_judge_errors', 0)}"
        lines.append(
            f"| {tier} | {fmt(b['asr'])} | {fmt(v['asr'])} | {fmt(r['asr'])} | "
            f"{fmt(b['rule_asr'])} | {fmt(v['rule_asr'])} | {fmt(r['rule_asr'])} | {judged} |"
        )

    lines += [
        "",
        "## Endorse/Endorse ASR",
        "",
        "| upstream | baseline ASR | visibility ASR | refusal-only ASR | baseline rule | visibility rule | refusal-only rule |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for tier in ("low", "mid", "high"):
        b = ee(BASELINE[tier])
        v = ee(VISIBILITY[tier])
        r = ee(REFUSAL_ONLY[tier])
        lines.append(
            f"| {tier} | {fmt(b['asr'])} | {fmt(v['asr'])} | {fmt(r['asr'])} | "
            f"{fmt(b['rule_asr'])} | {fmt(v['rule_asr'])} | {fmt(r['rule_asr'])} |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        "- If refusal-only drives object/object ASR to zero, pipeline failures are caused by objection-to-plan transduction rather than simple audit endorsement.",
        "- Visibility is a separate test: if merely showing audit+payload to the decider does not remove object/object ASR, then plan generation itself is the stronger causal lever.",
        "- The original high/refusal-only run was interrupted by 9 GPT-4o-mini judge 403 errors. The table uses the clean rerun, which completed all 100 conditions and 400/400 trace calls.",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")
    print("\n".join(lines[:20]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
