"""Detect missing or insufficient retries on nodes that need them."""

from __future__ import annotations
from .base import Finding, Severity
from ..parser import get_node_setting, is_http_or_api_node, is_write_side_effect_node


def check_retries(wf: dict) -> list[Finding]:
    findings: list[Finding] = []

    for node in wf["nodes"]:
        name = node["name"]
        ntype = (node.get("type") or "").lower()

        # Skip pure triggers and pure code nodes that don't call out
        if any(x in ntype for x in ("trigger", "manual", "set", "if", "switch", "code", "function")):
            # Still check HTTP Request / AI nodes even if named strangely
            if not is_http_or_api_node(node):
                continue

        retry_on_fail = get_node_setting(node, "retryOnFail") or get_node_setting(
            node, "retry_on_fail"
        )
        max_tries = get_node_setting(node, "maxTries") or get_node_setting(node, "max_tries") or 1
        wait_ms = (
            get_node_setting(node, "waitBetweenTries")
            or get_node_setting(node, "wait_between_tries")
            or 0
        )

        needs_retry = is_http_or_api_node(node)

        if needs_retry and not retry_on_fail:
            findings.append(
                Finding(
                    check_id="RTY-001",
                    title=f"No Retry On Fail enabled: {name}",
                    severity=Severity.HIGH,
                    node_name=name,
                    description=(
                        f"Node '{name}' calls an external service but Retry On Fail is disabled. "
                        "Transient 429/5xx/timeouts will fail the execution immediately."
                    ),
                    evidence=f"retryOnFail={retry_on_fail}, maxTries={max_tries}, waitBetweenTries={wait_ms}",
                    recommendation=(
                        "Open the node → Settings → enable Retry On Fail. "
                        "Recommended defaults for most APIs: Max Tries = 3, "
                        "Wait Between Tries = 2000–3000 ms. "
                        "For known rate-limited services increase the wait above the rate-limit window."
                    ),
                    effort_minutes=5,
                    tags=["retries", "resilience"],
                )
            )
        elif needs_retry and retry_on_fail and (int(max_tries) < 2 or int(wait_ms) < 1000):
            findings.append(
                Finding(
                    check_id="RTY-002",
                    title=f"Weak retry configuration: {name}",
                    severity=Severity.MEDIUM,
                    node_name=name,
                    description=(
                        f"Node '{name}' has Retry On Fail enabled but the values are too aggressive "
                        f"(maxTries={max_tries}, wait={wait_ms} ms). Immediate retries often hit the "
                        "same rate-limit or transient outage again."
                    ),
                    evidence=f"maxTries={max_tries}, waitBetweenTries={wait_ms}",
                    recommendation=(
                        "Raise Max Tries to at least 3 and Wait Between Tries to ≥ 2000 ms "
                        "(or higher for strict rate limits)."
                    ),
                    effort_minutes=3,
                    tags=["retries"],
                )
            )

        # Flag dangerous combination: retry on a non-idempotent write without protection
        if retry_on_fail and is_write_side_effect_node(node) and not _has_idempotency_hint(node):
            findings.append(
                Finding(
                    check_id="RTY-003",
                    title=f"Retry enabled on write without visible idempotency: {name}",
                    severity=Severity.HIGH,
                    node_name=name,
                    description=(
                        f"Node '{name}' can create/update external state and has Retry On Fail enabled. "
                        "If the first attempt actually succeeded but the response timed out, a retry "
                        "could produce a duplicate record, email, or charge; verify destination behavior."
                    ),
                    evidence="retryOnFail=true on a side-effect node with no clear idempotency key visible in parameters.",
                    recommendation=(
                        "Either: (1) disable Retry On Fail and handle failures via an error branch + "
                        "dead-letter, or (2) pass an Idempotency-Key / unique business key and check "
                        "for prior processing before the write. Stripe, many CRMs, and good HTTP APIs "
                        "support idempotency keys."
                    ),
                    effort_minutes=25,
                    tags=["retries", "duplicates", "idempotency"],
                )
            )

    return findings


def _has_idempotency_hint(node: dict) -> bool:
    """Very lightweight heuristic — looks for common parameter names."""
    params = str(node.get("parameters") or {}).lower()
    hints = (
        "idempotency",
        "idempotent",
        "unique_key",
        "dedupe",
        "deduplicate",
        "already_exists",
        "upsert",
        "if not exists",
    )
    return any(h in params for h in hints)