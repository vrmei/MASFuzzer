from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import behavior_judge
import rule_oracle


def load_trace(path: Path) -> list[dict]:
    rows = []
    for line in open(path, encoding="utf-8"):
        if line.strip():
            rows.append(json.loads(line))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sample-from", default="")
    args = ap.parse_args()

    trace = load_trace(Path(args.trace))
    by_seed: dict[int, dict] = defaultdict(dict)
    meta_by_seed: dict[int, dict] = {}
    errors = []

    for row in trace:
        meta = row.get("metadata") or {}
        seed = meta.get("condition_seed")
        stage = meta.get("stage")
        if seed is None or not stage:
            continue
        meta_by_seed[seed] = {k: v for k, v in meta.items() if k not in {"stage", "stage_seed"}}
        if row.get("ok"):
            by_seed[seed][stage] = row.get("response", "")
        else:
            by_seed[seed][stage + "_error"] = {
                "error_type": row.get("error_type"),
                "error": row.get("error"),
            }
            errors.append({"condition_seed": seed, "stage": stage, **by_seed[seed][stage + "_error"]})

    records = []
    for seed in sorted(by_seed):
        stages = by_seed[seed]
        meta = meta_by_seed[seed]
        if not {"audit", "plan", "decider"}.issubset(stages):
            continue
        judge_text = stages.get("behavior_judge")
        if judge_text is not None:
            parsed = behavior_judge._parse(judge_text)
            grade = parsed["grade"]
            hijacked = int(parsed["hijacked"])
            judge_error = None
        else:
            grade = -1
            hijacked = None
            judge_error = stages.get("behavior_judge_error")
        rb = rule_oracle.grade(stages["decider"], "", meta.get("target_tool", ""))
        records.append(
            {
                "payload_id": meta.get("payload_id"),
                "strategy": meta.get("strategy", ""),
                "target_tool": meta.get("target_tool", ""),
                "audit_endorse": meta.get("audit_endorse"),
                "plan_endorse": meta.get("plan_endorse"),
                "seed": seed,
                "grade": grade,
                "hijacked": hijacked,
                "judge_error": judge_error,
                "rule_score": rb["score"],
                "rule_hijacked": int(rb["hijacked"]),
                "audit": stages["audit"],
                "plan": stages["plan"],
                "final_text": stages["decider"],
            }
        )

    summary = []
    for audit_endorse in (False, True):
        for plan_endorse in (False, True):
            rs = [
                r for r in records
                if r["audit_endorse"] == audit_endorse and r["plan_endorse"] == plan_endorse
            ]
            judged = [r for r in rs if r["hijacked"] is not None]
            summary.append(
                {
                    "audit": "endorse" if audit_endorse else "object",
                    "plan": "endorse" if plan_endorse else "object",
                    "n": len(rs),
                    "n_judged": len(judged),
                    "n_judge_errors": len(rs) - len(judged),
                    "asr": sum(r["hijacked"] for r in judged) / len(judged) if judged else None,
                    "rule_asr": sum(r["rule_hijacked"] for r in rs) / len(rs) if rs else None,
                    "mean_grade": sum(r["grade"] for r in judged) / len(judged) if judged else None,
                }
            )

    sample = {}
    config = {}
    if args.sample_from:
        source = json.load(open(args.sample_from, encoding="utf-8"))
        sample = source.get("sample", {})
        config = source.get("config", {})
    out = {
        "sample": sample,
        "config": config,
        "recovered_from_trace": args.trace,
        "errors": errors,
        "summary": summary,
        "records": records,
    }
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {args.out}")
    print(f"records={len(records)} errors={len(errors)}")
    for row in summary:
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
