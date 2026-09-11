# Troubleshooting

## `/api/health` says Exasol unavailable

1. Confirm Exasol Personal is running and reachable.
2. Check `EXASOL_HOST`, `EXASOL_PORT`, `EXASOL_USER` and `EXASOL_PASSWORD` in `.env`.
3. Check the TLS setting. Keep `EXASOL_SSL_VERIFY=1` for normal trusted deployments.
4. Run `python scripts/setup_exasol.py` again after connectivity is fixed.

## Schema exists but investigation fails

Run:

```bash
python scripts/seed_demo.py --logs 250000 --metrics 60000
python scripts/smoke_test.py
```

## Demo already ran once

The seed script clears and rebuilds the demo tables. The simulated rollback is idempotent for `INC-001`, so refreshing the browser does not create a pile of duplicate actions.

## Want a larger workload?

Run:

```bash
python scripts/seed_demo.py --logs 1000000 --metrics 120000
python scripts/benchmark.py
```

Use the measured benchmark output in your presentation rather than claiming a fixed number in advance.
