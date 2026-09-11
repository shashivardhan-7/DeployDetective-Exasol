from __future__ import annotations

import argparse
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

SERVICES = [
    ("checkout", "Checkout", "commerce", "payment"),
    ("payment", "Payment", "commerce", "fraud"),
    ("catalog", "Catalog", "commerce", None),
    ("inventory", "Inventory", "commerce", None),
    ("auth", "Auth", "platform", None),
    ("search", "Search", "commerce", "catalog"),
    ("shipping", "Shipping", "commerce", None),
    ("notification", "Notification", "platform", None),
    ("recommendation", "Recommendation", "growth", "catalog"),
    ("fraud", "Fraud", "risk", None),
]

BASE = datetime(2026, 9, 11, 8, 0, 0)
INCIDENT_DEPLOY = BASE + timedelta(hours=2, minutes=24)
SPIKE = INCIDENT_DEPLOY + timedelta(minutes=6)
ACTION_AT = SPIKE + timedelta(minutes=6)
END = BASE + timedelta(hours=3)


def chunks(items, size=10000):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def connect():
    import pyexasol
    verify = os.getenv("EXASOL_SSL_VERIFY", "1") == "1"
    return pyexasol.connect(
        dsn=f"{os.getenv('EXASOL_HOST', 'localhost')}:{os.getenv('EXASOL_PORT', '8563')}",
        user=os.getenv("EXASOL_USER", "SYS"),
        password=os.getenv("EXASOL_PASSWORD", ""),
        schema=os.getenv("EXASOL_SCHEMA", "DEPLOY_DETECTIVE"),
        encryption=verify,
        validate_server_certificate=verify,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic Deploy Detective replay data.")
    parser.add_argument("--logs", type=int, default=250_000, help="Number of log rows to insert.")
    parser.add_argument("--metrics", type=int, default=60_000, help="Base metric timestamps per service; each timestamp produces two metric rows.")
    args = parser.parse_args()
    if args.logs < 10 or args.metrics < 10:
        raise SystemExit("logs and metrics must be at least 10")

    schema = os.getenv("EXASOL_SCHEMA", "DEPLOY_DETECTIVE")
    con = connect()

    for table in ["AGENT_ACTIONS", "SCENARIO_EVENTS", "INCIDENTS", "METRICS", "LOGS", "DEPLOYS", "SERVICES"]:
        con.execute(f"DELETE FROM {schema}.{table}")

    con.executemany(
        f"INSERT INTO {schema}.SERVICES (SERVICE_ID,SERVICE_NAME,TEAM,DEPENDS_ON) VALUES (?,?,?,?)",
        SERVICES,
    )

    deploys = []
    for sid, *_ in SERVICES:
        deploys.append((f"DEP-{sid}-old", sid, BASE + timedelta(hours=1), "v2.3.9", "team-platform", "Routine release", "ACTIVE"))
    deploys.extend([
        ("DEP-checkout-bad", "checkout", INCIDENT_DEPLOY, "v2.4.0", "team-checkout", "Checkout performance change", "ACTIVE"),
        ("DEP-checkout-next", "checkout", ACTION_AT + timedelta(minutes=12), "v2.4.1", "team-checkout", "Rollback target version", "PENDING"),
    ])
    con.executemany(
        f"INSERT INTO {schema}.DEPLOYS (DEPLOY_ID,SERVICE_ID,DEPLOYED_AT,VERSION,AUTHOR,CHANGE_SUMMARY,STATUS) VALUES (?,?,?,?,?,?,?)",
        deploys,
    )

    con.execute(
        f"""
        INSERT INTO {schema}.INCIDENTS
        VALUES ('INC-001','checkout',TIMESTAMP '2026-09-11 10:30:00',NULL,'DEP-checkout-bad','Checkout 5xx spike after deploy','OPEN')
        """
    )
    con.execute(
        f"""
        INSERT INTO {schema}.INCIDENTS
        VALUES ('INC-000','checkout',TIMESTAMP '2026-08-21 14:12:00',TIMESTAMP '2026-08-21 14:22:00','DEP-checkout-old','Checkout timeout incident','RESOLVED')
        """
    )

    rng = random.Random(7)
    service_ids = [row[0] for row in SERVICES]
    logs: list[tuple] = []
    per_service = max(1, args.logs // len(service_ids))

    for sid in service_ids:
        for i in range(per_service):
            minute = i % 180
            ts = BASE + timedelta(minutes=minute, seconds=rng.randint(0, 59))
            level = rng.choices(["INFO", "WARN", "ERROR"], weights=[72, 18, 10], k=1)[0]
            message = "request completed"
            if sid == "checkout" and SPIKE <= ts < ACTION_AT:
                level = "ERROR" if rng.random() < 0.80 else "WARN"
                message = "checkout upstream timeout: payment dependency"
            elif sid == "payment" and SPIKE <= ts < ACTION_AT:
                level = "ERROR" if rng.random() < 0.48 else "WARN"
                message = "payment dependency timeout"
            logs.append((sid, ts.strftime("%Y-%m-%d %H:%M:%S"), level, message))

    logs = logs[: args.logs]
    logs_with_ids = [(idx + 1, *row) for idx, row in enumerate(logs)]
    for batch in chunks(logs_with_ids):
        con.executemany(
            f"INSERT INTO {schema}.LOGS (LOG_ID,SERVICE_ID,TS,LEVEL,MESSAGE) VALUES (?,?,?,?,?)",
            batch,
        )

    metric_rows: list[tuple] = []
    points = max(1, args.metrics // len(service_ids))
    for sid in service_ids:
        for i in range(points):
            ts = BASE + timedelta(minutes=i % 180, seconds=15)
            if sid == "checkout" and SPIKE <= ts < ACTION_AT:
                err, latency = 0.34, 620
            elif sid == "checkout" and ts >= ACTION_AT:
                minutes_after = max(0, int((ts - ACTION_AT).total_seconds() // 60))
                err = max(0.02, 0.08 - 0.006 * minutes_after)
                latency = max(180, 520 - 25 * minutes_after)
            elif sid == "checkout":
                err, latency = 0.03, 180
            elif sid == "payment" and SPIKE <= ts < ACTION_AT:
                err, latency = 0.18, 540
            elif sid == "payment" and ts >= ACTION_AT:
                err, latency = 0.03, 190
            else:
                err, latency = 0.02, 160
            metric_rows.append((sid, ts.strftime("%Y-%m-%d %H:%M:%S"), "error_rate", err))
            metric_rows.append((sid, ts.strftime("%Y-%m-%d %H:%M:%S"), "p95_latency_ms", latency))

    for batch in chunks(metric_rows):
        con.executemany(
            f"INSERT INTO {schema}.METRICS (SERVICE_ID,TS,METRIC_NAME,VALUE) VALUES (?,?,?,?)",
            batch,
        )

    print(f"Seeded {len(logs_with_ids):,} log rows and {len(metric_rows):,} metric rows.")
    print("Demo incident: INC-001 / checkout / DEP-checkout-bad / v2.4.0")
    print("Expected causal chain: deploy 10:24 → spike 10:30 → simulated rollback 10:36 → recovery")
    print("Investigation prompt: What's wrong with checkout?")


if __name__ == "__main__":
    main()
