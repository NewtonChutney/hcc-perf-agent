from agent.web import writeback
from agent.web.es import Run


def run_with_status(result="FAIL"):
    r = Run("https://j/job/X/1/", "X", "1", "2026-11-18T05:18:14")
    r.status = {"index": "idx", "doc_id": "d1", "id": "2026-11-18T05_11_07", "result": result}
    return r


def test_mapping_matches_reportportal_sync():
    # opl/status_data_updater.py RP_TO_ES_STATE: no_defect PASS, system_issue ERROR, else FAIL;
    # except automation_bug, which RP set to FAIL and we set to ERROR.
    assert writeback.RESULT_FOR_CATEGORY == {
        "false_positive": "PASS", "environment_failure": "ERROR", "automation_bug": "ERROR",
        "new_issue": "FAIL", "known_issue": "FAIL", "requires_investigation": "FAIL"}


def test_old_category_names_are_read_as_new():
    from agent.web.es import _review
    doc = _review({"category": "possible_baseline_false_positive", "predicted_category": "true_failure"})
    assert doc == {"category": "false_positive", "predicted_category": "new_issue"}


def test_switch_and_allowlist(monkeypatch):
    monkeypatch.setenv("WRITEBACK_USERS", "nmucheli,alice")
    monkeypatch.setenv("WRITEBACK_ENABLED", "false")
    assert not writeback.allowed("nmucheli@cluster.local")
    assert writeback.apply(run_with_status(), "new_issue", "nmucheli")["status"] == "disabled"
    monkeypatch.setenv("WRITEBACK_ENABLED", "true")
    assert writeback.allowed("nmucheli@cluster.local") and writeback.allowed("alice")
    assert not writeback.allowed("mallory@cluster.local") and not writeback.allowed(None)
    assert writeback.apply(run_with_status(), "new_issue", "mallory")["status"] == "not_allowed"
    monkeypatch.setenv("WRITEBACK_USERS", "*")
    assert writeback.allowed("anyone@cluster.local")


def test_load_window_covers_upload_only_timestamps():
    from agent.web.es import load_window
    # kessel: started/ended are the 23 s upload; parameters hold the 300 s load
    assert load_window({"started": "2026-11-18T05:17:46.11+00:00", "ended": "2026-11-18T05:18:09.93+00:00",
                        "parameters": {"start": "2026-11-18T05:11:12+00:00", "end": "2026-11-18T05:17:46+00:00"}}) \
        == ("2026-11-18T05:11:12+00:00", "2026-11-18T05:18:09.93+00:00")
    # notifications: started/ended already cover the load
    assert load_window({"started": "2026-11-12T14:03:59+00:00", "ended": "2026-11-12T14:07:01+00:00",
                        "parameters": {"start": "2026-11-12T14:05:46+00:00"},
                        "results": {"end": "2026-11-12T14:06:51+00:00"}}) \
        == ("2026-11-12T14:03:59+00:00", "2026-11-12T14:07:01+00:00")


def test_auto_apply_bar_is_per_service_and_category():
    fp = "false_positive"
    def rv(job, label, cat, said=None):
        return {"job_name": job, "predicted_label": label, "predicted_category": cat, "category": said or cat}
    reviews = ([rv("Kessel", "IMPROVED", fp)] * 7
               + [rv("Kessel", "NOISE", fp)] * 3         # same category: pooled with IMPROVED
               + [rv("Notif", "IMPROVED", fp)] * 4
               + [rv("Inv", "IMPROVED", fp)] * 18
               + [rv("Inv", "NOISE", fp, "new_issue")] * 2
               + [rv("Kessel", "REGRESSION", "requires_investigation")] * 60)
    progress = writeback.auto_apply_progress(reviews)
    got = {(p["job"], p["category"]): p["status"] for p in progress}
    assert writeback.AUTO_APPLY_MIN_REVIEWS == 10
    assert got == {
        ("Kessel", fp): "meets the bar",              # 10/10; qualifies alone, no 3-service gate
        ("Notif", fp): "6 more reviews needed",
        ("Inv", fp): "agreement below 95%",           # 18/20 = 90%
        ("Kessel", "requires_investigation"): "always reviewed by a person",
    }
    assert next(p for p in progress if p["job"] == "Kessel" and p["category"] == fp)["labels"] == \
        {"IMPROVED": 7, "NOISE": 3}


def test_planned():
    assert writeback.planned(run_with_status("FAIL"), "false_positive") == \
        {"old": "FAIL", "new": "PASS", "changes": True}
    assert writeback.planned(run_with_status("FAIL"), "requires_investigation")["changes"] is False
