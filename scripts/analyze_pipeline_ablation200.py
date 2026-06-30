from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "logs"
DATA = ROOT / "data" / "paradox_dataset_500.json"
OUT = LOGS / "pipeline_ablation200_analysis.md"

TIERS = {
    "low": "low_llama31_8b",
    "mid": "mid_llama31_70b",
    "high": "high_deepseek_v3",
}

BASELINE500 = {
    "low": LOGS / "pipeline500_baseline_low_llama31_8b.json",
    "mid": LOGS / "pipeline500_baseline_mid_llama31_70b.json",
    "high": LOGS / "pipeline500_baseline_high_deepseek_v3.json",
}

VISIBILITY500_LOW = LOGS / "pipeline500_visibility_low_llama31_8b.json"


def load(path: Path) -> dict:
    return json.load(open(path, encoding="utf-8"))


def sample_ids_from(path: Path) -> set:
    data = load(path)
    ids = data.get("sample", {}).get("distribution", {}).get("ids")
    if ids:
        return {int(x) for x in ids}
    return {int(r["payload_id"]) for r in data.get("records", [])}


def records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return load(path).get("records", [])


def ablation_records(variant: str, tier: str, label: str) -> list[dict]:
    if variant == "visibility" and tier == "low" and VISIBILITY500_LOW.exists():
        return records(VISIBILITY500_LOW)
    return records(LOGS / f"pipeline_ablation200_{variant}_{label}.json")


def summarize(recs: list[dict], ids: set[int] | None = None) -> dict:
    out = {}
    for audit_endorse in (False, True):
        for plan_endorse in (False, True):
            key = ("endorse" if audit_endorse else "object", "endorse" if plan_endorse else "object")
            rs = [
                r for r in recs
                if r.get("audit_endorse") == audit_endorse
                and r.get("plan_endorse") == plan_endorse
                and (ids is None or int(r.get("payload_id", -1)) in ids)
            ]
            judged = [r for r in rs if r.get("hijacked") is not None]
            if judged:
                asr = sum(int(r["hijacked"]) for r in judged) / len(judged)
                rule = sum(int(r.get("rule_hijacked") or 0) for r in judged) / len(judged)
                grade = sum(float(r.get("grade") or 0) for r in judged) / len(judged)
            else:
                asr = rule = grade = None
            out[key] = {
                "n_total": len(rs),
                "n_judged": len(judged),
                "n_errors": len(rs) - len(judged),
                "asr": asr,
                "rule_asr": rule,
                "mean_grade": grade,
            }
    return out


def fmt(x, digits: int = 3) -> str:
    return "NA" if x is None else f"{x:.{digits}f}"


def cell(table: dict, cond: tuple[str, str], key: str) -> str:
    return fmt(table[cond][key])


def ncell(table: dict, cond: tuple[str, str]) -> str:
    r = table[cond]
    return f"{r['n_judged']}/{r['n_total']}"


def main() -> int:
    # Prefer the ablation200 sample ids if any run has completed; otherwise use the deterministic 200 ids
    # from payload_sampling by importing the project utility.
    sample_ids = None
    for label in TIERS.values():
        p = LOGS / f"pipeline_ablation200_visibility_{label}.json"
        if p.exists():
            sample_ids = sample_ids_from(p)
            break
    if sample_ids is None:
        import sys
        sys.path.insert(0, str(ROOT / "src"))
        from payload_sampling import load_payload_sample
        rows, _meta = load_payload_sample(str(DATA), 200, "stratified", 42, "")
        sample_ids = {int(r["id"]) for r in rows}

    lines = [
        "# Pipeline Ablation200 Analysis",
        "",
        "Baseline is sliced from completed pipeline500 baseline runs using the same 200 stratified payload ids.",
        "Ablation rows exclude failed API/error records and report judged/total for transparency.",
        "",
        "## Object/Object",
        "",
        "| tier | baseline ASR | visibility ASR | refusal-only ASR | baseline rule | visibility rule | refusal rule | visibility n | refusal n |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    tables = {}
    for tier, label in TIERS.items():
        b = summarize(records(BASELINE500[tier]), sample_ids)
        v = summarize(ablation_records("visibility", tier, label), sample_ids)
        r = summarize(ablation_records("refusal_only", tier, label), sample_ids)
        tables[(tier, "baseline")] = b
        tables[(tier, "visibility")] = v
        tables[(tier, "refusal_only")] = r
        cond = ("object", "object")
        lines.append(
            f"| {tier} | {cell(b, cond, 'asr')} | {cell(v, cond, 'asr')} | {cell(r, cond, 'asr')} | "
            f"{cell(b, cond, 'rule_asr')} | {cell(v, cond, 'rule_asr')} | {cell(r, cond, 'rule_asr')} | "
            f"{ncell(v, cond)} | {ncell(r, cond)} |"
        )

    lines += [
        "",
        "## All Conditions",
        "",
    ]
    for tier in ("low", "mid", "high"):
        lines += [
            f"### {tier}",
            "",
            "| variant | condition | ASR | rule ASR | mean grade | judged/total |",
            "|---|---|---:|---:|---:|---:|",
        ]
        for variant in ("baseline", "visibility", "refusal_only"):
            tab = tables[(tier, variant)]
            for cond in (("object", "object"), ("object", "endorse"), ("endorse", "object"), ("endorse", "endorse")):
                c = f"{cond[0]}/{cond[1]}"
                lines.append(
                    f"| {variant} | {c} | {cell(tab, cond, 'asr')} | {cell(tab, cond, 'rule_asr')} | "
                    f"{cell(tab, cond, 'mean_grade')} | {ncell(tab, cond)} |"
                )
        lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")
    print("\n".join(lines[:14]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
