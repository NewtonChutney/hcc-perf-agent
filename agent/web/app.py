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

from . import alerts, chat, es, fmt, writeback
from .charts import sparkline
from .rules import CATEGORIES, LABELS, evaluate, evaluate_many

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
# oauth-proxy on OpenShift reports users as <name>@cluster.local; show just the name.
templates.env.filters["who"] = lambda s: (s or "").removesuffix("@cluster.local")


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
def runs_page(request: Request, days: int = 7, job: str = "", result: str = "FAIL", show_pr: bool = False,
              review: str = "", label: str = ""):
    days = max(1, min(days, 60))
    error = None
    rows, jobs = [], []
    try:
        runs = es.list_runs(days, job or None, result or None)
        if not show_pr:
            runs = [r for r in runs if not (r.status and r.status["pr"])]
        reviews = es.get_reviews([r.review_id for r in runs])
        rows = [(r, a, reviews.get(r.review_id)) for r, a in zip(runs, evaluate_many(runs))]
        jobs = es.job_names()
    except requests.RequestException as exc:
        error = f"Elasticsearch request failed: {exc}"
    # A run needs a review when the agent made a call on it (anything but PASS) and nobody has reviewed it.
    pending = sum(1 for _, a, rv in rows if a.predicted_category and not rv)
    if review == "pending":
        rows = [x for x in rows if x[1].predicted_category and not x[2]]
    elif review == "reviewed":
        rows = [x for x in rows if x[2]]
    if label:
        rows = [x for x in rows if x[1].label == label]
    counts = collections.Counter(a.label for _, a, _ in rows)
    user = current_user(request)
    here = request.url.path + (f"?{request.url.query}" if request.url.query else "")
    # static/runs.js asks for just the results area (X-Partial: 1) when a filter changes; the
    # URL stays the same as the full page's, so responses must not be cached interchangeably.
    partial = request.headers.get("x-partial") == "1"
    response = templates.TemplateResponse(request, "_runs_results.html" if partial else "runs.html", dict(
        rows=rows, jobs=jobs, days=days, job=job, result=result, show_pr=show_pr, review=review,
        label=label, labels=LABELS, pending=pending, counts=counts, error=error, user=user, here=here,
        can_write=writeback.allowed(user), result_for=writeback.RESULT_FOR_CATEGORY))
    response.headers["Vary"] = "X-Partial"
    if partial:
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/runs/{job}/{number}", response_class=HTMLResponse)
def run_page(request: Request, job: str, number: str, saved: bool = False):
    run = es.get_run(job, number)
    if run is None:
        raise HTTPException(404, f"No decisions found for {job} #{number}")
    assessment = evaluate(run, all_metrics=True)
    metrics = [r.decision.metric for r in assessment.readings]
    test, history = es.comparable_history(run, [m for m in metrics if m != "?"])
    charts = {m: sparkline(points, highlight_url=run.build_url) for m, points in history.items()}
    # opl's pass_or_fail records a check that raised as {"result": "ERROR"} with no metric name
    # (pass_or_fail.py: info_all.append({"result": "ERROR", "exception": ...}), and the exception
    # text is dropped before upload). Name the candidates: metrics this job checks in other runs
    # that have no decision in this one.
    nameless_errors = sum(1 for d in run.decisions if d.metric == "?")
    missing_metrics = []
    if nameless_errors:
        present = {d.metric for d in run.decisions}
        # A year back: a metric that errors in every run never gets a named decision again.
        missing_metrics = sorted(m for m in es.gated_metrics(job, days=365) if m not in present)
    user = current_user(request)
    return templates.TemplateResponse(request, "run.html", dict(
        charts=charts, test=test, nameless_errors=nameless_errors, missing_metrics=missing_metrics,
        **_review_context(run, assessment, user, saved)))


def _review_context(run: es.Run, a, user: str | None, saved: bool) -> dict:
    """Everything _review.html needs; shared by the run page and the in-place save."""
    return dict(run=run, a=a, user=user, saved=saved, review=es.get_review(run.review_id),
                categories=CATEGORIES, can_write=writeback.allowed(user),
                agree_plan=writeback.planned(run, a.predicted_category),
                result_for=writeback.RESULT_FOR_CATEGORY)


@app.post("/runs/{job}/{number}/review")
def submit_review(request: Request, job: str, number: str,
                  verdict: str = Form(...), category: str = Form(""),
                  explanation: str = Form(""), bug_url: str = Form(""), next: str = Form("")):
    check_same_origin(request)
    user = current_user(request)
    if not user:
        raise HTTPException(401, "not signed in")
    run = es.get_run(job, number)
    if run is None:
        raise HTTPException(404)
    a = evaluate(run)
    if verdict == "agree":
        category = a.predicted_category or ""
    if category not in CATEGORIES:
        raise HTTPException(400, "choose a category")
    bug_url = bug_url.strip()
    if bug_url and not bug_url.startswith("https://"):
        raise HTTPException(400, "bug URL must use https://")
    if category == "known_issue" and not bug_url:
        raise HTTPException(400, "known_issue needs a bug URL")
    explanation = explanation.strip()[:4000]
    try:
        outcome = writeback.apply(run, category, user, explanation, bug_url or None, a.predicted_category)
    except requests.RequestException as exc:
        outcome = {"status": "failed", "error": str(exc)[:500]}
    es.save_review(run.review_id, {
        "run_id": run.review_id,
        "job_name": job,
        "build_url": run.build_url,
        "predicted_category": a.predicted_category,
        "predicted_label": a.label,
        "category": category,
        "explanation": explanation,
        "bug_url": bug_url or None,
        "signature": sorted(d.metric for d in run.failed),
        "reviewer": user,
        "source": "web-ui",
        "writeback": outcome,
    })
    # static/run.js saves without navigating: answer with the refreshed review area.
    if request.headers.get("x-partial") == "1":
        if outcome.get("status") == "changed" and run.status:
            run.status["result"] = outcome["result_after"]
        response = templates.TemplateResponse(request, "_review.html", _review_context(run, a, user, True))
        response.headers["Cache-Control"] = "no-store"
        return response
    # Agree from the runs list returns to the same filtered list; only local paths are accepted.
    if next.startswith("/") and not next.startswith("//"):
        return RedirectResponse(next, status_code=303)
    return RedirectResponse(f"/runs/{job}/{number}?saved=1", status_code=303)


@app.get("/reviews", response_class=HTMLResponse)
def reviews_page(request: Request):
    error = None
    reviews = []
    try:
        reviews = es.list_reviews()
    except requests.RequestException as exc:
        error = f"Elasticsearch request failed: {exc}"
    return templates.TemplateResponse(request, "reviews.html", dict(
        reviews=reviews, progress=writeback.auto_apply_progress(reviews), error=error,
        min_reviews=writeback.AUTO_APPLY_MIN_REVIEWS, min_agreement=writeback.AUTO_APPLY_MIN_AGREEMENT,
        user=current_user(request)))


@app.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request):
    return templates.TemplateResponse(request, "chat.html", dict(user=current_user(request)))


templates.env.globals.update(chat_models=lambda: chat.MODELS, chat_default_model=lambda: chat.LLM_MODEL,
                             writeback_enabled=writeback.enabled)


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
    model = body.get("model") or None
    if model and model not in chat.MODELS:
        raise HTTPException(400, "unknown model")
    try:
        # The tool loop does blocking HTTP calls; keep it off the event loop.
        from starlette.concurrency import run_in_threadpool
        result = await run_in_threadpool(chat.answer, history, user, job, build, model)
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
