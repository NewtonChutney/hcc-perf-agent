#!/usr/bin/env python3
"""Measure run-to-run noise of every gated CPT metric (PLAN.md section 5.1).

For each `investigator-conf.yaml` in an iperf checkout, read its ES index and the
metric paths in `sets`, fetch golden runs from the last N days, drop runs of PR
images (`:on-pr-` tags), group runs that are comparable (test name, scenario,
transport, duration, client count), and compute for every metric:

  median, robust CV = 1.4826 * MAD / |median|, and the band a robust 3-sigma
  rule would need (3 * robust CV).

PASS and FAIL runs are both used (ERROR runs are not): the PASS-only history
that pass_or_fail uses is itself narrowed by the current rule. Median/MAD keep
the occasional real regression from inflating the result.

Read-only: only `_search` requests are sent.
"""

import argparse
import collections
import datetime
import pathlib
import re
import statistics
import sys

import requests
import yaml

NEAR_ZERO = 1e-9
GROUP_FIELDS = [
    ("scenario", ("parameters", "test", "scenario")),
    ("transport", ("parameters", "test", "transport")),
    ("duration", ("parameters", "test", "duration")),
    ("clients", ("parameters", "locust", "num_clients")),
]


def lookup(doc, path):
    """Resolve a dotted status-data path; keys may themselves contain dots."""
    parts = path.split(".")
    node = doc
    i = 0
    while i < len(parts):
        if not isinstance(node, dict):
            return None
        for j in range(len(parts), i, -1):
            key = ".".join(parts[i:j])
            if key in node:
                node = node[key]
                i = j
                break
        else:
            return None
    return node if isinstance(node, (int, float)) and not isinstance(node, bool) else None


def nested(doc, keys):
    for k in keys:
        if not isinstance(doc, dict) or k not in doc:
            return None
        doc = doc[k]
    return doc


def is_pr_run(doc):
    pods = nested(doc, ("parameters", "cluster", "pods")) or {}
    return any(isinstance(v, dict) and ":on-pr-" in str(v.get("image", "")) for v in pods.values())


def fetch(es, index, since, cache):
    if index in cache:
        return cache[index]
    query = {
        "size": 10000,
        "query": {"bool": {"filter": [
            {"term": {"golden.keyword": "true"}},
            {"terms": {"result.keyword": ["PASS", "FAIL"]}},
            {"range": {"started": {"gte": since}}},
        ]}},
    }
    r = requests.get(f"{es}/{index}/_search", json=query, timeout=120)
    if r.status_code != 200:
        cache[index] = None
        return None
    cache[index] = [h["_source"] for h in r.json()["hits"]["hits"]]
    return cache[index]


def literal_name(conf):
    m = re.search(r'name\.keyword:\s*"([^"{}]+)"', conf["history"].get("es_query", ""))
    return m.group(1) if m else None


