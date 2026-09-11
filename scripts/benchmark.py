from __future__ import annotations

import os
import time
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

from agent.tools import ExasolTools  # noqa: E402


def main() -> None:
    tools = ExasolTools()
    print("DEPLOY DETECTIVE — EXASOL BENCHMARK")
    print("=" * 52)
    print("Measured at runtime; no timing numbers are hard-coded.\n")

    con = tools.connect()
    schema = tools.schema
    counts = {}
    for table in ["LOGS", "METRICS", "DEPLOYS", "INCIDENTS", "AGENT_ACTIONS"]:
        counts[table] = int(con.execute(f"SELECT COUNT(*) FROM {schema}.{table}").fetchone()[0])
    for table, value in counts.items():
        print(f"{table:16s} {value:>12,}")

    print("\nQUERY TIMINGS")
    print("-" * 32)
    for name in ["error_rate", "deploy_correlation", "dependency_latency", "historical_match"]:
        start = time.perf_counter()
        result = tools.query(name, service_id="checkout")
        measured = (time.perf_counter() - start) * 1000.0
        print(f"{name:28s} {measured:9.2f} ms  ({len(result.rows):,} rows)")


if __name__ == "__main__":
    main()
