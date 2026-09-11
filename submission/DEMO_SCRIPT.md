# 3-minute demo script

**0:00–0:20 — Problem**

“Production incidents create many alerts, but the expensive part is finding the causal chain. Deploy Detective turns one plain-language incident report into an investigation.”

**0:20–0:45 — Plan**

Enter: `What's wrong with checkout?`

Point at the plan: resolve the service, inspect error rate, correlate deploys, inspect downstream latency, compare history, decide, act, verify.

**0:45–1:25 — Exasol evidence**

Expand the SQL trace. Show the one-minute error rate, the moving baseline, the deploy six minutes before the spike, and the downstream p95 latency. Emphasize: “You can read the exact SQL. This is not a black-box RCA score.”

**1:25–1:55 — Decision**

Show the decision panel: high-confidence rollback. Point to deployment ID `DEP-checkout-bad` and version `v2.4.0`.

**1:55–2:20 — Action**

Show `SIMULATED_ROLLBACK` and say: “The action boundary is deliberately sandboxed. In production this adapter could target a deployment platform; here it only records an auditable replay action.”

**2:20–2:45 — Verification**

Show the final SQL and pre/post error rate. End on `VERIFIED RECOVERY`.

**2:45–3:00 — Close**

“Deploy Detective did not just summarize alerts. It planned an investigation, correlated multiple signals in Exasol, took a safe action, and queried the result to prove recovery.”
