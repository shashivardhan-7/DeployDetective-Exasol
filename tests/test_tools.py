import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.tools import load_queries


def test_all_query_blocks_are_loaded():
    queries = load_queries()
    assert set(queries) == {
        "error_rate",
        "deploy_correlation",
        "dependency_latency",
        "historical_match",
        "verify_recovery",
    }


def test_dependency_query_accepts_candidate_deploy_filter():
    sql = load_queries()["dependency_latency"]
    assert ":deploy_id" in sql


def test_verify_query_is_read_only():
    sql = load_queries()["verify_recovery"].upper()
    assert "INSERT INTO" not in sql
    assert "UPDATE " not in sql
    assert "DELETE FROM" not in sql
