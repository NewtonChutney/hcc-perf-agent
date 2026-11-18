"""Write a review's verdict back to the run's result, replacing ReportPortal's sync.

ReportPortal used to be where people overrode results: the Jenkins job
UtilResultsFromRPToES ran `opl/status_data_updater.py --action rp-to-es`, which mapped the
RP defect type to a result (`no_defect` -> PASS, `system_issue` -> ERROR, anything else ->
FAIL), set `result` on the status-data document, and appended a `comments` entry. It also
set `result` in the `results-dashboard-data` index (`--action rp-to-dashboard-update`).
This module does the same from a review, so the next `pass_or_fail` baseline query sees
it, exactly as it saw RP overrides.

This is the only code that writes to status data. Each write:
- needs WRITEBACK_ENABLED and a reviewer listed in WRITEBACK_USERS ("*" = anyone signed in)
- uses optimistic concurrency (if_seq_no), so a concurrent edit isn't overwritten
- appends a comment with who, what, and why
- is recorded in the review document (result before and after)
"""

from __future__ import annotations

import datetime as dt
import logging
import os
from urllib.parse import quote

import requests

from . import es

# Review category -> result, mirroring RP_TO_ES_STATE in opl/status_data_updater.py.
RESULT_FOR_CATEGORY = {
    "possible_baseline_false_positive": "PASS",   # RP no_defect
    "environment_failure": "ERROR",               # RP system_issue
    "true_failure": "FAIL",                       # RP product_bug
    "known_issue": "FAIL",                        # RP product_bug with a bug link
    "requires_investigation": "FAIL",             # RP to_investigate
}
DASHBOARD_INDEX = os.environ.get("DASHBOARD_INDEX", "results-dashboard-data")

# Bar for the agent to apply a category on its own (PLAN.md 6.4 and 7), judged per service
# (Jenkins job) and category. Auto-apply itself isn't built yet; the Reviews page shows progress.
AUTO_APPLY_MIN_REVIEWS = int(os.environ.get("AUTO_APPLY_MIN_REVIEWS", "10"))
AUTO_APPLY_MIN_AGREEMENT = float(os.environ.get("AUTO_APPLY_MIN_AGREEMENT", "95"))
NEVER_AUTO = {"true_failure", "requires_investigation"}


def auto_apply_progress(reviews: list[dict]) -> list[dict]:
    """Per (job, agent category): reviews, agreement, and whether it meets the bar.

    IMPROVED and NOISE both predict possible_baseline_false_positive and count together;
    the label mix is reported so a record built mostly on one label is visible.
    """
    groups: dict[tuple[str, str], dict] = {}
    for r in reviews:
        if r.get("predicted_category"):
            g = groups.setdefault((r.get("job_name") or "?", r["predicted_category"]),
                                  {"n": 0, "agreed": 0, "labels": {}})
            g["n"] += 1
            g["agreed"] += r.get("category") == r["predicted_category"]
            label = r.get("predicted_label") or "?"
            g["labels"][label] = g["labels"].get(label, 0) + 1
    out = []
    for (job, cat), g in sorted(groups.items()):
        n, agreed = g["n"], g["agreed"]
        pct = 100 * agreed / n
        if cat in NEVER_AUTO:
            status = "always reviewed by a person"
        elif n < AUTO_APPLY_MIN_REVIEWS:
            status = f"{AUTO_APPLY_MIN_REVIEWS - n} more reviews needed"
        elif pct < AUTO_APPLY_MIN_AGREEMENT:
            status = f"agreement below {AUTO_APPLY_MIN_AGREEMENT:g}%"
        else:
            status = "meets the bar"
        out.append({"job": job, "category": cat, "labels": dict(sorted(g["labels"].items())), "reviewed": n,
                    "agreed": agreed, "pct": pct, "status": status, "eligible": status == "meets the bar"})
    return out
log = logging.getLogger("hcc-perf-agent.writeback")


def enabled() -> bool:
    return os.environ.get("WRITEBACK_ENABLED", "false").lower() == "true"


def _short(user: str) -> str:
    return (user or "").removesuffix("@cluster.local")


def allowed(user: str | None) -> bool:
    users = {u.strip() for u in os.environ.get("WRITEBACK_USERS", "").split(",") if u.strip()}
    return bool(user) and enabled() and ("*" in users or _short(user) in users or user in users)


def planned(run: es.Run, category: str | None) -> dict | None:
    """What a review with this category would do to the run's result, for the UI."""
    if not run.status or not category:
        return None
    new = RESULT_FOR_CATEGORY.get(category)
    old = run.status.get("result")
    return {"old": old, "new": new, "changes": bool(new) and new != old}


def apply(run: es.Run, category: str, reviewer: str, explanation: str = "", bug_url: str | None = None,
          predicted: str | None = None) -> dict:
    """Set the run's result from the review. Returns what happened, for the review record."""
    new = RESULT_FOR_CATEGORY.get(category)
    if not enabled():
        return {"status": "disabled"}
    if not allowed(reviewer):
        return {"status": "not_allowed"}
    if not run.status or not new:
        return {"status": "no_status_data" if not run.status else "no_mapping"}

    index, doc_id = run.status["index"], run.status["doc_id"]
    url = f"{es.ES_URL}/{index}/_doc/{quote(doc_id, safe='')}"
    r = requests.get(url, timeout=es.TIMEOUT)
    r.raise_for_status()
    got = r.json()
    doc = got["_source"]
    old = doc.get("result")
    if old == new:
        return {"status": "unchanged", "result_before": old, "result_after": new}

    text = f"Result {old} -> {new} by HCC Perf Agent review: {category}"
    if predicted and predicted != category:
        text += f" (agent suggested {predicted})"
    if explanation:
        text += f". {explanation}"
    if bug_url:
        text += f" {bug_url}"
    comments = doc.get("comments") if isinstance(doc.get("comments"), list) else []
    comments.append({"author": _short(reviewer), "date": dt.datetime.now(dt.timezone.utc).isoformat(),
                     "text": text})
    doc["comments"] = comments
    doc["result"] = new
    w = requests.put(f"{url}?if_seq_no={got['_seq_no']}&if_primary_term={got['_primary_term']}&refresh=wait_for",
                     json=doc, timeout=es.TIMEOUT)
    if w.status_code == 409:
        return {"status": "conflict", "result_before": old}
    w.raise_for_status()
    outcome = {"status": "changed", "result_before": old, "result_after": new,
               "status_index": index, "status_doc_id": doc_id,
               "dashboard": _update_dashboard(doc.get("id"), new)}
    log.info(f"writeback {run.job_name}#{run.build_number} {index}/{doc_id}: {old} -> {new} "
             f"by {_short(reviewer)} ({category}); dashboard {outcome['dashboard']}")
    return outcome


def _update_dashboard(run_id: str | None, result: str) -> str:
    if not run_id:
        return "no run id"
    try:
        hits = es._es("POST", f"{DASHBOARD_INDEX}/_search", {
            "size": 2, "query": {"term": {"result_id.keyword": run_id}}})["hits"]["hits"]
        if len(hits) != 1:
            return f"{len(hits)} dashboard documents for {run_id}; not updated"
        es._es("POST", f"{DASHBOARD_INDEX}/_update/{quote(hits[0]['_id'], safe='')}?refresh=wait_for",
               {"doc": {"result": result}})
        return "updated"
    except requests.RequestException as exc:
        return f"failed: {exc}"
