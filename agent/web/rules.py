"""The agent's reading of a run: direction-aware, and judged against measured noise.

Today `check_by_min_max_0_1` fails a metric when it leaves [min, max] of recent golden
runs in either direction, so a faster run fails too, and a min/max band can be narrower
than the test's own run-to-run noise. The agent re-reads each failing decision:

1. Direction: is the move better or worse? Guessed from the metric name until
   per-service config declares it (PLAN.md 5.7).
2. Noise: for worse moves, is the value outside the metric's normal range? The range is
   the agent's own band from comparable history (same test, last NOISE_DAYS days, PR
   runs excluded): median +/- max(NOISE_FLOOR_PCT of the median, NOISE_K x robust sigma),
   robust sigma = 1.4826 x MAD. This is the band PLAN.md 5.2 proposes for `opl`; here it
   only drives the label, not Jenkins' verdict.

The UI shows both so a reviewer can see why a run was labelled.
"""

from __future__ import annotations

import os
import re
import statistics
from dataclasses import dataclass

from .es import Decision, Run

NOISE_FLOOR_PCT = float(os.environ.get("NOISE_FLOOR_PCT", "5"))
NOISE_K = float(os.environ.get("NOISE_K", "3"))
NOISE_MIN_RUNS = int(os.environ.get("NOISE_MIN_RUNS", "5"))
NOISE_DAYS = int(os.environ.get("NOISE_DAYS", "30"))
# Metrics whose normal value is ~0 have no relative band; they use an absolute limit
# (PLAN.md 5.7), matched on the last part of the name. Others with median 0 stay unknown.
ABSOLUTE_LIMITS = {"fail_ratio": 0.01}

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


# Labels assess() can return, in the order the UI lists them.
LABELS = ("REGRESSION", "NOISE", "IMPROVED", "UNCLEAR", "ERROR", "PASS")


@dataclass
class NoiseBand:
    """A metric's normal range in comparable history."""
    n: int
    median: float
    lower: float
    upper: float
    half_width_pct: float     # band half-width as % of the median
    robust_cv_pct: float
    basis: str                # "floor" (NOISE_FLOOR_PCT won) or "noise" (k x robust sigma won)


def noise_band(values: list[float]) -> NoiseBand | None:
    """median +/- max(floor% of median, k x 1.4826 x MAD); None if too few runs or median ~0."""
    if len(values) < NOISE_MIN_RUNS:
        return None
    med = statistics.median(values)
    if abs(med) < 1e-9:
        return None
    sigma = 1.4826 * statistics.median(abs(v - med) for v in values)
    floor = NOISE_FLOOR_PCT / 100 * abs(med)
    half = max(floor, NOISE_K * sigma)
    lower = med - half
    if min(values) >= 0:  # counts, latencies, ratios can't go below zero
        lower = max(lower, 0.0)
    return NoiseBand(len(values), med, lower, med + half, 100 * half / abs(med),
                     100 * sigma / abs(med), "floor" if floor >= NOISE_K * sigma else "noise")


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
    noise: NoiseBand | None = None
    beyond_noise: bool | None = None  # for worse moves: outside the normal range? None = unknown
    vs_median_pct: float | None = None

    @property
    def arrow(self) -> str:
        """Which way the value moved out of the band: up or down. Color shows good or bad."""
        return {"above": "▲", "below": "▼"}.get(self.side or "", "")

    @property
    def short_name(self) -> str:
        """Last part of the metric name, with its parent when the last part is a generic
        statistic (measurements.x.cpu.mean -> cpu.mean)."""
        parts = self.decision.metric.split(".")
        generic = {"mean", "median", "max", "min", "avg", "sum", "stdev", "iqr", "range"}
        return ".".join(parts[-2:]) if parts[-1] in generic and len(parts) > 1 else parts[-1]


def judge_noise(r: MetricReading, band: NoiseBand | None) -> MetricReading:
    """Fill in whether a worse move is beyond the metric's normal range."""
    d = r.decision
    if r.verdict != "worse" or d.value is None:
        r.noise = band
        return r
    limit = ABSOLUTE_LIMITS.get(d.metric.split(".")[-1])
    if limit is not None and r.better == "lower":
        r.beyond_noise = d.value > limit
    elif band is not None:
        r.noise = band
        r.vs_median_pct = 100 * (d.value - band.median) / abs(band.median)
        r.beyond_noise = d.value > band.upper if r.better == "lower" else d.value < band.lower
    return r


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


def evaluate(run: Run, all_metrics: bool = False) -> Assessment:
    """assess() plus the noise check. Fetches comparable history only for worse metrics
    (enough for the label), or for every metric when `all_metrics` (run page)."""
    from . import es

    readings = [read_decision(d) for d in run.decisions]
    worse = [r.decision.metric for r in readings if all_metrics or r.verdict == "worse"]
    bands: dict[str, NoiseBand | None] = {}
    if worse and run.status:
        _, hist = es.comparable_history(run, worse, size=50, days=NOISE_DAYS)
        for m, points in hist.items():
            values = [p["value"] for p in points
                      if p.get("build_url") != run.build_url and not p.get("pr")
                      and p.get("run_result") != "ERROR"
                      and isinstance(p.get("value"), (int, float)) and not isinstance(p.get("value"), bool)]
            bands[m] = noise_band(values)
    return assess(run, bands)


def evaluate_many(runs: list[Run], workers: int = 8) -> list[Assessment]:
    """evaluate() for a list of runs; history queries run in parallel, order is kept."""
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(evaluate, runs))


def assess(run: Run, bands: dict[str, NoiseBand | None] | None = None) -> Assessment:
    """Label a run. Without `bands` (no history fetched), worse moves count as regressions."""
    readings = [read_decision(d) for d in run.decisions]
    if bands is not None:
        readings = [judge_noise(r, bands.get(r.decision.metric)) for r in readings]
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
        beyond = [r for r in worse if r.beyond_noise is not False]  # unknown counts as beyond
        if beyond:
            unknown = sum(r.beyond_noise is None for r in beyond)
            return Assessment("REGRESSION", "requires_investigation",
                              f"{len(beyond)} metric(s) moved in the worse direction beyond normal noise"
                              + (f" ({unknown} with too little history to tell)" if unknown else "")
                              + (f", {len(worse) - len(beyond)} worse but within noise" if len(worse) > len(beyond) else "")
                              + (f", {len(better)} improved" if better else "") + ".", readings)
        return Assessment("NOISE", "possible_baseline_false_positive",
                          f"{len(worse)} metric(s) moved in the worse direction, but each is within its normal "
                          f"run-to-run range (median ± max({NOISE_FLOOR_PCT:g}%, {NOISE_K:g}× robust sigma) over "
                          f"comparable runs of the last {NOISE_DAYS} days). The min/max band is tighter than "
                          "the test's own noise.", readings)
    if better and not unknown:
        return Assessment("IMPROVED", "possible_baseline_false_positive",
                          f"All {len(better)} failing metric(s) moved in the better direction. "
                          "Today's two-sided check fails these; the baseline may be stale.", readings)
    return Assessment("UNCLEAR", "requires_investigation",
                      "Direction unknown for some failing metrics; needs a human look.", readings)
