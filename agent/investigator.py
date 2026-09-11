from __future__ import annotations

from dataclasses import asdict

from .decision import decide_remediation
from .narrative import build_narrative
from .planner import make_plan
from .tools import ExasolTools


class Investigator:
    def __init__(self, tools: ExasolTools | None = None):
        self.tools = tools or ExasolTools()

    def run(self, request: str) -> dict:
        plan = make_plan(request)
        trace: list[dict] = [
            {
                "step": 1,
                "name": "Plan investigation",
                "status": "complete",
                "detail": asdict(plan),
            }
        ]

        q1 = self.tools.query("error_rate", service_id=plan.service_id)
        trace.append(
            {
                "step": 2,
                "name": "Measure error-rate timeline",
                "status": "complete",
                "elapsed_ms": q1.elapsed_ms,
                "sql": q1.sql,
                "columns": q1.columns,
                "rows": q1.rows[-20:],
            }
        )

        q2 = self.tools.query("deploy_correlation", service_id=plan.service_id)
        trace.append(
            {
                "step": 3,
                "name": "Correlate deploy with spike",
                "status": "complete",
                "elapsed_ms": q2.elapsed_ms,
                "sql": q2.sql,
                "columns": q2.columns,
                "rows": q2.rows[:10],
            }
        )

        candidate_deploy_id = str(q2.rows[0][0]) if q2.rows else ""
        q3 = self.tools.query("dependency_latency", service_id=plan.service_id, deploy_id=candidate_deploy_id)
        trace.append(
            {
                "step": 4,
                "name": "Check downstream latency",
                "status": "complete",
                "elapsed_ms": q3.elapsed_ms,
                "sql": q3.sql,
                "columns": q3.columns,
                "rows": q3.rows[:10],
            }
        )

        q4 = self.tools.query("historical_match", service_id=plan.service_id)
        trace.append(
            {
                "step": 5,
                "name": "Match historical incidents",
                "status": "complete",
                "elapsed_ms": q4.elapsed_ms,
                "sql": q4.sql,
                "columns": q4.columns,
                "rows": q4.rows[:10],
            }
        )

        decision = decide_remediation(q2.rows, q3.rows, q4.rows)
        narrative = build_narrative(plan.service_id, q2.rows, q3.rows, q4.rows, decision.action)
        trace.append(
            {
                "step": 6,
                "name": "Decide remediation",
                "status": "complete",
                "decision": decision.action,
                "confidence": decision.confidence,
                "evidence": decision.rationale,
            }
        )

        action = None
        if decision.action == "ROLLBACK" and q2.rows:
            deploy_id = str(q2.rows[0][0])
            action = self.tools.record_simulated_rollback(plan.service_id, deploy_id)
            trace.append(
                {
                    "step": 7,
                    "name": "Execute simulated rollback",
                    "status": "complete",
                    **action,
                }
            )

            q5 = self.tools.query("verify_recovery", action_id=action["action_id"])
            verified = False
            if q5.rows:
                pre_rate = q5.rows[0][3]
                post_rate = q5.rows[0][4]
                verified = pre_rate is not None and post_rate is not None and float(post_rate) < float(pre_rate)
            trace.append(
                {
                    "step": 8,
                    "name": "Verify recovery",
                    "status": "complete" if verified else "warning",
                    "elapsed_ms": q5.elapsed_ms,
                    "sql": q5.sql,
                    "columns": q5.columns,
                    "rows": q5.rows,
                    "verified": verified,
                }
            )
        else:
            trace.append(
                {
                    "step": 7,
                    "name": "Action gate",
                    "status": "skipped",
                    "decision": "OBSERVE",
                    "message": "Safety policy did not authorize an automated rollback.",
                }
            )

        verified = bool(trace[-1].get("verified", False))
        return {
            "service_id": plan.service_id,
            "request": request,
            "plan": plan.steps,
            "intent": plan.intent,
            "planner_confidence": plan.confidence,
            "decision": decision.action,
            "decision_confidence": decision.confidence,
            "narrative": narrative,
            "trace": trace,
            "verified": verified,
            "action": action,
        }
