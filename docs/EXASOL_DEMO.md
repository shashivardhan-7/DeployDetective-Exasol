# Exasol demo notes

Deploy Detective is intentionally database-first. The judge can inspect the exact SQL in `database/queries.sql`, then watch those same queries execute through `agent/tools.py`.

## Q1 — Error-rate timeline

`LOGS` is aggregated into one-minute buckets. This is the first signal used to identify an incident-shaped deviation.

## Q2 — Deploy correlation

A moving baseline is calculated with an analytic window function. Elevated buckets are joined to `DEPLOYS` for the affected service and scored by their distance from the deploy.

## Q3 — Dependency signal

The service dependency graph in `SERVICES` is joined with `METRICS`, and p95 downstream latency is computed with `PERCENTILE_CONT` over a deploy-relative time window.

## Q4 — Historical context

The current service is compared with previous incidents and their known root-cause deployments.

## Q5 — Verification

After the simulated rollback is recorded, a new read over the replay telemetry calculates pre-action and post-action error rate. The query does not create the recovery evidence.

## Benchmark discipline

`scripts/benchmark.py` measures the same query path at runtime. The application does not hard-code a “sub-second” claim; the benchmark prints whatever the evaluator's Exasol environment actually measures.
