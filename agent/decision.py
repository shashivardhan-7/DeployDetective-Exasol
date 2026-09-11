from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RemediationDecision:
    action: str
    confidence: float
    rationale: str


def decide_remediation(
    deploy_rows: list[list[object]],
    dependency_rows: list[list[object]],
    historical_rows: list[list[object]],
) -> RemediationDecision:
    """Deterministic policy layer: the evidence decides, not the UI.

    The first deploy-correlation row is already ranked by the Exasol query.
    We require a meaningful spike and a deploy inside the correlation window.
    """
    if not deploy_rows:
        return RemediationDecision(
            action="OBSERVE",
            confidence=0.25,
            rationale="No deployment aligned with an elevated error-rate bucket. Keep the incident open for deeper investigation.",
        )

    row = deploy_rows[0]
    spike_delta = float(row[7]) if row[7] is not None else 0.0
    minutes_from_deploy = float(row[8]) if row[8] is not None else 999.0

    # High-confidence rollback when the Exasol evidence shows a sizeable spike
    # shortly after a deploy. Dependency/historical evidence increases confidence.
    if spike_delta >= 10.0 and minutes_from_deploy <= 15.0:
        confidence = 0.82
        if dependency_rows:
            confidence += 0.07
        if historical_rows:
            confidence += 0.03
        return RemediationDecision(
            action="ROLLBACK",
            confidence=min(confidence, 0.97),
            rationale=(
                "A deployment on the affected service is tightly aligned with a large error-rate increase. "
                "Downstream and historical evidence strengthen the hypothesis, so the safe demo action is rollback."
            ),
        )

    return RemediationDecision(
        action="OBSERVE",
        confidence=0.50,
        rationale="The temporal correlation is not strong enough to justify an automated rollback in the demo policy.",
    )
