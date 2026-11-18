"""Elasticsearch access for the web UI.

Reads `pass_or_fail` decisions and CPT status data; writes only to the reviews index.

A "run" here is one Jenkins build: `pass_or_fail` writes one decision document per
metric, all carrying the same `build_url`. Decisions don't carry the status-data ID, so
the status-data document is found by time: it is uploaded a few seconds before the
decisions, and runs on the perf cluster are serialized by a Jenkins lock.
"""

from __future__ import annotations

import datetime as dt
import json
import os
from dataclasses import dataclass, field
from urllib.parse import quote

import requests

ES_URL = os.environ.get("ES_URL", "http://elasticsearch.intlab.perf-infra.lab.eng.rdu2.redhat.com").rstrip("/")
DECISIONS_INDEX = os.environ.get("DECISIONS_INDEX", "insights_perf_aa_decisions")
STATUS_INDICES = os.environ.get("STATUS_INDICES", "insights_perf_index_*")
REVIEWS_INDEX = os.environ.get("REVIEWS_INDEX", "insights_perf_triage_reviews")
TIMEOUT = 30
# Status data is uploaded just before the decisions; allow for a slow upload.
JOIN_WINDOW = "2m"


@dataclass
class Decision:
    metric: str
    result: str
    method: str
    value: float | None
    lower: float | None
    upper: float | None
    uploaded: str
    exception: str | None = None


@dataclass
class Run:
    build_url: str
    job_name: str
    build_number: str
    uploaded: str
    decisions: list[Decision] = field(default_factory=list)
    status: dict | None = None  # status-data summary, when the time join finds it

    @property
    def key(self) -> str:
        return f"{self.job_name}#{self.build_number}"

    @property
    def result(self) -> str:
        results = {d.result for d in self.decisions}
        return "ERROR" if "ERROR" in results else "FAIL" if "FAIL" in results else "PASS"

    @property
    def failed(self) -> list[Decision]:
        return [d for d in self.decisions if d.result == "FAIL"]

    @property
    def review_id(self) -> str:
        """Same document ID that `rp-triage` review.py uses (status-data ID), else job#build."""
        return (self.status or {}).get("id") or self.key


