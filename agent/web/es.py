"""Elasticsearch access for the web UI.

Reads `pass_or_fail` decisions and CPT status data; writes only to the reviews index.

A "run" here is one Jenkins build: `pass_or_fail` writes one decision document per
metric, all carrying the same `build_url`. Status data records the same URL in
`results.jenkins.build_url`, which is the join key. Older documents without it are
matched by time instead: status data is uploaded a few seconds before the decisions, and
runs on the perf cluster are serialized by a Jenkins lock.
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
BUILD_URL_FIELD = "results.jenkins.build_url"
# Time-join fallback: status data is uploaded just before the decisions; allow for a slow upload.
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


_WINDOW = dt.timedelta(minutes=int(JOIN_WINDOW.rstrip("m")))
_SKEW = dt.timedelta(seconds=5)


def attach_status(runs: list[Run], full: bool = False) -> None:
    """Find each run's status-data document by build URL; for documents without one, the
    latest `ended` within JOIN_WINDOW before the run's first decision."""
    if not runs:
        return
    source = True if full else ["id", "name", "result", "golden", "started", "ended", "parameters.start",
                                "parameters.end", "results.end", "parameters.cluster.pods", BUILD_URL_FIELD]
    try:
        data = _es("POST", f"{STATUS_INDICES}/_search", {
            "size": len(runs) * 2,
            "_source": source,
            "query": {"terms": {f"{BUILD_URL_FIELD}.keyword": [r.build_url for r in runs]}},
        })
        by_url = {lookup(h["_source"], BUILD_URL_FIELD): h for h in data["hits"]["hits"]}
        matched = {r.build_url: by_url[r.build_url] for r in runs if r.build_url in by_url}
        rest = [r for r in runs if r.build_url not in matched]
        if rest:
            matched.update(_time_join(rest, source))
    except requests.RequestException:
        return
    for run in runs:
        if run.build_url in matched:
            run.status = _status_summary(matched[run.build_url], full)


def _time_join(runs: list[Run], source) -> dict[str, dict]:
    times = [_utc(r.uploaded) for r in runs]
    data = _es("POST", f"{STATUS_INDICES}/_search", {
        "size": 10000,
        "_source": source,
        "sort": [{"ended": "asc"}],
        "query": {"range": {"ended": {"gte": (min(times) - _WINDOW).isoformat(),
                                       "lte": (max(times) + _SKEW).isoformat()}}},
    })
    candidates = []
    for hit in data["hits"]["hits"]:
        try:
            candidates.append((_utc(hit["_source"]["ended"]), hit))
        except (KeyError, TypeError, ValueError):
            continue
    out = {}
    for run, t in zip(runs, times):
        for ended, hit in candidates:
            if t - _WINDOW <= ended <= t + _SKEW:
                out[run.build_url] = hit  # ascending, so the last match is the closest
    return out


def load_window(src: dict) -> tuple[str, str] | None:
    """When the test actually ran. `started`/`ended` cover only the upload step in some
    services (kessel: 23 s for a 300 s test) while `parameters.start`/`end` hold the load
    window; others are the reverse. Take the earliest start and latest end of all of them."""
    params, results = src.get("parameters") or {}, src.get("results") or {}
    starts = [t for t in (src.get("started"), params.get("start")) if isinstance(t, str)]
    ends = [t for t in (src.get("ended"), params.get("end"), results.get("end")) if isinstance(t, str)]
    try:
        return (min(starts, key=_utc), max(ends, key=_utc)) if starts and ends else None
    except ValueError:
        return None


