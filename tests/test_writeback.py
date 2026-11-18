from agent.web import writeback
from agent.web.es import Run


def run_with_status(result="FAIL"):
    r = Run("https://j/job/X/1/", "X", "1", "2026-11-18T05:18:14")
    r.status = {"index": "idx", "doc_id": "d1", "id": "2026-11-18T05_11_07", "result": result}
    return r


def test_mapping_matches_reportportal_sync():
    # opl/status_data_updater.py RP_TO_ES_STATE: no_defect PASS, system_issue ERROR, else FAIL.
    assert writeback.RESULT_FOR_CATEGORY == {
        "possible_baseline_false_positive": "PASS", "environment_failure": "ERROR",
        "true_failure": "FAIL", "known_issue": "FAIL", "requires_investigation": "FAIL"}


def test_switch_and_allowlist(monkeypatch):
    monkeypatch.setenv("WRITEBACK_USERS", "nmucheli,alice")
    monkeypatch.setenv("WRITEBACK_ENABLED", "false")
    assert not writeback.allowed("nmucheli@cluster.local")
    assert writeback.apply(run_with_status(), "true_failure", "nmucheli")["status"] == "disabled"
    monkeypatch.setenv("WRITEBACK_ENABLED", "true")
    assert writeback.allowed("nmucheli@cluster.local") and writeback.allowed("alice")
    assert not writeback.allowed("mallory@cluster.local") and not writeback.allowed(None)
    assert writeback.apply(run_with_status(), "true_failure", "mallory")["status"] == "not_allowed"
    monkeypatch.setenv("WRITEBACK_USERS", "*")
    assert writeback.allowed("anyone@cluster.local")


def test_planned():
    assert writeback.planned(run_with_status("FAIL"), "possible_baseline_false_positive") == \
        {"old": "FAIL", "new": "PASS", "changes": True}
    assert writeback.planned(run_with_status("FAIL"), "requires_investigation")["changes"] is False
