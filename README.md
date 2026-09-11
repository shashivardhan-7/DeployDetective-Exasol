# Deploy Detective

**An agent that finds the root cause, takes a safe action, and proves recovery — powered by Exasol Personal.**

Deploy Detective is an agentic AIOps prototype for microservice incidents. Instead of another alert dashboard, it runs a transparent investigation across logs, metrics, deployment history and historical incidents in Exasol.

## The core loop

```text
User: "What's wrong with checkout?"
                    ↓
                  PLAN
                    ↓
               INVESTIGATE
         ┌──────────┼───────────┐
         ↓          ↓           ↓
      errors     deploys    dependency
         └──────────┼───────────┘
                    ↓
                  DECIDE
                    ↓
              SIMULATED ACT
                    ↓
                 VERIFY
                    ↓
           VERIFIED RECOVERY
```

The application is built to make the agentic loop visible: judges can inspect the plan, open the exact SQL, see the deployment evidence, watch the action get audited, and then inspect the verification query.

## Why Exasol is central

Exasol is not just the persistence layer. It executes the RCA workload:

- high-volume `LOGS` aggregation into one-minute buckets;
- analytic-window baselines for spike detection;
- deploy-to-spike temporal joins;
- dependency-aware p95 latency calculations;
- historical incident joins;
- post-action verification over the same analytical store.

The exact SQL is versioned in `database/queries.sql` and the agent executes those same statements through `agent/tools.py`.

## Demo scenario

The deterministic generator creates a 10-service microservice graph with a known checkout incident:

1. `DEP-checkout-bad` deploys `v2.4.0` at 10:24.
2. Checkout errors spike at 10:30.
3. Payment latency also rises, creating a downstream signal.
4. The agent ranks the deploy as the strongest explanation.
5. The explicit action policy recommends rollback.
6. The simulated deployment adapter records the rollback in Exasol.
7. Verification re-queries the replay telemetry and confirms a lower post-action error rate.

No real production system is modified.

## Repository

```text
DeployDetective/
├── app/
│   └── main.py
├── agent/
│   ├── decision.py
│   ├── investigator.py
│   ├── narrative.py
│   ├── planner.py
│   └── tools.py
├── deployment/
│   ├── __init__.py
│   └── mock_deployer.py
├── database/
│   ├── schema.sql
│   └── queries.sql
├── scripts/
│   ├── benchmark.py
│   ├── seed_demo.py
│   ├── setup_exasol.py
│   └── smoke_test.py
├── static/
│   ├── app.js
│   ├── index.html
│   └── styles.css
├── tests/
│   ├── test_decision.py
│   ├── test_planner.py
│   └── test_tools.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── EXASOL_DEMO.md
│   ├── JUDGE_WALKTHROUGH.md
│   ├── SECURITY.md
│   └── TROUBLESHOOTING.md
├── data/
│   └── README.md
├── submission/
│   ├── DEMO_SCRIPT.md
│   ├── PITCH_DECK_OUTLINE.md
│   └── README.md
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── RUN_GUIDE.md
└── requirements.txt
```

## Quick start

Follow the full [RUN_GUIDE.md](RUN_GUIDE.md). The shortest path is:

```bash
python -m venv .venv
# activate the environment
pip install -r requirements.txt
cp .env.example .env
python scripts/setup_exasol.py
python scripts/seed_demo.py --logs 250000 --metrics 60000
python scripts/smoke_test.py
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000` and use:

```text
What's wrong with checkout?
```

## Tests and benchmark

Unit tests:

```bash
pytest -q
```

Runtime benchmark:

```bash
python scripts/benchmark.py
```

The benchmark reports the evaluator's measured timings; the repository does not hard-code a “sub-second” result.

## Safety boundary

The deployment action is intentionally simulated. The project demonstrates the **action + verification** behavior without creating a real production change. A production deployment adapter would require authentication, authorization, approval policy, idempotency and a real audit trail.

## Design choices

**Single agent:** one coherent investigation thread is more meaningful than decorative multi-agent orchestration.

**No mandatory external LLM:** the core investigation is deterministic and reproducible. An LLM can be added later for richer intent/narrative, but a missing model key cannot break the database-backed demo.

**Plain HTML/CSS/JS:** no Node.js or frontend build chain is required for the evaluator.

## Primary track

**AI Agents That Get Things Done**

The project demonstrates a complete tool-using loop: understand the request, plan a multi-step investigation, query structured data, make a decision, take an action, and verify the outcome.

## License

MIT — see [LICENSE](LICENSE).
