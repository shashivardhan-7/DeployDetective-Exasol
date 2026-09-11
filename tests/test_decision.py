import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.decision import decide_remediation


def test_strong_correlation_requests_rollback():
    deploy_rows = [["DEP-1", "checkout", None, "v2", None, None, None, 28.0, 6.0]]
    decision = decide_remediation(deploy_rows, [["DEP-1", "v2", None, "payment", 620, "Payment"]], [])
    assert decision.action == "ROLLBACK"
    assert decision.confidence >= 0.8


def test_weak_correlation_observes():
    deploy_rows = [["DEP-1", "checkout", None, "v2", None, None, None, 4.0, 24.0]]
    decision = decide_remediation(deploy_rows, [], [])
    assert decision.action == "OBSERVE"
