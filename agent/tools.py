from __future__ import annotations

import os
import re
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from deployment.mock_deployer import MockDeploymentAPI



ROOT = Path(__file__).resolve().parents[1]
SQL_FILE = ROOT / "database" / "queries.sql"
SAFE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def load_queries() -> dict[str, str]:
    mapping = {
        "-- Q1:": "error_rate",
        "-- Q2:": "deploy_correlation",
        "-- Q3:": "dependency_latency",
        "-- Q4:": "historical_match",
        "-- Q5:": "verify_recovery",
    }
    blocks: dict[str, str] = {}
    current_name: str | None = None
    buffer: list[str] = []
    for line in SQL_FILE.read_text(encoding="utf-8").splitlines():
        hit = next((name for marker, name in mapping.items() if line.startswith(marker)), None)
        if hit:
            if current_name:
                blocks[current_name] = "\n".join(buffer).strip()
            current_name = hit
            buffer = [line]
        elif current_name:
            buffer.append(line)
    if current_name:
        blocks[current_name] = "\n".join(buffer).strip()
    return blocks


@dataclass
class QueryResult:
    name: str
    sql: str
    columns: list[str]
    rows: list[list[object]]
    elapsed_ms: float


class ExasolTools:
    def __init__(self) -> None:
        self.schema = os.getenv("EXASOL_SCHEMA", "DEPLOY_DETECTIVE")
        if not SAFE_NAME.match(self.schema):
            raise ValueError("EXASOL_SCHEMA contains an unsafe SQL identifier")
        self._connection = None
        self.queries = load_queries()

    def connect(self):
        if self._connection is None:
            verify = os.getenv("EXASOL_SSL_VERIFY", "1") == "1"
            import pyexasol
            self._connection = pyexasol.connect(
                dsn=f"{os.getenv('EXASOL_HOST', 'localhost')}:{os.getenv('EXASOL_PORT', '8563')}",
                user=os.getenv("EXASOL_USER", "SYS"),
                password=os.getenv("EXASOL_PASSWORD", ""),
                schema=self.schema,
                encryption=verify,
                validate_server_certificate=verify,
            )
        return self._connection

    @staticmethod
    def _sql_literal(value: str) -> str:
        return "'" + value.replace("'", "''") + "'"

    def render_sql(self, name: str, **params: str) -> str:
        statement = self.queries[name]
        for key, value in params.items():
            statement = statement.replace(f":{key}", self._sql_literal(str(value)))
        return statement

    def query(self, name: str, service_id: str | None = None, action_id: str | None = None, deploy_id: str | None = None) -> QueryResult:
        params: dict[str, str] = {}
        if service_id:
            params["service_id"] = service_id
        if action_id:
            params["action_id"] = action_id
        if deploy_id:
            params["deploy_id"] = deploy_id
        elif name == "dependency_latency":
            params["deploy_id"] = ""
        rendered = self.render_sql(name, **params)
        start = time.perf_counter()
        cur = self.connect().execute(rendered)
        rows = [list(row) for row in cur.fetchall()]
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        columns = [d[0] for d in cur.description] if cur.description else []
        return QueryResult(name=name, sql=rendered, columns=columns, rows=rows, elapsed_ms=elapsed_ms)

    def record_simulated_rollback(self, service_id: str, deploy_id: str, incident_id: str = "INC-001") -> dict:
        """Simulated deployment adapter.

        The action changes only the demo's audit/control layer. It does not call
        Kubernetes, CI/CD, GitHub, ArgoCD, or any external production system.
        Verification later reads telemetry that was already seeded for the replay.
        """
        deployment_api = MockDeploymentAPI()
        proposed = deployment_api.rollback(service_id, deploy_id)
        action_id = proposed.action_id
        con = self.connect()
        existing = con.execute(
            f"SELECT ACTION_ID, ACTIONED_AT FROM {self.schema}.AGENT_ACTIONS WHERE INCIDENT_ID = {self._sql_literal(incident_id)} ORDER BY ACTIONED_AT DESC LIMIT 1"
        ).fetchone()
        if existing:
            return {
                "action_id": str(existing[0]),
                "action_type": "ROLLBACK_DEPLOY",
                "deploy_id": deploy_id,
                "result": "ALREADY_APPLIED",
                "message": "A rollback action is already recorded for this demo incident; no duplicate action was created.",
                "simulated": True,
            }

        actioned_at = con.execute(
            f"SELECT DEPLOYED_AT + INTERVAL '12' MINUTE FROM {self.schema}.DEPLOYS WHERE DEPLOY_ID = {self._sql_literal(deploy_id)}"
        ).fetchone()[0]
        if actioned_at is None:
            raise RuntimeError(f"Could not determine rollback timestamp for deploy {deploy_id}")

        con.execute(
            f"""
            INSERT INTO {self.schema}.AGENT_ACTIONS
              (ACTION_ID, INCIDENT_ID, SERVICE_ID, ACTION_TYPE, TARGET_DEPLOY_ID, ACTIONED_AT, RESULT, DETAILS)
            VALUES
              ({self._sql_literal(action_id)}, {self._sql_literal(incident_id)}, {self._sql_literal(service_id)},
               'ROLLBACK_DEPLOY', {self._sql_literal(deploy_id)},
               TIMESTAMP '{actioned_at.strftime('%Y-%m-%d %H:%M:%S')}', 'SUCCESS',
               'Simulated deployment rollback for hackathon replay. No external deployment system was modified.')
            """
        )
        con.execute(
            f"""
            INSERT INTO {self.schema}.SCENARIO_EVENTS
              (EVENT_ID, INCIDENT_ID, SERVICE_ID, EVENT_TS, EVENT_TYPE, DETAILS)
            VALUES
              ({self._sql_literal('EVT-' + uuid.uuid4().hex[:12])}, {self._sql_literal(incident_id)},
               {self._sql_literal(service_id)}, TIMESTAMP '{actioned_at.strftime('%Y-%m-%d %H:%M:%S')}',
               'SIMULATED_ROLLBACK', 'Replay controller accepted rollback for verification.')
            """
        )
        return {
            "action_id": action_id,
            "action_type": "ROLLBACK_DEPLOY",
            "deploy_id": deploy_id,
            "actioned_at": actioned_at.isoformat(),
            "result": "SUCCESS",
            "message": "Simulated rollback accepted and audited in Exasol. Verification will read post-action telemetry only.",
            "simulated": True,
        }

    def health(self) -> dict:
        try:
            con = self.connect()
            result = con.execute("SELECT CURRENT_USER, CURRENT_SCHEMA").fetchone()
            table_rows = con.execute(
                f"SELECT COUNT(*) FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = {self._sql_literal(self.schema)}"
            ).fetchone()[0]
            return {
                "application": "ok",
                "exasol": "connected",
                "schema": self.schema,
                "user": result[0],
                "table_count": int(table_rows),
            }
        except Exception as exc:
            self._connection = None
            return {
                "application": "ok",
                "exasol": "unavailable",
                "schema": self.schema,
                "error": str(exc),
            }