def _status_summary(hit: dict, full: bool) -> dict:
    src = hit["_source"]
    return {
        "window": load_window(src),
        "index": hit["_index"],
        "doc_id": hit["_id"],
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


# A job can rotate through several tests (e.g. InsightsKesselK6_runnerAPI runs ~12), whose
# baselines differ by an order of magnitude. History and comparisons must stay within one
# test: same name and same values for these parameters (as in tools/measure_noise.py).
COMPARABLE_FIELDS = (
    ("parameters", "test", "scenario"),
    ("parameters", "test", "transport"),
    ("parameters", "test", "duration"),
    ("parameters", "locust", "num_clients"),
)


def lookup(doc, path: str):
    """Resolve a dotted status-data path whose keys may themselves contain dots."""
    parts, node, i = path.split("."), doc, 0
    while i < len(parts):
        if not isinstance(node, dict):
            return None
        for j in range(len(parts), i, -1):
            key = ".".join(parts[i:j])
            if key in node:
                node, i = node[key], j
                break
        else:
            return None
    return node


def _nested(doc, keys):
    for k in keys:
        if not isinstance(doc, dict) or k not in doc:
            return None
        doc = doc[k]
    return doc


def test_identity(doc: dict) -> dict:
    """What makes two runs comparable: test name plus the COMPARABLE_FIELDS that are set."""
    ident = {"name": doc.get("name")}
    for keys in COMPARABLE_FIELDS:
        v = _nested(doc, keys)
        if isinstance(v, (str, int, float)) and not isinstance(v, bool):
            ident[".".join(keys)] = v
    return ident


def comparable_history(run: Run, metrics: list[str], size: int = 40,
                       days: int | None = None) -> tuple[dict, dict[str, list[dict]]]:
    """Last `size` runs of the same test up to this run, oldest first, per metric.

    Values come from status data, so non-gated metrics work too. Bands and results come
    from the decisions uploaded right after each run (same time join as attach_status).
    Returns (test identity, {metric: [points]}). Falls back to job-wide decision history
    (possibly mixing tests) only when this run has no status data.
    """
    doc = status_doc(run)
    if doc is None:
        before = run.uploaded[:19] + "||+1m"
        return {}, metric_history(run.job_name, metrics, before=before, size=size)
    ident = test_identity(doc)
    window = {"lte": doc["ended"]}
    if days:
        window["gte"] = (_utc(doc["ended"]) - dt.timedelta(days=days)).isoformat()
    filters = [{"range": {"ended": window}}]
    for field, value in ident.items():
        filters.append({"term": {f"{field}.keyword" if isinstance(value, str) else field: value}})
    data = _es("POST", f"{run.status['index']}/_search", {
        "size": size,
        "sort": [{"ended": "desc"}],
        "_source": ["ended", "result", "parameters.cluster.pods", BUILD_URL_FIELD] + metrics,
        "query": {"bool": {"filter": filters}},
    })
    docs = [h["_source"] for h in reversed(data["hits"]["hits"])]
    if not docs:
        return ident, {m: [] for m in metrics}
    # Decisions for these runs: by build URL, plus a time range for documents without one.
    decisions = _es("POST", f"{DECISIONS_INDEX}/_search", {
        "size": 10000,
        "_source": ["description", "value", "lower_boundary", "upper_boundary", "result", "uploaded", "build_url"],
        "query": {"bool": {"filter": [
            {"term": {"job_name.keyword": run.job_name}},
            {"terms": {"description.keyword": metrics}},
            {"range": {"uploaded": {"gte": (_utc(docs[0]["ended"]) - _SKEW).isoformat(),
                                    "lte": (_utc(docs[-1]["ended"]) + _WINDOW).isoformat()}}},
        ]}},
    })["hits"]["hits"]
    by_url: dict[tuple[str, str], dict] = {}
    by_metric: dict[str, list[tuple[dt.datetime, dict]]] = {}
    for h in decisions:
        s = h["_source"]
        by_url[(s.get("build_url"), s["description"])] = s
        by_metric.setdefault(s["description"], []).append((_utc(s["uploaded"]), s))
    out: dict[str, list[dict]] = {}
    for m in metrics:
        points = []
        for d in docs:
            url = lookup(d, BUILD_URL_FIELD)
            if url:
                dec = by_url.get((url, m))
            else:
                ended = _utc(d["ended"])
                dec = next((s for t, s in by_metric.get(m, []) if ended - _SKEW <= t <= ended + _WINDOW), None)
            value = lookup(d, m)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                value = dec.get("value") if dec else None
            points.append({
                "ended": d["ended"], "value": value, "pr": _is_pr(d), "run_result": d.get("result"),
                "lower_boundary": dec.get("lower_boundary") if dec else None,
                "upper_boundary": dec.get("upper_boundary") if dec else None,
                "result": dec.get("result") if dec else None,  # None: metric not gated in that run
                "build_url": url or (dec.get("build_url") if dec else None),
                "uploaded": dec.get("uploaded") if dec else d["ended"],
            })
        out[m] = points
    return ident, out


def previous_comparable(run: Run) -> Run | None:
    """The latest earlier run of the same test that has decisions."""
    if not run.status:
        return None
    _, hist = comparable_history(run, [d.metric for d in run.decisions[:1]], size=10)
    for p in reversed(next(iter(hist.values()), [])[:-1]):
        url = p.get("build_url")
        if url and url != run.build_url:
            return get_run(run.job_name, url.rstrip("/").split("/")[-1])
    return None


def status_doc(run: Run) -> dict | None:
    """The run's full status-data document, if the time join found one."""
    if not run.status:
        return None
    return _es("GET", f"{run.status['index']}/_doc/{quote(run.status['doc_id'], safe='')}").get("_source")


def gated_metrics(job: str, days: int = 30) -> dict[str, dict]:
    """Metrics `pass_or_fail` checked for this job recently, with decision counts."""
    data = _es("POST", f"{DECISIONS_INDEX}/_search", {
        "size": 0,
        "query": {"bool": {"filter": [
            {"term": {"job_name.keyword": job}},
            {"range": {"uploaded": {"gte": f"now-{days}d"}}},
        ]}},
        "aggs": {"m": {"terms": {"field": "description.keyword", "size": 500},
                        "aggs": {"r": {"terms": {"field": "result.keyword"}}}}},
    })
    return {b["key"]: {"decisions": b["doc_count"], **{r["key"]: r["doc_count"] for r in b["r"]["buckets"]}}
            for b in data["aggregations"]["m"]["buckets"]}


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


def get_reviews(review_ids: list[str]) -> dict[str, dict]:
    """Reviews for many runs in one request, keyed by review ID; runs without one are absent."""
    if not review_ids:
        return {}
    r = requests.post(f"{ES_URL}/{REVIEWS_INDEX}/_mget", json={"ids": list(dict.fromkeys(review_ids))},
                      timeout=TIMEOUT)
    if r.status_code == 404:  # index not created yet
        return {}
    r.raise_for_status()
    return {d["_id"]: d["_source"] for d in r.json().get("docs", []) if d.get("found")}


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
