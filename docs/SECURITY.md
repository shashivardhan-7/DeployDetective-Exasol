# Security and safety

- Do not commit `.env` or credentials.
- Exasol credentials are read from environment variables only.
- SQL values are escaped before being substituted into the demo queries.
- `EXASOL_SCHEMA` is restricted to a safe identifier pattern.
- The rollback adapter is simulated and cannot change a real deployment system.
- The verification query is read-only; it never inserts “success” telemetry.
- A production adapter would require authentication, authorization, approval policy, idempotency and audit controls before any real change.
