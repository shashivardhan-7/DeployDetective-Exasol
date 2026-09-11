# Deploy Detective — Run Guide

This guide is intentionally copy/paste oriented for an evaluator using a clean machine.

## Prerequisites

- Python 3.11+
- Exasol Personal reachable from the machine running this project
- Exasol credentials supplied by the evaluator's environment
- Node.js is **not** required

## 1. Clone and create the environment

```bash
git clone <PUBLIC_REPOSITORY_URL>
cd deploydetective
python -m venv .venv
```

### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 2. Configure Exasol

```bash
cp .env.example .env
```

Fill in the connection values:

```text
EXASOL_HOST=...
EXASOL_PORT=8563
EXASOL_USER=SYS
EXASOL_PASSWORD=...
EXASOL_SCHEMA=DEPLOY_DETECTIVE
EXASOL_SSL_VERIFY=1
```

Use the TLS mode appropriate to the evaluator's Exasol Personal deployment.

## 3. Build the schema

```bash
python scripts/setup_exasol.py
```

Expected output:

```text
Deploy Detective schema initialized successfully.
```

## 4. Seed the deterministic replay

Quick judge run:

```bash
python scripts/seed_demo.py --logs 250000 --metrics 60000
```

Larger benchmark run:

```bash
python scripts/seed_demo.py --logs 1000000 --metrics 120000
```

Expected output names the demo incident:

```text
INC-001 / checkout / DEP-checkout-bad / v2.4.0
```

## 5. Smoke test Exasol

```bash
python scripts/smoke_test.py
```

This confirms that all required tables exist and contain data.

## 6. Start Deploy Detective

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open:

`http://127.0.0.1:8000`

The API health endpoint is:

`http://127.0.0.1:8000/api/health`

Unlike a static health response, this endpoint actually checks Exasol connectivity.

## 7. Run the live demo

Enter:

```text
What's wrong with checkout?
```

The expected trace is:

```text
01  Plan investigation
02  Measure error-rate timeline
03  Correlate deploy with spike
04  Check downstream latency
05  Match historical incidents
06  Decide remediation → ROLLBACK
07  Execute simulated rollback
08  Verify recovery → VERIFIED
```

The UI shows the actual SQL text and the measured time returned by Exasol for each query.

## 8. Run tests

The local unit tests do not require Exasol:

```bash
pytest -q
```

## 9. Run the benchmark

```bash
python scripts/benchmark.py
```

The benchmark prints row counts and runtime measurements. Do not replace those results with a hand-written performance claim.

## 10. What is intentionally simulated?

The rollback is **simulated**. The adapter writes an audit record and replay event in Exasol; it does not contact Kubernetes, Argo CD, GitHub Actions or any real deployment environment.

The verification step is real database analysis: it reads telemetry that was seeded for the deterministic incident replay and confirms that post-action error rate is lower than the pre-action window.
