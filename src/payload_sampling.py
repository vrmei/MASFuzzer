"""Reproducible payload sampling utilities for formal intervention runs."""
from __future__ import annotations

import collections
import json
import random
from typing import Iterable


def _round_robin_take(groups: dict[str, list[dict]], n: int, rng: random.Random) -> list[dict]:
    buckets = []
    for key in sorted(groups):
        bucket = list(groups[key])
        rng.shuffle(bucket)
        if bucket:
            buckets.append((key, bucket))

    selected = []
    while buckets and len(selected) < n:
        next_buckets = []
        for key, bucket in buckets:
            if len(selected) >= n:
                next_buckets.append((key, bucket))
                continue
            selected.append(bucket.pop())
            if bucket:
                next_buckets.append((key, bucket))
        buckets = next_buckets
    return selected


def _balanced_strategy_tool(rows: list[dict], n: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    by_strategy: dict[str, list[dict]] = collections.defaultdict(list)
    for row in rows:
        by_strategy[row.get("strategy", "?")].append(row)

    strategies = sorted(by_strategy)
    base, extra = divmod(n, len(strategies))
    quotas = {strategy: base + (1 if i < extra else 0) for i, strategy in enumerate(strategies)}

    selected: list[dict] = []
    leftovers: list[dict] = []
    for strategy in strategies:
        by_tool: dict[str, list[dict]] = collections.defaultdict(list)
        for row in by_strategy[strategy]:
            by_tool[row.get("target_tool", "?")].append(row)
        chosen = _round_robin_take(by_tool, min(quotas[strategy], len(by_strategy[strategy])), rng)
        selected.extend(chosen)
        chosen_ids = {row.get("id") for row in chosen}
        leftovers.extend([row for row in by_strategy[strategy] if row.get("id") not in chosen_ids])

    if len(selected) < n:
        rng.shuffle(leftovers)
        selected.extend(leftovers[: n - len(selected)])

    selected = selected[:n]
    selected.sort(key=lambda row: int(row["id"]) if str(row.get("id", "")).isdigit() else str(row.get("id", "")))
    return selected


def payload_distribution(rows: Iterable[dict]) -> dict:
    rows = list(rows)
    return {
        "n": len(rows),
        "ids": [row.get("id") for row in rows],
        "strategy": dict(collections.Counter(row.get("strategy", "?") for row in rows).most_common()),
        "target_tool": dict(collections.Counter(row.get("target_tool", "?") for row in rows).most_common()),
        "source_company": dict(collections.Counter(row.get("source_company", "?") for row in rows).most_common()),
    }


def load_payload_sample(
    data_path: str,
    n: int,
    sample: str = "stratified",
    sample_seed: int = 42,
    payload_ids: str = "",
) -> tuple[list[dict], dict]:
    rows = json.load(open(data_path, encoding="utf-8"))
    if payload_ids:
        requested = [x.strip() for x in payload_ids.split(",") if x.strip()]
        by_id = {str(row.get("id")): row for row in rows}
        missing = [pid for pid in requested if pid not in by_id]
        if missing:
            raise ValueError(f"Unknown payload id(s): {', '.join(missing)}")
        selected = [by_id[pid] for pid in requested]
        method = "ids"
    elif sample == "first":
        selected = rows[:n]
        method = "first"
    elif sample == "random":
        rng = random.Random(sample_seed)
        selected = rng.sample(rows, min(n, len(rows)))
        selected.sort(key=lambda row: int(row["id"]) if str(row.get("id", "")).isdigit() else str(row.get("id", "")))
        method = "random"
    elif sample == "stratified":
        selected = _balanced_strategy_tool(rows, min(n, len(rows)), sample_seed)
        method = "stratified_strategy_tool"
    else:
        raise ValueError(f"Unknown sample mode: {sample}")

    meta = {
        "data_path": data_path,
        "method": method,
        "requested_n": n,
        "sample_seed": sample_seed,
        "distribution": payload_distribution(selected),
    }
    return selected, meta
