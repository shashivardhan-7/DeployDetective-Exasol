from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import uuid


@dataclass(frozen=True)
class RollbackResult:
    action_id: str
    service_id: str
    deploy_id: str
    action_type: str
    actioned_at: datetime
    result: str
    simulated: bool = True
    message: str = "Simulated rollback accepted. No production system was modified."


class MockDeploymentAPI:
    """A local stand-in for a real deployment platform API.

    In a production installation this boundary could be replaced with an
    authenticated Kubernetes/Argo/CD deployment client. The hackathon adapter
    never performs an external network call.
    """

    def rollback(self, service_id: str, deploy_id: str) -> RollbackResult:
        return RollbackResult(
            action_id="ACT-" + uuid.uuid4().hex[:12],
            service_id=service_id,
            deploy_id=deploy_id,
            action_type="ROLLBACK_DEPLOY",
            actioned_at=datetime.now(timezone.utc),
            result="SUCCESS",
        )
