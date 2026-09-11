from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def main() -> None:
    import pyexasol
    verify = os.getenv("EXASOL_SSL_VERIFY", "1") == "1"
    con = pyexasol.connect(
        dsn=f"{os.getenv('EXASOL_HOST', 'localhost')}:{os.getenv('EXASOL_PORT', '8563')}",
        user=os.getenv("EXASOL_USER", "SYS"),
        password=os.getenv("EXASOL_PASSWORD", ""),
        schema=os.getenv("EXASOL_SCHEMA", "DEPLOY_DETECTIVE"),
        encryption=verify,
        validate_server_certificate=verify,
    )
    schema = os.getenv("EXASOL_SCHEMA", "DEPLOY_DETECTIVE")
    required = ["SERVICES", "DEPLOYS", "LOGS", "METRICS", "INCIDENTS", "AGENT_ACTIONS", "SCENARIO_EVENTS"]
    for table in required:
        count = int(con.execute(f"SELECT COUNT(*) FROM {schema}.{table}").fetchone()[0])
        print(f"PASS {table:18s} {count:,} rows")
    print("Smoke test passed.")


if __name__ == "__main__":
    main()
