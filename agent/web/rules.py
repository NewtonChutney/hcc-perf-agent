"""Direction-aware reading of today's two-sided `pass_or_fail` decisions.

Today `check_by_min_max_0_1` fails a metric when it leaves [min, max] of recent golden
runs in either direction, so a faster run fails too. Until per-service config declares
each metric's direction (PLAN.md 5.7), the direction is guessed from the metric name.
The guess is shown in the UI so a reviewer can see why a run was labelled.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .es import Decision, Run

# Checked in order; the first match wins (so `num_failures` is "lower is better").
_DIRECTION_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"fail|error|exception|timeout|retr(y|ies)|oom|restart", re.I), "lower"),
    (re.compile(r"rps|per_?sec|throughput|num_requests|total_requests|requests_count|processed|success", re.I), "higher"),
    (re.compile(r"percentile|p\d\d|response_time|latency|duration|time|lag|cpu|memory|mem_|max", re.I), "lower"),
]

# Categories shared with rp-triage review.py and the insights_perf_triage_reviews index.
CATEGORIES = (
    "true_failure",
    "possible_baseline_false_positive",
    "environment_failure",
    "known_issue",
    "requires_investigation",
)


def better_direction(metric: str) -> str | None:
    """'lower', 'higher', or None when the name doesn't say."""
    for pattern, direction in _DIRECTION_RULES:
        if pattern.search(metric):
            return direction
    return None


@dataclass
class MetricReading:
    decision: Decision
    better: str | None      # which direction is better
    side: str | None        # 'above' or 'below' the band, for FAIL
    verdict: str            # 'worse', 'better', 'unknown', or 'pass'
    deviation_pct: float | None  # distance outside the band, relative to the band edge


def read_decision(d: Decision) -> MetricReading:
    better = better_direction(d.metric)
    if d.result != "FAIL" or d.value is None:
        return MetricReading(d, better, None, "pass" if d.result == "PASS" else "unknown", None)
    side = None
    edge = None
    if d.upper is not None and d.value > d.upper:
        side, edge = "above", d.upper
    elif d.lower is not None and d.value < d.lower:
        side, edge = "below", d.lower
    deviation = 100 * (d.value - edge) / abs(edge) if edge else None
    if side is None or better is None:
        verdict = "unknown"
    elif (side == "above") == (better == "higher"):
        verdict = "better"
    else:
        verdict = "worse"
    return MetricReading(d, better, side, verdict, deviation)


@dataclass
class Assessment:
    label: str              # PASS, ERROR, REGRESSION, IMPROVED, UNCLEAR
    predicted_category: str | None
    summary: str
    readings: list[MetricReading]


def assess(run: Run) -> Assessment:
    readings = [read_decision(d) for d in run.decisions]
    failed = [r for r in readings if r.decision.result == "FAIL"]
    if run.result == "ERROR":
        return Assessment("ERROR", "environment_failure",
                          "pass_or_fail errored; check the Jenkins console.", readings)
    if not failed:
        return Assessment("PASS", None, "All gated metrics are inside their bands.", readings)
    worse = [r for r in failed if r.verdict == "worse"]
    better = [r for r in failed if r.verdict == "better"]
    unknown = [r for r in failed if r.verdict == "unknown"]
    if worse:
        return Assessment("REGRESSION", "requires_investigation",
                          f"{len(worse)} metric(s) moved in the worse direction"
                          + (f", {len(better)} improved" if better else "") + ".", readings)
    if better and not unknown:
        return Assessment("IMPROVED", "possible_baseline_false_positive",
                          f"All {len(better)} failing metric(s) moved in the better direction. "
                          "Today's two-sided check fails these; the baseline may be stale.", readings)
    return Assessment("UNCLEAR", "requires_investigation",
                      "Direction unknown for some failing metrics; needs a human look.", readings)
