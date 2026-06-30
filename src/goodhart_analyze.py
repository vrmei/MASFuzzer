"""Analyze the Goodhart-fix experiment (#4): does coherence-coupled fitness (cert_coh) avoid the high-certainty
ASR-reversal tail that pure-certainty (certainty) over-shoots into?

Reads goodhart_s{0,1,2}.json. Per arm (pooled over seeds): ASR, mean coherence, mean lex_norm, fraction of
candidates landing in the top certainty bin [0.8,1.0] (the reversal zone), and ASR within that zone.
Evidence for the fix: cert_coh reaches >= ASR of certainty with HIGHER coherence and FEWER candidates stuck in
the low-ASR over-certain tail.
"""
import json, os, glob
from statistics import mean, pstdev

LOGS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
ARMS = ["certainty", "cert_coh", "neutral"]


def recs(arm):
    out = []
    for f in sorted(glob.glob(os.path.join(LOGS, "goodhart_s[0-9].json"))):
        d = json.load(open(f, encoding="utf-8"))
        out += d.get(arm, {}).get("records", [])
    return out


def per_seed_asr(arm):
    vals = []
    for f in sorted(glob.glob(os.path.join(LOGS, "goodhart_s[0-9].json"))):
        d = json.load(open(f, encoding="utf-8"))
        if arm in d:
            vals.append(d[arm]["asr"])
    return vals


print("=" * 84)
print(f"{'arm':10} {'ASR (mean±std)':16} {'coh':6} {'mean_lexnorm':12} {'%in[.8,1]':10} {'ASR|[.8,1]':10} {'ASR|[.6,.8]':11}")
print("-" * 84)
for a in ARMS:
    r = recs(a)
    if not r:
        print(f"{a:10} (no data)"); continue
    asrs = per_seed_asr(a)
    top = [x for x in r if x["lex_norm"] >= 0.8]
    mid = [x for x in r if 0.6 <= x["lex_norm"] < 0.8]
    fr_top = len(top) / len(r)
    asr_top = mean([x["hijacked"] for x in top]) if top else float("nan")
    asr_mid = mean([x["hijacked"] for x in mid]) if mid else float("nan")
    print(f"{a:10} {mean(asrs):.2f} ± {pstdev(asrs):.2f}     {mean([x['coherence'] for x in r]):.2f}   "
          f"{mean([x['lex_norm'] for x in r]):.3f}        {fr_top*100:4.0f}%      "
          f"{asr_top:.2f}       {asr_mid:.2f}")
print("=" * 84)
print("Goodhart FIXED if: cert_coh ASR >= certainty ASR, cert_coh coherence > certainty, and cert_coh has a")
print("SMALLER %in[.8,1] (it stops over-shooting into the reversal tail where ASR|[.8,1] < ASR|[.6,.8]).")
