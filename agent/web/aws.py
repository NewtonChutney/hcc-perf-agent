"""Read-only RDS evidence from AWS: Performance Insights and CloudWatch.

Uses the perf team's PI reader key (IAM user consoledot-perf-team-rds-pi-reader, copied
from rhperfcluster cpt/iperf-secret into Secret hcc-perf-agent-aws). That key can read
Performance Insights metrics, top SQL and wait events, describe DB instances, and read
CloudWatch. rdu3 reaches AWS only through the corporate proxy (EGRESS_PROXY).
"""

from __future__ import annotations

import datetime as dt
import os
import statistics
import threading
import time

PI_METRICS = {
    "db.load.avg": "average active sessions (DB load)",
    "os.cpuUtilization.total.avg": "CPU %",
    "os.loadAverageMinute.one.avg": "OS load average (1 min)",
    "os.diskIO.rdsdev.readIOsPS.avg": "read IOPS",
    "os.diskIO.rdsdev.writeIOsPS.avg": "write IOPS",
    "db.Transactions.xact_commit.avg": "commits per second",
}
CLOUDWATCH_METRICS = ("CPUUtilization", "DatabaseConnections", "FreeableMemory", "ReadLatency",
                      "WriteLatency", "ReadIOPS", "WriteIOPS", "DiskQueueDepth")
MAX_WINDOW = dt.timedelta(hours=6)
_lock = threading.Lock()
_session = None
_instances_cache: tuple[float, list[dict]] | None = None


def enabled() -> bool:
    return bool(os.environ.get("AWS_PI_ACCESS_KEY_ID") and os.environ.get("AWS_PI_SECRET_ACCESS_KEY"))


def _client(service: str):
    global _session
    import boto3
    from botocore.config import Config

    with _lock:
        if _session is None:
            _session = boto3.Session(aws_access_key_id=os.environ["AWS_PI_ACCESS_KEY_ID"],
                                     aws_secret_access_key=os.environ["AWS_PI_SECRET_ACCESS_KEY"],
                                     region_name=os.environ.get("AWS_REGION", "us-east-1"))
    proxy = os.environ.get("EGRESS_PROXY")
    cfg = Config(connect_timeout=10, read_timeout=30, retries={"max_attempts": 2},
                 proxies={"https": proxy, "http": proxy} if proxy else None)
    return _session.client(service, config=cfg)


def instances() -> list[dict]:
    """RDS instances in the perf account (cached for 10 minutes)."""
    global _instances_cache
    if _instances_cache and time.monotonic() - _instances_cache[0] < 600:
        return _instances_cache[1]
    out, marker = [], None
    rds = _client("rds")
    while True:
        page = rds.describe_db_instances(MaxRecords=100, **({"Marker": marker} if marker else {}))
        for d in page["DBInstances"]:
            out.append({"instance": d["DBInstanceIdentifier"], "resource_id": d.get("DbiResourceId"),
                        "engine": f"{d.get('Engine')} {d.get('EngineVersion')}", "class": d.get("DBInstanceClass"),
                        "performance_insights": d.get("PerformanceInsightsEnabled", False)})
        marker = page.get("Marker")
        if not marker:
            break
    _instances_cache = (time.monotonic(), out)
    return out


def guess_instances(names: list[str]) -> list[str]:
    """RDS instances that belong to the run's pods, by service name.

    Instance kessel-inventory-perf (service "kessel-inventory") matches a pod that starts
    with the service name or shares its first two name parts (kessel-inventory-api).
    If nothing matches that way, fall back to the first name part (notifications-gw-service
    -> notifications-backend-perf). Read replicas (-readonly) are included.
    """
    names = [n.lower() for n in names if n]
    services = {i["instance"]: i["instance"].lower().removesuffix("-readonly").removesuffix("-perf")
                for i in instances()}
    strong = [i for i, s in services.items() if any(n.startswith(s) or _shared_prefix(n, s) >= 2 for n in names)]
    if strong:
        return strong
    return [i for i, s in services.items() if any(_shared_prefix(n, s) >= 1 for n in names)]


def _shared_prefix(a: str, b: str) -> int:
    n = 0
    for x, y in zip(a.split("-"), b.split("-")):
        if x != y:
            break
        n += 1
    return n


def _summary(values: list[float]) -> dict:
    if not values:
        return {"points": 0}
    return {"avg": statistics.fmean(values), "max": max(values), "min": min(values),
            "p50": statistics.median(values), "points": len(values)}


def window_report(instance: str, start: dt.datetime, end: dt.datetime, top: int = 5) -> dict:
    """PI load, OS metrics, top SQL and waits, and CloudWatch metrics for one instance and window."""
    if end - start > MAX_WINDOW:
        return {"error": f"window longer than {MAX_WINDOW}; narrow it"}
    inst = next((i for i in instances() if i["instance"] == instance), None)
    if inst is None:
        return {"error": f"unknown RDS instance {instance}; use list_rds_instances"}
    period = 60 if end - start <= dt.timedelta(hours=1) else 300
    report: dict = {"instance": instance, "engine": inst["engine"], "class": inst["class"],
                    "window_utc": [start.isoformat(), end.isoformat()], "period_s": period}

    if inst["performance_insights"] and inst["resource_id"]:
        pi = _client("pi")
        args = dict(ServiceType="RDS", Identifier=inst["resource_id"], StartTime=start, EndTime=end)
        metrics = pi.get_resource_metrics(PeriodInSeconds=period,
                                          MetricQueries=[{"Metric": m} for m in PI_METRICS], **args)
        report["performance_insights"] = {
            m["Key"]["Metric"]: {"meaning": PI_METRICS.get(m["Key"]["Metric"]),
                                 **_summary([p["Value"] for p in m["DataPoints"] if "Value" in p])}
            for m in metrics["MetricList"]}
        sql = pi.describe_dimension_keys(Metric="db.load.avg", GroupBy={"Group": "db.sql_tokenized", "Limit": top},
                                         **args)
        report["top_sql_by_load"] = [{"aas": k["Total"],
                                      "statement": k["Dimensions"].get("db.sql_tokenized.statement", "")[:400]}
                                     for k in sql["Keys"]]
        waits = pi.describe_dimension_keys(Metric="db.load.avg", GroupBy={"Group": "db.wait_event", "Limit": top},
                                           **args)
        report["top_waits_by_load"] = [{"aas": k["Total"], "wait": k["Dimensions"].get("db.wait_event.name"),
                                        "type": k["Dimensions"].get("db.wait_event.type")} for k in waits["Keys"]]
    else:
        report["performance_insights"] = "not enabled on this instance"

    cw = _client("cloudwatch").get_metric_data(StartTime=start, EndTime=end, MetricDataQueries=[
        {"Id": f"m{i}", "Label": name, "ReturnData": True, "MetricStat": {
            "Metric": {"Namespace": "AWS/RDS", "MetricName": name,
                       "Dimensions": [{"Name": "DBInstanceIdentifier", "Value": instance}]},
            "Period": period, "Stat": "Average"}} for i, name in enumerate(CLOUDWATCH_METRICS)])
    report["cloudwatch"] = {r["Label"]: _summary(r["Values"]) for r in cw["MetricDataResults"]}
    report["units"] = {"FreeableMemory": "bytes", "ReadLatency": "seconds", "WriteLatency": "seconds",
                       "aas": "average active sessions over the window"}
    return report
