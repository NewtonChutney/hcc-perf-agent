"""HCC Perf Agent web UI: CPT run triage and reviews, perf-cluster alerts.

Runs behind an OpenShift oauth-proxy sidecar, which authenticates users and passes
`X-Forwarded-Email` / `X-Forwarded-User`. The app listens on localhost only, so those
headers can't be set by anyone but the proxy. Writes go only to the reviews index.
"""

from __future__ import annotations

import collections
import logging
import os
import pathlib
from urllib.parse import urlparse

import requests
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import alerts, chat, es, fmt
from .charts import sparkline
from .rules import CATEGORIES, assess

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
HERE = pathlib.Path(__file__).parent
app = FastAPI(title="HCC Perf Agent", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
templates = Jinja2Templates(directory=HERE / "templates")
templates.env.globals.update(
    kibana_url=os.environ.get("KIBANA_URL", ""),
    alerts_enabled=alerts.enabled,
    chat_enabled=chat.enabled,
)
templates.env.filters["num"] = fmt.num
templates.env.filters["pct"] = fmt.pct
templates.env.filters["short_time"] = lambda s: (s or "")[:16].replace("T", " ")


def current_user(request: Request) -> str | None:
    return (request.headers.get("x-forwarded-email") or request.headers.get("x-forwarded-user")
            or os.environ.get("DEV_USER") or None)


def check_same_origin(request: Request) -> None:
    """Reject cross-site form posts (the proxy's session cookie would otherwise ride along)."""
    origin = request.headers.get("origin") or request.headers.get("referer")
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    if not origin or urlparse(origin).netloc != host:
        raise HTTPException(403, "cross-origin request rejected")


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/readyz")
def readyz():
    ok = es.ping()
    return JSONResponse({"elasticsearch": ok}, status_code=200 if ok else 503)


@app.get("/", response_class=HTMLResponse)
def runs_page(request: Request, days: int = 7, job: str = "", result: str = "FAIL", show_pr: bool = False):
    days = max(1, min(days, 60))
    error = None
    rows, jobs = [], []
    try:
        runs = es.list_runs(days, job or None, result or None)
        if not show_pr:
            runs = [r for r in runs if not (r.status and r.status["pr"])]
        rows = [(r, assess(r)) for r in runs]
        jobs = es.job_names()
    except requests.RequestException as exc:
        error = f"Elasticsearch request failed: {exc}"
    counts = collections.Counter(a.label for _, a in rows)
    return templates.TemplateResponse(request, "runs.html", dict(
        rows=rows, jobs=jobs, days=days, job=job, result=result, show_pr=show_pr,
        counts=counts, error=error, user=current_user(request)))


@app.get("/runs/{job}/{number}", response_class=HTMLResponse)
def run_page(request: Request, job: str, number: str, saved: bool = False):
    run = es.get_run(job, number)
    if run is None:
        raise HTTPException(404, f"No decisions found for {job} #{number}")
    assessment = assess(run)
    metrics = [r.decision.metric for r in assessment.readings]
    test, history = es.comparable_history(run, metrics)
    charts = {m: sparkline(points, highlight_url=run.build_url) for m, points in history.items()}
    return templates.TemplateResponse(request, "run.html", dict(
        run=run, a=assessment, charts=charts, test=test, review=es.get_review(run.review_id),
        categories=CATEGORIES, saved=saved, user=current_user(request)))


@app.post("/runs/{job}/{number}/review")
def submit_review(request: Request, job: str, number: str,
                  verdict: str = Form(...), category: str = Form(""),
                  explanation: str = Form(""), bug_url: str = Form("")):
    check_same_origin(request)
    user = current_user(request)
    if not user:
        raise HTTPException(401, "not signed in")
    run = es.get_run(job, number)
    if run is None:
        raise HTTPException(404)
    a = assess(run)
    if verdict == "agree":
        category = a.predicted_category or ""
    if category not in CATEGORIES:
        raise HTTPException(400, "choose a category")
    bug_url = bug_url.strip()
    if bug_url and not bug_url.startswith("https://"):
        raise HTTPException(400, "bug URL must use https://")
    if category == "known_issue" and not bug_url:
        raise HTTPException(400, "known_issue needs a bug URL")
    es.save_review(run.review_id, {
        "run_id": run.review_id,
        "job_name": job,
        "build_url": run.build_url,
        "predicted_category": a.predicted_category,
        "predicted_label": a.label,
        "category": category,
        "explanation": explanation.strip()[:4000],
        "bug_url": bug_url or None,
        "signature": sorted(d.metric for d in run.failed),
        "reviewer": user,
        "source": "web-ui",
    })
    return RedirectResponse(f"/runs/{job}/{number}?saved=1", status_code=303)


@app.get("/reviews", response_class=HTMLResponse)
def reviews_page(request: Request):
    error = None
    reviews = []
    try:
        reviews = es.list_reviews()
    except requests.RequestException as exc:
        error = f"Elasticsearch request failed: {exc}"
    by_job = collections.defaultdict(lambda: [0, 0])
    for r in reviews:
        if r.get("predicted_category"):
            by_job[r.get("job_name", "?")][0] += 1
            by_job[r.get("job_name", "?")][1] += r.get("category") == r.get("predicted_category")
    return templates.TemplateResponse(request, "reviews.html", dict(
        reviews=reviews, by_job=dict(sorted(by_job.items())), error=error, user=current_user(request)))


@app.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request):
    return templates.TemplateResponse(request, "chat.html", dict(user=current_user(request)))


@app.post("/api/chat")
async def chat_api(request: Request):
    check_same_origin(request)
    user = current_user(request)
    if not user:
        raise HTTPException(401, "not signed in")
    body = await request.json()
    history = body.get("messages")
    if not isinstance(history, list) or not history or history[-1].get("role") != "user":
        raise HTTPException(400, "messages must end with a user message")
    job, build = body.get("job") or None, body.get("build") or None
    try:
        # The tool loop does blocking HTTP calls; keep it off the event loop.
        from starlette.concurrency import run_in_threadpool
        result = await run_in_threadpool(chat.answer, history, user, job, build)
    except chat.ChatUnavailable as exc:
        return JSONResponse({"error": str(exc)}, status_code=503)
    return result


@app.get("/alerts", response_class=HTMLResponse)
def alerts_page(request: Request):
    data, error = None, None
    if alerts.enabled():
        try:
            data = alerts.fetch()
        except requests.RequestException as exc:
            error = f"Alertmanager request failed: {exc}"
    return templates.TemplateResponse(request, "alerts.html", dict(
        data=data, error=error, enabled=alerts.enabled(), am_url=alerts.ALERTMANAGER_URL,
        user=current_user(request)))
