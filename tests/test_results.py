from agent.web.es import Decision, Run, matches_result


def run(said, stored=None):
    r = Run("https://j/job/X/1/", "X", "1", "2026-11-18T05:18:14",
            [Decision("m", said, "check_by_min_max_0_1", 1, 0, 2, "2026-11-18T05:18:14")])
    r.status = {"result": stored} if stored else None
    return r


def test_review_override_is_the_current_result():
    r = run("FAIL", "PASS")
    assert (r.current_result, r.overridden) == ("PASS", True)
    assert matches_result(r, "FAIL-PASS") and matches_result(r, "PASS")
    assert not matches_result(r, "FAIL")


def test_still_failing_is_FAIL_only():
    r = run("FAIL", "FAIL")
    assert matches_result(r, "FAIL") and not matches_result(r, "FAIL-PASS")


def test_pipeline_storing_ERROR_as_FAIL_is_not_an_override():
    r = run("ERROR", "FAIL")
    assert (r.current_result, r.overridden) == ("ERROR", False)
    assert matches_result(r, "ERROR") and not matches_result(r, "FAIL")


def test_without_status_data_pass_or_fail_decides():
    r = run("FAIL")
    assert (r.current_result, r.overridden) == ("FAIL", False)
