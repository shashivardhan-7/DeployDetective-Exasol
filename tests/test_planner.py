import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.planner import make_plan


def test_checkout_resolution():
    plan = make_plan("checkout is slow")
    assert plan.service_id == "checkout"
    assert plan.intent == "service_incident_investigation"
    assert "query_error_rate" in plan.steps
    assert plan.steps[-1] == "verify_recovery"


def test_payment_resolution():
    plan = make_plan("why is payment failing?")
    assert plan.service_id == "payment"


def test_unknown_request_defaults_to_safe_demo_service():
    plan = make_plan("investigate the production checkout path")
    assert plan.service_id == "checkout"
