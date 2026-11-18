from agent.web.es import Decision, Run
from agent.web.rules import assess, better_direction, read_decision


def d(metric, value, lower, upper, result="FAIL"):
    return Decision(metric, result, "check_by_min_max_0_1", value, lower, upper, "2026-11-18T05:18:14")


def run(*decisions):
    return Run("https://j/job/X/1/", "X", "1", "2026-11-18T05:18:14", list(decisions))


def test_direction_from_name():
    assert better_direction("results.requests.SUMMARY.95percentile") == "lower"
    assert better_direction("results.requests.SUMMARY.median_response_time") == "lower"
    assert better_direction("results.requests.SUMMARY.num_requests") == "higher"
    assert better_direction("results.requests.SUMMARY.num_failures") == "lower"
    assert better_direction("measurements.insights-engine.results.rps") == "higher"
    assert better_direction("results.something.count") is None


def test_faster_run_is_improved_not_regression():
    # InsightsKesselK6_runnerAPI #4601: p95 and median below the band, more requests.
    a = assess(run(
        d("results.requests.SUMMARY.95percentile", 370.96, 382.74, 417.59),
        d("results.requests.SUMMARY.median_response_time", 115.95, 119.41, 138.01),
        d("results.requests.SUMMARY.num_requests", 706930, 614913, 682763),
    ))
    assert a.label == "IMPROVED"
    assert a.predicted_category == "false_positive"


def test_any_worse_metric_is_regression():
    a = assess(run(
        d("results.requests.SUMMARY.95percentile", 450, 382, 417),
        d("results.requests.SUMMARY.num_requests", 706930, 614913, 682763),
    ))
    assert a.label == "REGRESSION"


def test_unknown_direction_is_unclear():
    assert assess(run(d("results.something.count", 5, 1, 2))).label == "UNCLEAR"


def test_pass_and_error():
    assert assess(run(d("x.95percentile", 1, 0, 2, "PASS"))).label == "PASS"
    assert assess(run(d("x.95percentile", None, None, None, "ERROR"))).label == "ERROR"


def test_arrow_follows_the_value_and_color_follows_the_direction():
    # More requests: value went up and that's better -> up arrow, "better".
    r = read_decision(d("results.requests.SUMMARY.num_requests", 706930, 614913, 682763))
    assert (r.arrow, r.verdict) == ("▲", "better")
    # Zero failures under a band with a minimum: value went down and that's better.
    r = read_decision(d("results.requests.SUMMARY.num_failures", 0, 3, 40))
    assert (r.arrow, r.verdict) == ("▼", "better")
    # Slower p95: up and worse.
    r = read_decision(d("results.requests.SUMMARY.95percentile", 450, 382, 417))
    assert (r.arrow, r.verdict) == ("▲", "worse")


def test_number_format_has_no_exponent():
    from agent.web.fmt import num
    assert [num(v) for v in (614913.0, 382.744, 1.6285, 0.000123456, 0, None)] == \
        ["614,913", "382.7", "1.63", "0.000123", "0", "-"]


def test_deviation_is_relative_to_band_edge():
    r = read_decision(d("x.95percentile", 110, 50, 100))
    assert (r.side, r.verdict, round(r.deviation_pct, 1)) == ("above", "worse", 10.0)


def test_noise_band_uses_the_larger_of_floor_and_measured_noise():
    from agent.web.rules import noise_band
    quiet = noise_band([100, 100.5, 99.5, 100.2, 99.8, 100.1])   # tiny spread -> 5% floor wins
    assert quiet.basis == "floor" and round(quiet.half_width_pct, 1) == 5.0
    noisy = noise_band([100, 120, 80, 110, 90, 105, 95])          # big spread -> 3 x robust sigma wins
    assert noisy.basis == "noise" and noisy.half_width_pct > 5
    assert noise_band([1, 2, 3]) is None                         # too few runs
    assert noise_band([0, 0, 0, 0, 0, 0]) is None                # median 0 -> no relative band


def test_worse_within_normal_noise_is_NOISE_not_REGRESSION():
    from agent.web.rules import noise_band
    # InsightsKesselK6_runnerAPI #4451: median_response_time 36.16 ms, min/max band 32.01-36.02,
    # comparable history median ~35.5 ms with ~2% robust CV.
    history = [35.5, 35.0, 36.1, 34.8, 35.9, 35.3, 36.3, 35.6, 34.9, 35.7]
    m = "results.requests.SUMMARY.median_response_time"
    a = assess(run(d(m, 36.157, 32.008, 36.023)), {m: noise_band(history)})
    assert a.label == "NOISE" and a.predicted_category == "false_positive"
    assert a.readings[0].beyond_noise is False
    # Well beyond the normal range stays a regression.
    assert assess(run(d(m, 45.0, 32.008, 36.023)), {m: noise_band(history)}).label == "REGRESSION"
    # No history to judge -> conservative: regression.
    assert assess(run(d(m, 36.157, 32.008, 36.023)), {m: None}).label == "REGRESSION"


def test_recurring_one_off_with_same_images_is_OUTLIER():
    from agent.web.rules import Recurrence, noise_band
    # InsightsKesselK6_runnerAPI #4594 (CheckForUpdateBulk): p95 2382 ms vs a 30-day median of
    # ~2006 ms (band +-13.5%), same images as #4582, 12 earlier one-offs this slow in 90 days.
    m = "results.requests.SUMMARY.95percentile"
    history = [2105, 2089, 2106, 2123, 1910, 1944, 1979, 2135, 1994, 1961, 2356, 1973, 1957, 1918, 1975,
               1982, 1993, 2154, 2028, 2069, 2046, 1858, 2005, 2029, 2126]
    bands = {m: noise_band(history)}
    r = run(d(m, 2382.45, 1982.19, 2380.35))
    rec = Recurrence("4582", [], {m: (12, "3245")}, [])
    a = assess(r, bands, rec)
    assert a.label == "OUTLIER" and a.predicted_category == "environment_failure"
    assert a.readings[0].seen == 12 and "#4582" in a.summary

    # Any of these keeps it a REGRESSION:
    changed = assess(r, bands, Recurrence("4582", ["kessel-inventory-api"], {m: (12, "3245")}, []))
    assert changed.label == "REGRESSION" and "kessel-inventory-api" in changed.summary
    sustained = assess(r, bands, Recurrence("4582", [], {m: (12, "3245")}, [m]))
    assert sustained.label == "REGRESSION" and "sustained" in sustained.summary
    assert assess(r, bands, Recurrence("4582", [], {m: (1, "3245")}, [])).label == "REGRESSION"
    assert assess(r, bands, Recurrence("4582", None, {m: (12, "3245")}, [])).label == "REGRESSION"
    assert assess(r, bands).label == "REGRESSION"  # no lookback


def test_failures_are_never_an_outlier():
    from agent.web.rules import Recurrence, noise_band
    m = "results.requests.SUMMARY.num_failures"
    bands = {m: noise_band([10, 11, 9, 10, 12, 10, 11])}
    a = assess(run(d(m, 40, 9, 12)), bands, Recurrence("1", [], {m: (5, "0")}, []))
    assert a.label == "REGRESSION" and "failures rose" in a.summary


def test_fail_ratio_uses_absolute_limit():
    m = "results.requests.SUMMARY.fail_ratio"
    assert assess(run(d(m, 0.004, 0, 0.001)), {m: None}).label == "NOISE"       # under 1%
    assert assess(run(d(m, 0.05, 0, 0.001)), {m: None}).label == "REGRESSION"   # over 1%