def _es(method: str, path: str, body=None, ndjson: str | None = None) -> dict:
    headers = {"Content-Type": "application/x-ndjson" if ndjson else "application/json"}
    data = ndjson if ndjson is not None else (json.dumps(body) if body is not None else None)
    r = requests.request(method, f"{ES_URL}/{path}", data=data, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _split_build(url: str) -> tuple[str, str]:
    parts = [p for p in url.rstrip("/").split("/") if p]
    return (parts[-2] if len(parts) >= 2 else url, parts[-1] if parts else "")


def _decision(src: dict) -> Decision:
    return Decision(
        metric=src.get("description", "?"),
        result=src.get("result", "?"),
        method=src.get("method", ""),
        value=src.get("value"),
        lower=src.get("lower_boundary"),
        upper=src.get("upper_boundary"),
        uploaded=src.get("uploaded", ""),
        exception=src.get("exception"),
    )


def list_runs(days: int, job: str | None = None, result: str | None = None, limit: int = 200) -> list[Run]:
    """Runs with decisions uploaded in the last `days`, newest first."""
    filters = [{"range": {"uploaded": {"gte": f"now-{days}d"}}}]
    if job:
        filters.append({"term": {"job_name.keyword": job}})
    data = _es("POST", f"{DECISIONS_INDEX}/_search", {
        "size": 10000,
        "sort": [{"uploaded": "desc"}],
        "query": {"bool": {"filter": filters}},
    })
    runs: dict[str, Run] = {}
    for hit in data["hits"]["hits"]:
        src = hit["_source"]
        url = src.get("build_url")
        if not url:
            continue
        if url not in runs:
            job_name, number = _split_build(url)
            runs[url] = Run(url, src.get("job_name") or job_name, number, src.get("uploaded", ""))
        run = runs[url]
        run.decisions.append(_decision(src))
        run.uploaded = min(run.uploaded, src.get("uploaded", run.uploaded))
    out = [r for r in runs.values() if not result or r.result == result][:limit]
    attach_status(out)
    return out


def get_run(job: str, number: str) -> Run | None:
    data = _es("POST", f"{DECISIONS_INDEX}/_search", {
        "size": 1000,
        "query": {"bool": {"filter": [
            {"term": {"job_name.keyword": job}},
            {"wildcard": {"build_url.keyword": f"*/{job}/{number}/"}},
        ]}},
    })
    hits = data["hits"]["hits"]
    if not hits:
        return None
    first = hits[0]["_source"]
    run = Run(first["build_url"], job, number, min(h["_source"].get("uploaded", "") for h in hits))
    run.decisions = sorted((_decision(h["_source"]) for h in hits), key=lambda d: (d.result != "FAIL", d.metric))
    attach_status([run], full=True)
    return run


def _is_pr(src: dict) -> bool:
    pods = ((src.get("parameters") or {}).get("cluster") or {}).get("pods") or {}
    return any(isinstance(v, dict) and ":on-pr-" in str(v.get("image", "")) for v in pods.values())


def _images(src: dict) -> dict[str, str]:
    pods = ((src.get("parameters") or {}).get("cluster") or {}).get("pods") or {}
    return {k: str(v.get("image")) for k, v in sorted(pods.items()) if isinstance(v, dict) and v.get("image")}


def _utc(ts: str) -> dt.datetime:
    """Parse ES timestamps; decisions have no zone (UTC), status data has +00:00."""
    t = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def attach_status(runs: list[Run], full: bool = False) -> None:
    """Find each run's status-data document: the latest `ended` within JOIN_WINDOW before
    the run's first decision (plus 5 s for clock skew).

    One range query covers all runs; matching is done here.
    """
    if not runs:
        return
    times = [_utc(r.uploaded) for r in runs]
    window = dt.timedelta(minutes=int(JOIN_WINDOW.rstrip("m")))
    skew = dt.timedelta(seconds=5)
    source = True if full else ["id", "name", "result", "golden", "started", "ended", "parameters.cluster.pods"]
    try:
        data = _es("POST", f"{STATUS_INDICES}/_search", {
            "size": 10000,
            "_source": source,
            "sort": [{"ended": "asc"}],
            "query": {"range": {"ended": {"gte": (min(times) - window).isoformat(),
                                           "lte": (max(times) + skew).isoformat()}}},
        })
    except requests.RequestException:
        return
    candidates = []
    for hit in data["hits"]["hits"]:
        try:
            candidates.append((_utc(hit["_source"]["ended"]), hit))
        except (KeyError, TypeError, ValueError):
            continue
    for run, t in zip(runs, times):
        best = None
        for ended, hit in candidates:
            if t - window <= ended <= t + skew:
                best = hit  # ascending, so the last match is the closest
        if best is None:
            continue
        hits = [best]
        src = hits[0]["_source"]
        run.status = {
            "index": hits[0]["_index"],
            "id": src.get("id"),
            "name": src.get("name"),
            "result": src.get("result"),
            "golden": str(src.get("golden")).lower() == "true",
            "pr": _is_pr(src),
            "started": src.get("started"),
            "ended": src.get("ended"),
            "images": _images(src),
            "test": ((src.get("parameters") or {}).get("test")) if full else None,
            "comments": src.get("comments") if full else None,
        }


def metric_history(job: str, metrics: list[str], before: str, size: int = 40) -> dict[str, list[dict]]:
    """Last `size` decisions per metric for this job, up to and including this run."""
    if not metrics:
        return {}
    lines = []
    for m in metrics:
        lines.append(json.dumps({"index": DECISIONS_INDEX}))
        lines.append(json.dumps({
            "size": size,
            "_source": ["value", "lower_boundary", "upper_boundary", "result", "uploaded", "build_url"],
            "sort": [{"uploaded": "desc"}],
            "query": {"bool": {"filter": [
                {"term": {"job_name.keyword": job}},
                {"term": {"description.keyword": m}},
                {"range": {"uploaded": {"lte": before}}},
            ]}},
        }))
    responses = _es("POST", "_msearch", ndjson="\n".join(lines) + "\n")["responses"]
    out = {}
    for m, resp in zip(metrics, responses):
        hits = (resp.get("hits") or {}).get("hits") or []
        out[m] = [h["_source"] for h in reversed(hits)]
    return out


def job_names(days: int = 30) -> list[str]:
    data = _es("POST", f"{DECISIONS_INDEX}/_search", {
        "size": 0,
        "query": {"range": {"uploaded": {"gte": f"now-{days}d"}}},
        "aggs": {"jobs": {"terms": {"field": "job_name.keyword", "size": 200}}},
    })
    return sorted(b["key"] for b in data["aggregations"]["jobs"]["buckets"])


# --- reviews -----------------------------------------------------------------

def get_review(review_id: str) -> dict | None:
    r = requests.get(f"{ES_URL}/{REVIEWS_INDEX}/_doc/{quote(review_id, safe='')}", timeout=TIMEOUT)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json().get("_source")


def save_review(review_id: str, doc: dict) -> None:
    doc = dict(doc, reviewed_at=dt.datetime.now(dt.timezone.utc).isoformat())
    _es("PUT", f"{REVIEWS_INDEX}/_doc/{quote(review_id, safe='')}?refresh=wait_for", doc)


def list_reviews(limit: int = 500) -> list[dict]:
    data = _es("POST", f"{REVIEWS_INDEX}/_search", {
        "size": limit,
        "sort": [{"reviewed_at": {"order": "desc", "unmapped_type": "date"}}],
    })
    return [h["_source"] for h in data["hits"]["hits"]]


def ping() -> bool:
    try:
        requests.get(ES_URL, timeout=5).raise_for_status()
        return True
    except requests.RequestException:
        return False
