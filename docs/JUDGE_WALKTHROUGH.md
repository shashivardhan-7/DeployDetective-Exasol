# Judge walkthrough

This is the shortest end-to-end evaluator path.

## Prerequisites

- Python 3.11+
- Exasol Personal reachable from the machine running the app

## Run

```bash
git clone <PUBLIC_REPOSITORY_URL>
cd deploydetective
python -m venv .venv
```

Activate the environment, then:

```bash
pip install -r requirements.txt
cp .env.example .env
python scripts/setup_exasol.py
python scripts/seed_demo.py --logs 250000 --metrics 60000
python scripts/smoke_test.py
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000` and submit:

```text
What's wrong with checkout?
```

## Expected result

The trace should show:

- a service-specific investigation plan;
- Exasol error-rate SQL;
- Exasol deploy/spike correlation;
- downstream p95 SQL;
- historical incident SQL;
- a rollback decision;
- a simulated, audited rollback;
- verification SQL with a lower post-action error rate;
- `VERIFIED RECOVERY` in the UI.

## What to inspect

- `database/queries.sql` — the transparent analytical evidence.
- `agent/investigator.py` — the agent loop.
- `agent/decision.py` — the explicit action policy.
- `agent/tools.py` — Exasol + action tool boundary.
- `scripts/benchmark.py` — measured performance.
