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


def test_image_changes_see_rebuilds_behind_moving_tags():
    from agent.web.es import image_changes
    spicedb = '"quay.io/x/spicedb:latest"'  # status data stores this one with quotes
    before = {"images": {"api": "quay.io/x/api:534e583", "spicedb": spicedb},
              "image_builds": {"api": "2026-11-12T17:34", "spicedb": "2026-11-10T13:25"}}
    same = {"images": dict(before["images"]), "image_builds": dict(before["image_builds"])}
    assert image_changes(same, before) == ([], [])
    rebuilt = {"images": dict(before["images"]), "image_builds": {**before["image_builds"], "spicedb": "2026-11-19T09:00"}}
    assert image_changes(rebuilt, before) == (["spicedb (rebuilt behind the same tag)"], [])
    new_tag = {"images": {**before["images"], "api": "quay.io/x/api:aaaaaaa"}, "image_builds": before["image_builds"]}
    assert image_changes(new_tag, before)[0] == ["api"]
    no_builds = {"images": before["images"]}
    assert image_changes(no_builds, {"images": before["images"]}) == ([], ["spicedb"])


def test_baseline_needs_a_pass_run_that_pass_or_fail_checked(monkeypatch):
    from agent.web import es
    # InsightsKesselK6_runnerAPI #4730 after a review passed #4726 (no decisions) to start the
    # baseline: #4726 wasn't history when #4730 ran, so #4730 stays NO_BASELINE.
    r = Run("https://j/job/K/4730/", "K", "4730", "2026-11-23T08:01:51")
    r.status = {"index": "i", "ended": "2026-11-23T08:01:51+00:00", "identity": {"name": "t"}}
    seeded = {"_source": {"results": {"jenkins": {"build_url": "https://j/job/K/4726/"}}}}
    decisions = {"https://j/job/K/4726/": 0}

    def fake_es(method, path, body=None, ndjson=None):
        if path.endswith("/_count"):
            return {"count": sum(decisions.get(u, 0) for u in body["query"]["terms"]["build_url.keyword"])}
        return {"hits": {"hits": [seeded]}}

    monkeypatch.setattr(es, "_es", fake_es)
    assert es.has_baseline(r) is False
    decisions["https://j/job/K/4726/"] = 7  # pass_or_fail checked it: real history
    assert es.has_baseline(r) is True
    r.status = None
    assert es.has_baseline(r) is None


def test_without_status_data_pass_or_fail_decides():
    r = run("FAIL")
    assert (r.current_result, r.overridden) == ("FAIL", False)
