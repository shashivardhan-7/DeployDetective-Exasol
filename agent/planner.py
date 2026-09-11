from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class InvestigationPlan:
    service_id: str
    user_request: str
    intent: str
    confidence: float
    steps: list[str]


SERVICE_ALIASES = {
    "checkout": "checkout",
    "payment": "payment",
    "catalog": "catalog",
    "inventory": "inventory",
    "auth": "auth",
    "search": "search",
    "shipping": "shipping",
    "notification": "notification",
    "recommendation": "recommendation",
    "fraud": "fraud",
}


INVESTIGATION_STEPS = [
    "resolve_intent",
    "query_error_rate",
    "correlate_recent_deploys",
    "check_downstream_latency",
    "match_historical_incidents",
    "decide_remediation",
    "execute_simulated_rollback",
    "verify_recovery",
]


def make_plan(request: str) -> InvestigationPlan:
    text = request.lower().strip()
    if not text:
        raise ValueError("request cannot be empty")

    matches = [sid for alias, sid in SERVICE_ALIASES.items() if re.search(rf"\b{re.escape(alias)}\b", text)]
    service_id = matches[0] if matches else "checkout"
    confidence = 0.98 if matches else 0.55
    intent = "service_incident_investigation"

    return InvestigationPlan(
        service_id=service_id,
        user_request=request,
        intent=intent,
        confidence=confidence,
        steps=INVESTIGATION_STEPS.copy(),
    )
