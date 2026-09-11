# Pitch deck outline

1. **Title** — Deploy Detective: find the cause, take the safe action, prove recovery.
2. **Problem** — Alert floods hide causal chains across logs, metrics and deploy history.
3. **Gap** — AIOps products often hide correlation behind black-box search/ML pipelines.
4. **Solution** — One agent with an explicit Plan → Investigate → Decide → Act → Verify loop.
5. **Why Exasol** — High-volume SQL analytics, time-window joins, window functions and p95 calculations in one explainable data layer.
6. **Architecture** — Plain web UI → agent → Exasol SQL tools + simulated deployment adapter → verification.
7. **Live incident** — checkout deploy → error spike → downstream latency → rollback → recovery.
8. **Technical excellence** — deterministic generator, reusable SQL, measured benchmark, unit tests, health check, action audit.
9. **Safety** — simulated action boundary; no real production changes.
10. **Future** — OpenTelemetry/Prometheus ingestion and policy-controlled real deployment adapters.
