# Architecture

```text
                    +-----------------------+
                    |    SRE / Judge        |
                    +-----------+-----------+
                                |
                                v
                    +-----------------------+
                    | FastAPI + plain web UI |
                    +-----------+-----------+
                                |
                                v
                    +-----------------------+
                    | Deploy Detective Agent |
                    | plan → investigate     |
                    | → decide → act → verify|
                    +-----+-------------+-----+
                          |             |
                 SQL tool |             | action tool
                          |             |
                          v             v
                 +----------------+  +-------------------+
                 | Exasol Personal|  | Simulated deploy |
                 | logs            |  | rollback API      |
                 | metrics         |  | audit/control     |
                 | deploys         |  +-------------------+
                 | incidents       |
                 | actions/events |
                 +--------+-------+
                          |
                          v
                    Verification SQL
                          |
                          v
                  VERIFIED RECOVERY
```

## Why one agent?

A single investigation thread is enough: the agent has one user intent, one evidence chain and one action policy. Splitting this into separate “log agent”, “metric agent” and “deploy agent” would add orchestration overhead without adding meaningful capability for this demo.

## Agent loop

1. **Plan** — resolve the service and investigation intent.
2. **Investigate** — execute transparent Exasol SQL for error rate, deployment correlation, downstream p95 and historical incidents.
3. **Decide** — apply an explicit evidence policy to the query results.
4. **Act** — invoke the simulated deployment adapter and record an auditable action.
5. **Verify** — re-query telemetry after the action and compare pre/post error rate.

## Safety boundary

The action adapter never changes a real production system. `deployment/mock_deployer.py` is the local deployment boundary; `SCENARIO_EVENTS` records the simulated action, while the verification query is strictly read-only.
