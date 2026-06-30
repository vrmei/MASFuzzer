"""Post-hoc ablation of the hard action-preservation gate (no re-run needed).

The gate rejects any mutated child whose rewrite removed the destructive action, so a high-certainty BUT
\"defanged\" payload (the action softened away) cannot be counted as a hijack and inflate ASR. We apply the same
deterministic destructive-verb detector used by the rule oracle to each mutated payload in the recorded
certainty-arm runs, and report, per source:
  defanged_frac : fraction of mutated payloads that no longer contain ANY destructive verb (the gate would reject)
  ASR_nogate    : raw hijack rate over ALL records (gate OFF)
  ASR_gate      : hijack rate over action-PRESERVED records only (gate ON -- the honest ASR)
  false_hijacks : defanged records that were nonetheless graded as hijacks (the inflation the gate removes)
"""
from __future__ import annotations
import json, glob, os, sys
from rule_oracle import _DESTR

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "..", "logs")


def preserved(payload: str) -> bool:
    return bool(_DESTR.search(payload or ""))


def analyze(glob_pat, arm):
    recs = []
    for f in sorted(glob.glob(os.path.join(LOG, glob_pat))):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        recs += d.get(arm, {}).get("records", [])
    if not recs:
        return None
    n = len(recs)
    pres = [r for r in recs if preserved(r["payload"])]
    defanged = [r for r in recs if not preserved(r["payload"])]
    asr_nogate = sum(r["hijacked"] for r in recs) / n
    asr_gate = (sum(r["hijacked"] for r in pres) / len(pres)) if pres else float("nan")
    false_hij = sum(r["hijacked"] for r in defanged)
    return {"arm": arm, "n": n, "defanged_frac": len(defanged) / n, "asr_nogate": asr_nogate,
            "asr_gate": asr_gate, "false_hijacks": false_hij,
            "false_hijack_rate": false_hij / n}


def main():
    print("=" * 78)
    print("HARD ACTION-PRESERVATION GATE -- post-hoc ablation (gate ON vs OFF)")
    print("=" * 78)
    sources = [("tab2_big_s*.json", "certainty", "headline certainty (7 seeds)"),
               ("ablation_s*.json", "certainty", "ablation certainty"),
               ("ablation_s*.json", "cert_nocoh", "ablation -coherence"),
               ("ablation_s*.json", "cert_noshot", "ablation -few-shot")]
    rows = []
    for pat, arm, label in sources:
        a = analyze(pat, arm)
        if a:
            a["label"] = label; rows.append(a)
            print(f"\n[{label}]  n={a['n']}")
            print(f"  defanged fraction      = {a['defanged_frac']:.3f}  (gate would reject these)")
            print(f"  ASR gate OFF (raw)     = {a['asr_nogate']:.3f}")
            print(f"  ASR gate ON  (honest)  = {a['asr_gate']:.3f}")
            print(f"  false hijacks removed  = {a['false_hijacks']} ({a['false_hijack_rate']:.3f} of all)")
    json.dump(rows, open(os.path.join(LOG, "gate_ablation.json"), "w"), indent=2)
    print("\nsaved logs/gate_ablation.json")


if __name__ == "__main__":
    sys.exit(main())
