# Synthetic data

No production logs, metrics, credentials or deployment artifacts are included in this project.

`scripts/seed_demo.py` generates deterministic telemetry for a 10-service microservice graph and injects a known checkout incident:

- bad deploy at 10:24;
- error spike at 10:30;
- simulated rollback at 10:36;
- recovery telemetry after the action.

The generator can scale the log and metric row counts for a stronger Exasol benchmark.
