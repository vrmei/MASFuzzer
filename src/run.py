"""Direction 5 MVE smoke run (mock; no API).

Runs >=3 seeds across N mock MAS apps, computes the two survival metrics and the baseline
comparison, and prints mean+/-std plus a paired test:

  M = security-unique failures over a FLARE-style reliability oracle
      = count(reliability=PASS AND security=FAIL)   -> must be > 0 to live
  K = inter-agent failures unreachable by a single-agent baseline
      = (security failures found in multi-agent scope) minus (those a single-agent campaign finds)
      -> must be > 0 to live

Baselines named: FLARE (reliability oracle, same apps) and AgentFuzzer (single-agent scope).
This is mock plumbing: swap MockLLM -> a real OpenRouter client to run for real.
"""
from __future__ import annotations
import statistics

from mock_llm import MockLLM, ToolLibrary
from fuzzer import run_campaign, score_campaign

SEEDS = [0, 1, 2]              # >=3 seeds
ROUNDS = 60                    # mutation rounds per campaign

# N mock MAS apps: each = (worker capability, manager capability). Capability paradox -> higher
# worker capability is more hijackable (mother paper).
APPS = {
    "app_lowcap":  (0.30, 0.55),
    "app_midcap":  (0.60, 0.55),
    "app_highcap": (0.90, 0.55),
}

# Gap-y tool library shared across agents (Direction 2 fold-in: fabricatable out-of-library tools).
LIB = ToolLibrary(
    tools=["search", "calculator", "calendar", "email_read"],
    plausible_missing=["email_send", "wire_transfer", "exec_shell", "db_write"],
)


def _mean_std(xs):
    return statistics.mean(xs), (statistics.pstdev(xs) if len(xs) > 1 else 0.0)


def _wilcoxon_signed_rank(diffs):
    """Tiny dependency-free Wilcoxon signed-rank test (two-sided) on paired differences.

    Returns (W, n_nonzero). With our small seed*app sample we report W and the direction; a real
    run uses scipy.stats.wilcoxon. We avoid importing scipy so the smoke test has no deps.
    """
    nz = [d for d in diffs if d != 0]
    if not nz:
        return 0.0, 0
    ranks = _rank([abs(d) for d in nz])
    w_pos = sum(r for r, d in zip(ranks, nz) if d > 0)
    w_neg = sum(r for r, d in zip(ranks, nz) if d < 0)
    return min(w_pos, w_neg), len(nz)


def _rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1  # 1-based average rank for ties
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def main():
    # per-app, per-seed metrics
    M_rates = []            # PASS->security-fail rate (the FLARE increment), pooled over apps
    K_counts = []           # inter-agent-only security failures, pooled over apps
    sec_unique = []         # security-unique failure rate (security FAIL overall)
    paired_diffs = []       # per (app,seed): security_fail_rate - reliability_fail_rate

    print("=" * 74)
    print("Direction 5 MVE (mock) -- security-oriented MAS fuzzing")
    print(f"apps={list(APPS)}  seeds={SEEDS}  rounds/campaign={ROUNDS}")
    print("baselines: FLARE (reliability oracle) | AgentFuzzer (single-agent scope)")
    print("=" * 74)

    for app, (wcap, mcap) in APPS.items():
        for s in SEEDS:
            worker = MockLLM(f"{app}-worker", capability=wcap)
            manager = MockLLM(f"{app}-manager", capability=mcap)

            # OURS: multi-agent campaign (full operator library)
            multi = score_campaign(run_campaign(worker, manager, LIB, s,
                                                inter_agent=True, rounds=ROUNDS), LIB)
            # BASELINE: single-agent campaign (AgentFuzzer reachability proxy)
            single = score_campaign(run_campaign(worker, manager, LIB, s,
                                                 inter_agent=False, rounds=ROUNDS), LIB)

            n = len(multi)
            rel_fail_rate = sum(r["reliability_fail"] for r in multi) / n
            sec_fail_rate = sum(r["security_fail"] for r in multi) / n
            m_rate = sum(r["pass_to_security_fail"] for r in multi) / n

            # K: security failures the multi-agent campaign finds that the single-agent one does not.
            multi_secfails = sum(r["security_fail"] for r in multi)
            single_secfails = sum(r["security_fail"] for r in single)
            k_count = max(0, multi_secfails - single_secfails)

            M_rates.append(m_rate)
            sec_unique.append(sec_fail_rate)
            K_counts.append(k_count)
            paired_diffs.append(sec_fail_rate - rel_fail_rate)

            print(f"  {app:11s} seed={s}  rel_fail={rel_fail_rate:.3f}  "
                  f"sec_fail={sec_fail_rate:.3f}  M(PASS->sec)={m_rate:.3f}  K(inter-agent)={k_count}")

    print("-" * 74)
    m_mean, m_std = _mean_std(M_rates)
    k_mean, k_std = _mean_std(K_counts)
    su_mean, su_std = _mean_std(sec_unique)
    pd_mean, pd_std = _mean_std(paired_diffs)
    W, n_nz = _wilcoxon_signed_rank(paired_diffs)

    print(f"RESULTS over {len(M_rates)} (app x seed) cells, {len(SEEDS)} seeds:")
    print(f"  security-unique failure rate : {su_mean:.3f} +/- {su_std:.3f}")
    print(f"  M  (PASS->security-fail rate): {m_mean:.3f} +/- {m_std:.3f}   "
          f"[FLARE increment; survival needs M>0]")
    print(f"  K  (inter-agent-only fails)  : {k_mean:.2f}  +/- {k_std:.2f}    "
          f"[vs single-agent baseline; survival needs K>0]")
    print(f"  paired (security - reliability) failure-rate diff: "
          f"{pd_mean:.3f} +/- {pd_std:.3f}")
    print(f"  Wilcoxon signed-rank W={W:.1f} on n={n_nz} nonzero paired diffs "
          f"(two-sided; scipy in real run)")
    print("-" * 74)

    alive = (m_mean > 0) and (k_mean > 0)
    print(f"SURVIVAL CHECK: M>0 and K>0  ->  {'ALIVE (both > 0)' if alive else 'DEAD'}")
    if alive:
        print("  => security oracle flags trials a reliability oracle PASSes (M>0), AND")
        print("     inter-agent operators reach failures a single-agent baseline cannot (K>0).")
    print("=" * 74)
    return 0 if alive else 1


if __name__ == "__main__":
    raise SystemExit(main())
