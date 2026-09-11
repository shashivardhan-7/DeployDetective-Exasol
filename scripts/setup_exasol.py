from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def connection_kwargs() -> dict:
    verify = os.getenv("EXASOL_SSL_VERIFY", "1") == "1"
    return {
        "dsn": f"{os.getenv('EXASOL_HOST', 'localhost')}:{os.getenv('EXASOL_PORT', '8563')}",
        "user": os.getenv("EXASOL_USER", "SYS"),
        "password": os.getenv("EXASOL_PASSWORD", ""),
        "encryption": verify,
        "validate_server_certificate": verify,
    }


def main() -> None:
    import pyexasol
    sql = (ROOT / "database" / "schema.sql").read_text(encoding="utf-8")
    con = pyexasol.connect(**connection_kwargs())
    for statement in (part.strip() for part in sql.split(";")):
        if statement:
            con.execute(statement)
    print("Deploy Detective schema initialized successfully.")


if __name__ == "__main__":
    main()
