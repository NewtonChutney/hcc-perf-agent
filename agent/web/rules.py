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
3. Recurrence: a worse move beyond that band is an OUTLIER rather than a REGRESSION when
   nothing changed and it is a one-off that has happened before: the run has the same
   images as the previous normal run of the same test, that previous run was inside the
   noise band, and at least OUTLIER_MIN_SEEN earlier one-offs were at least as bad (normal
   runs of the test in the last OUTLIER_DAYS days whose next run was back inside the
   band). Requiring one-offs keeps a sustained shift a REGRESSION even once its own runs
   pile up in the history. Failure and error counts never qualify: more failures is a
   correctness signal, not a slow run. Some tests have an
   occasional slow mode (Kessel CheckForUpdateBulk: whole runs ~18% slower, then back to
   normal with the same images) that a robust band rightly treats as outside normal
   noise but that is not a code change. OUTLIER predicts environment_failure, so the run
   is kept out of the baseline instead of passed into it. Images are compared by reference
   and build time (es.image_changes), so a rebuilt `latest` counts as a change; a moving
   tag without a recorded build time means "unknown", which also rules out OUTLIER.

The UI shows all of this so a reviewer can see why a run was labelled.
"""

from __future__ import annotations

import os
import re
import statistics
from dataclasses import dataclass, field

from .es import Decision, Run

NOISE_FLOOR_PCT = float(os.environ.get("NOISE_FLOOR_PCT", "5"))
NOISE_K = float(os.environ.get("NOISE_K", "3"))
NOISE_MIN_RUNS = int(os.environ.get("NOISE_MIN_RUNS", "5"))
NOISE_DAYS = int(os.environ.get("NOISE_DAYS", "30"))
OUTLIER_DAYS = int(os.environ.get("OUTLIER_DAYS", "90"))
OUTLIER_MIN_SEEN = int(os.environ.get("OUTLIER_MIN_SEEN", "2"))
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


# What each category means, for reviewers: (meaning, use it when, ReportPortal defect type).
# The result a review sets is writeback.RESULT_FOR_CATEGORY.
CATEGORY_HELP = {
    "possible_baseline_false_positive": (
        "The service is fine; the check was wrong. Its band is stale or tighter than the test's "
        "normal run-to-run noise.",
        "Every failing metric got better, or the worse moves are within normal noise.",
        "no_defect"),
    "environment_failure": (
        "The run is invalid: something other than the code under test broke or skewed it, so it "
        "says nothing about the service.",
        "Cluster, node, database or network trouble; a rollout or restarts during the run; a "
        "recurring one-off slow run; a check errored because the run is missing data.",
        "system_issue"),
    "true_failure": (
        "A real regression, caused by the code or configuration under test.",
        "You confirmed the slowdown (or other worse move) and its cause, e.g. an image change.",
        "product_bug"),
    "known_issue": (
        "A real problem that is already tracked.",
        "The failure matches an open bug; give its URL. Later runs failing the same metrics can be "
        "matched to it.",
        "product_bug, with a bug link"),
    "requires_investigation": (
        "Not known yet; someone needs to look.",
        "Worse beyond normal noise with no explanation yet, or the direction is unclear.",
        "to_investigate"),
}

# Labels assess() can return, in the order the UI lists them, and the category each predicts.
LABELS = ("REGRESSION", "OUTLIER", "NOISE", "IMPROVED", "UNCLEAR", "ERROR", "PASS")
LABEL_CATEGORY = {
    "REGRESSION": "requires_investigation",
    "OUTLIER": "environment_failure",
    "NOISE": "possible_baseline_false_positive",
    "IMPROVED": "possible_baseline_false_positive",
    "UNCLEAR": "requires_investigation",
    "ERROR": "environment_failure",
    "PASS": None,
}


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
    seen: int | None = None           # beyond noise: normal runs at least this bad in OUTLIER_DAYS
    seen_last: str | None = None      # the latest of those, as a build number

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
    label: str              # one of LABELS
    summary: str
    readings: list[MetricReading]

    @property
    def predicted_category(self) -> str | None:
        return LABEL_CATEGORY[self.label]


@dataclass
class Recurrence:
    """Evidence for telling a recurring outlier from a regression (rule 3 above)."""
    previous_build: str | None         # latest earlier normal run of the same test
    image_changes: list[str] | None    # pods whose image differs from that run; None = unknown
    seen: dict[str, tuple[int, str | None]]  # metric -> (earlier one-offs at least as bad, latest build)
    sustained: list[str]               # metrics where the previous run was beyond the band too
    image_unknown: list[str] = field(default_factory=list)  # moving tag, no build time: can't tell


# Metrics that never make a run an OUTLIER (rule 3).
_NOT_OUTLIER = re.compile(r"fail|error|exception|timeout", re.I)


def _build(url: str | None) -> str | None:
    return url.rstrip("/").split("/")[-1] if url else None


def recurrence(run: Run, readings: list[MetricReading]) -> Recurrence | None:
    """Look back OUTLIER_DAYS for the metrics that are worse beyond their noise band."""
    from . import es

    beyond = [r for r in readings if r.beyond_noise and r.noise is not None]
    if not beyond or not run.status:
        return None
    _, hist = es.comparable_history(run, [r.decision.metric for r in beyond], size=500,
                                    days=OUTLIER_DAYS, with_decisions=False)
    seen, sustained = {}, []
    previous = None
    for r in beyond:
        lower_better = r.better == "lower"

        def num(p):
            v = p.get("value")
            return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None

        def in_band(v):
            return v is not None and (v <= r.noise.upper if lower_better else v >= r.noise.lower)

        def as_bad(v):
            return v is not None and (v >= r.decision.value if lower_better else v <= r.decision.value)

        normal = [p for p in hist.get(r.decision.metric, [])
                  if not p.get("pr") and p.get("ended") != run.status.get("ended")
                  and p.get("build_url") != run.build_url and num(p) is not None]
        if not normal:
            continue
        previous = normal[-1]
        if not in_band(num(previous)):
            sustained.append(r.decision.metric)
        one_offs = [p for p, nxt in zip(normal, normal[1:]) if as_bad(num(p)) and in_band(num(nxt))]
        seen[r.decision.metric] = (len(one_offs), _build(one_offs[-1].get("build_url")) if one_offs else None)
    changes, unknown = None, []
    if previous and previous.get("images") and run.status.get("images"):
        changes, unknown = es.image_changes(run.status, previous)
    return Recurrence(_build(previous.get("build_url")) if previous else None, changes, seen, sustained, unknown)


def evaluate(run: Run, all_metrics: bool = False) -> Assessment:
    """assess() plus the noise check. Fetches comparable history only for worse metrics
    (enough for the label), or for every metric when `all_metrics` (run page)."""
    from . import es

    readings = [read_decision(d) for d in run.decisions]
    worse = [r.decision.metric for r in readings if all_metrics or r.verdict == "worse"]
    bands: dict[str, NoiseBand | None] = {}
    if worse and run.status:
        # Values come from status data; the decisions join isn't needed for a band.
        _, hist = es.comparable_history(run, worse, size=50, days=NOISE_DAYS, with_decisions=False)
        for m, points in hist.items():
            values = [p["value"] for p in points
                      if p.get("build_url") != run.build_url and p.get("ended") != run.status.get("ended")
                      and not p.get("pr")
                      and p.get("run_result") != "ERROR"
                      and isinstance(p.get("value"), (int, float)) and not isinstance(p.get("value"), bool)]
            bands[m] = noise_band(values)
    rec = recurrence(run, [judge_noise(r, bands.get(r.decision.metric)) for r in readings]) if bands else None
    return assess(run, bands, rec)


def evaluate_many(runs: list[Run], workers: int = 8) -> list[Assessment]:
    """evaluate() for a list of runs; history queries run in parallel, order is kept."""
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(_evaluate_or_fallback, runs))


def _evaluate_or_fallback(run: Run) -> Assessment:
    """One run's history failing to load shouldn't blank a whole list: label it without
    the noise check (worse moves count as regressions) and say so."""
    import requests

    try:
        return evaluate(run)
    except requests.RequestException:
        a = assess(run)
        a.summary += " (History didn't load, so this label skips the noise check; reload to retry.)"
        return a


def assess(run: Run, bands: dict[str, NoiseBand | None] | None = None,
           rec: Recurrence | None = None) -> Assessment:
    """Label a run. Without `bands` (no history fetched), worse moves count as regressions;
    without `rec`, moves beyond noise do."""
    readings = [read_decision(d) for d in run.decisions]
    if bands is not None:
        readings = [judge_noise(r, bands.get(r.decision.metric)) for r in readings]
    if rec is not None:
        for r in readings:
            if r.decision.metric in rec.seen and r.beyond_noise:
                r.seen, r.seen_last = rec.seen[r.decision.metric]
    failed = [r for r in readings if r.decision.result == "FAIL"]
    if run.result == "ERROR":
        return Assessment("ERROR", "pass_or_fail errored; check the Jenkins console.", readings)
    if not failed:
        return Assessment("PASS", "All gated metrics are inside their bands.", readings)
    worse = [r for r in failed if r.verdict == "worse"]
    better = [r for r in failed if r.verdict == "better"]
    unknown = [r for r in failed if r.verdict == "unknown"]
    if worse:
        beyond = [r for r in worse if r.beyond_noise is not False]  # unknown counts as beyond
        if beyond:
            unknown = sum(r.beyond_noise is None for r in beyond)
            moved = (f"{len(beyond)} metric(s) moved in the worse direction beyond normal noise"
                     + (f" ({unknown} with too little history to tell)" if unknown else "")
                     + (f", {len(worse) - len(beyond)} worse but within noise" if len(worse) > len(beyond) else "")
                     + (f", {len(better)} improved" if better else ""))
            prev = f"#{rec.previous_build}" if rec and rec.previous_build else "the previous run"
            failures = [r.short_name for r in beyond if _NOT_OUTLIER.search(r.decision.metric)]
            if (rec and rec.image_changes == [] and not rec.image_unknown and not rec.sustained and not failures
                    and all(r.seen is not None and r.seen >= OUTLIER_MIN_SEEN for r in beyond)):
                seen = ", ".join(f"{r.short_name} {r.seen} runs" + (f" (latest #{r.seen_last})" if r.seen_last else "")
                                 for r in beyond)
                return Assessment("OUTLIER",
                                  f"{moved}, but nothing changed and it has happened before: same images as {prev}, "
                                  f"which was normal, and one-off runs of this test at least this bad (next run back "
                                  f"to normal) in the last {OUTLIER_DAYS} days: {seen}. Looks like a recurring one-off "
                                  "run, not a code change; keep it out of the baseline.", readings)
            if rec and rec.image_changes:
                why = f" Images changed since {prev}: {', '.join(rec.image_changes)}."
            elif rec and rec.image_changes == [] and rec.image_unknown:
                why = (f" No image tag changed since {prev}, but {', '.join(rec.image_unknown)} use a moving tag with "
                       "no build time recorded, so whether the code changed is unknown.")
            elif rec and rec.image_changes == [] and failures:
                why = f" Same images as {prev}, but failures rose ({', '.join(failures)}), which is never treated as a one-off."
            elif rec and rec.image_changes == [] and rec.sustained:
                why = f" Same images as {prev}, but {prev} was beyond normal noise too: a sustained shift, not a one-off."
            elif rec and rec.image_changes == []:
                seen = ", ".join(f"{r.short_name} {r.seen}" if r.seen is not None else f"{r.short_name} unknown"
                                 for r in beyond)
                why = (f" Same images as {prev}, but fewer than {OUTLIER_MIN_SEEN} earlier one-offs this bad in "
                       f"the last {OUTLIER_DAYS} days ({seen}).")
            else:
                why = ""
            return Assessment("REGRESSION", moved + "." + why, readings)
        return Assessment("NOISE",
                          f"{len(worse)} metric(s) moved in the worse direction, but each is within its normal "
                          f"run-to-run range (median ± max({NOISE_FLOOR_PCT:g}%, {NOISE_K:g}× robust sigma) over "
                          f"comparable runs of the last {NOISE_DAYS} days). The min/max band is tighter than "
                          "the test's own noise.", readings)
    if better and not unknown:
        return Assessment("IMPROVED",
                          f"All {len(better)} failing metric(s) moved in the better direction. "
                          "Today's two-sided check fails these; the baseline may be stale.", readings)
    return Assessment("UNCLEAR", "Direction unknown for some failing metrics; needs a human look.", readings)
