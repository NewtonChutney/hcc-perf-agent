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
    assert a.predicted_category == "possible_baseline_false_positive"


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
