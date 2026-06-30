from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "logs"
OUT = LOGS / "pipeline_case_studies.md"

CASES = ["32", "39"]
SOURCES = [
    ("baseline_low", LOGS / "formal25_low_llama31_8b_pipeline.json"),
    ("visibility_low", LOGS / "pipeline_ablation25_visibility_low_llama31_8b.json"),
    ("refusal_low", LOGS / "pipeline_ablation25_refusal_only_low_llama31_8b.json"),
    ("baseline_high", LOGS / "formal25_high_deepseek_v3_pipeline.json"),
    ("refusal_high", LOGS / "pipeline_ablation25_refusal_only_high_deepseek_v3.rerun.json"),
]


def shorten(text: str, n: int = 900) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[:n] + " ..."


def main() -> int:
    lines = [
        "# Pipeline Case Studies",
        "",
        "Object/object means both auditor and planner were instructed to object. These cases show how the baseline planner can still convert objection into a remediation plan.",
        "",
    ]
    for pid in CASES:
        lines.append(f"## Payload {pid}")
        lines.append("")
        for label, path in SOURCES:
            if not path.exists():
                continue
            data = json.load(open(path, encoding="utf-8"))
            matches = [
                r for r in data["records"]
                if str(r["payload_id"]) == pid and not r["audit_endorse"] and not r["plan_endorse"]
            ]
            if not matches:
                continue
            r = matches[0]
            lines.append(f"### {label}: grade={r['grade']} hijacked={r['hijacked']} rule={r['rule_hijacked']}")
            lines.append("")
            lines.append(f"- audit: {shorten(r['audit'])}")
            lines.append(f"- plan: {shorten(r['plan'])}")
            lines.append(f"- final: {shorten(r['final_text'])}")
            lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
