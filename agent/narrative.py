from __future__ import annotations


def build_narrative(
    service_id: str,
    deploy_rows: list[list[object]],
    dependency_rows: list[list[object]],
    historical_rows: list[list[object]],
    decision: str,
) -> str:
    if not deploy_rows:
        return (
            f"No strong deployment correlation was found for {service_id}. "
            "The agent keeps the incident open rather than guessing."
        )

    first = deploy_rows[0]
    deploy_id = first[0]
    version = first[3]
    spike = first[7] if len(first) > 7 else "unknown"
    delta = first[8] if len(first) > 8 else "unknown"
    downstream = dependency_rows[0][5] if len(dependency_rows[0]) > 5 else "downstream service"
    p95 = dependency_rows[0][4] if len(dependency_rows[0]) > 4 else "unknown"
    historical = len(historical_rows)

    action_sentence = (
        "The policy therefore recommends a simulated rollback." if decision == "ROLLBACK"
        else "The policy does not cross the rollback threshold, so the agent keeps observing."
    )

    return (
        f"The strongest root-cause hypothesis is deploy {deploy_id} ({version}) on {service_id}. "
        f"Exasol found a {spike}% error-rate bucket with a {delta} percentage-point spike above its moving baseline, "
        f"about {first[8]} minutes from the deploy. The dependency check also found p95 latency of {p95} ms on {downstream}. "
        f"{historical} historical incident record(s) were available for comparison. {action_sentence}"
    )
