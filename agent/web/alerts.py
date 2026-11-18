"""Perf-cluster alerts, read from Alertmanager's v2 API (polling; read-only).

Needs `ALERTMANAGER_URL` and a bearer token for a ServiceAccount on the perf cluster
with `monitoring-alertmanager-view` (PLAN.md section 8). The token is read from a file
so it can come from a mounted Secret.
"""

from __future__ import annotations

import collections
import os
import pathlib

import requests

ALERTMANAGER_URL = os.environ.get("ALERTMANAGER_URL", "").rstrip("/")
TOKEN_FILE = pathlib.Path(os.environ.get("PERF_CLUSTER_TOKEN_FILE", "/var/run/secrets/perf-cluster/token"))
# Alerts known to be false (e.g. absent(up{...}) on targets that aren't scraped), comma-separated.
KNOWN_FALSE = {a.strip() for a in os.environ.get("ALERTS_KNOWN_FALSE", "").split(",") if a.strip()}


def enabled() -> bool:
    return bool(ALERTMANAGER_URL) and TOKEN_FILE.is_file()


def fetch() -> dict:
    token = TOKEN_FILE.read_text().strip()
    r = requests.get(f"{ALERTMANAGER_URL}/api/v2/alerts", params={"active": "true", "silenced": "false"},
                     headers={"Authorization": f"Bearer {token}"}, timeout=20)
    r.raise_for_status()
    groups = collections.defaultdict(list)
    for a in r.json():
        labels = a.get("labels", {})
        groups[(labels.get("severity", "none"), labels.get("alertname", "?"))].append({
            "namespace": labels.get("namespace", ""),
            "labels": {k: v for k, v in sorted(labels.items()) if k not in ("alertname", "severity", "namespace")},
            "summary": (a.get("annotations") or {}).get("summary") or (a.get("annotations") or {}).get("description", ""),
            "starts_at": a.get("startsAt", ""),
        })
    order = {"critical": 0, "error": 1, "warning": 2, "info": 3}
    return {
        "groups": sorted(groups.items(), key=lambda kv: (order.get(kv[0][0], 9), kv[0][1])),
        "total": sum(len(v) for v in groups.values()),
        "known_false": KNOWN_FALSE,
    }