def bucket(values):
    med = statistics.median(values)
    if abs(med) < NEAR_ZERO:
        return med, None
    mad = statistics.median(abs(v - med) for v in values)
    return med, 1.4826 * mad / abs(med)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--iperf", required=True, help="path to an iperf checkout")
    ap.add_argument("--es", default="http://elasticsearch.intlab.perf-infra.lab.eng.rdu2.redhat.com")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--min-runs", type=int, default=5)
    args = ap.parse_args()

    now = datetime.datetime.now(datetime.timezone.utc)
    since = (now - datetime.timedelta(days=args.days)).isoformat()
    confs = sorted(p for p in pathlib.Path(args.iperf).rglob("investigator-conf*.yaml") if "_eph" not in p.name)
    cache = {}
    rows = []          # per (conf, group, metric)
    skipped = []       # (conf, reason)

    for path in confs:
        rel = str(path.relative_to(args.iperf))
        conf = yaml.safe_load(path.read_text())
        hist = conf.get("history", {})
        if hist.get("type") != "elasticsearch":
            skipped.append((rel, f"history type {hist.get('type')}"))
            continue
        docs = fetch(args.es, hist["es_index"], since, cache)
        if docs is None:
            skipped.append((rel, f"index {hist['es_index']} not readable"))
            continue
        name = literal_name(conf)
        pr_dropped = sum(1 for d in docs if is_pr_run(d) and (not name or d.get("name") == name))
        docs = [d for d in docs if not is_pr_run(d) and (not name or d.get("name") == name)]
        groups = collections.defaultdict(list)
        for d in docs:
            key = (d.get("name"),) + tuple(nested(d, f) for _, f in GROUP_FIELDS)
            groups[key].append(d)
        usable = {k: v for k, v in groups.items() if len(v) >= args.min_runs}
        if not usable:
            skipped.append((rel, f"no comparable group with >= {args.min_runs} runs in {args.days} days "
                                 f"({len(docs)} runs, {pr_dropped} PR runs dropped)"))
            continue
        before = len(rows)
        for key, gdocs in usable.items():
            label = " / ".join(f"{n}={v}" for (n, _), v in zip(GROUP_FIELDS, key[1:]) if v is not None) or key[0]
            for metric in conf["sets"]:
                values = [v for v in (lookup(d, metric) for d in gdocs) if v is not None]
                if len(values) < args.min_runs:
                    continue
                med, rcv = bucket(values)
                rows.append(dict(conf=rel, index=hist["es_index"], group=label, metric=metric,
                                 n=len(values), median=med, rcv=rcv))
        if len(rows) == before:
            skipped.append((rel, f"{len(docs)} runs, but no `sets` metric has >= {args.min_runs} numeric values "
                                 f"({pr_dropped} PR runs dropped)"))

    print(f"# CPT metric noise, last {args.days} days\n")
    print(f"Generated {now:%Y-%m-%d %H:%M} UTC by `tools/measure_noise.py` from golden PASS/FAIL runs "
          f"(PR-image runs excluded), groups with >= {args.min_runs} runs.\n")
    print("`band needed` = 3 x robust CV: the +/- band a robust 3-sigma rule needs for this metric. "
          "`near zero` = median is 0, needs an absolute limit.\n")

    def cls(r):
        if r["rcv"] is None:
            return "near zero"
        b = 3 * r["rcv"]
        return "<= 5%" if b <= 0.05 else "5-10%" if b <= 0.10 else "10-20%" if b <= 0.20 else "> 20%"

    classes = ["<= 5%", "5-10%", "10-20%", "> 20%", "near zero"]
    print("## Summary per config\n")
    print("| Config | Groups | Metric series | " + " | ".join(f"band {c}" if c != "near zero" else c for c in classes) + " |")
    print("|---|---:|---:|" + "---:|" * len(classes))
    by_conf = collections.defaultdict(list)
    for r in rows:
        by_conf[r["conf"]].append(r)
    total = collections.Counter()
    for c, rs in sorted(by_conf.items()):
        cnt = collections.Counter(cls(r) for r in rs)
        total.update(cnt)
        print(f"| `{c}` | {len({r['group'] for r in rs})} | {len(rs)} | " + " | ".join(str(cnt[k]) for k in classes) + " |")
    print(f"| **All** | | **{sum(total.values())}** | " + " | ".join(f"**{total[k]}**" for k in classes) + " |\n")

    if skipped:
        print("## Configs without enough data\n")
        for c, why in skipped:
            print(f"- `{c}`: {why}")
        print()

    print("## Detail\n")
    for c, rs in sorted(by_conf.items()):
        print(f"### `{c}` (`{rs[0]['index']}`)\n")
        print("| Group | Metric | Runs | Median | Robust CV | Band needed |")
        print("|---|---|---:|---:|---:|---:|")
        for r in sorted(rs, key=lambda r: (r["group"], r["metric"])):
            m = r["metric"].replace("results.requests.SUMMARY.", "").replace("measurements.", "m.")
            cv = "-" if r["rcv"] is None else f"{100 * r['rcv']:.1f}%"
            band = "near zero" if r["rcv"] is None else f"{300 * r['rcv']:.1f}%"
            print(f"| {r['group']} | `{m}` | {r['n']} | {r['median']:.4g} | {cv} | {band} |")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
