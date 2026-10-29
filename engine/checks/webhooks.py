"""Webhook-specific security and reliability checks."""

from __future__ import annotations
from .base import Finding, Severity
from ..parser import get_node_setting


def check_webhooks(wf: dict) -> list[Finding]:
    findings: list[Finding] = []

    for node in wf["nodes"]:
        ntype = (node.get("type") or "").lower()
        if "webhook" not in ntype:
            continue

        name = node["name"]
        params = node.get("parameters") or {}

        # Authentication
        auth = (
            params.get("authentication")
            or params.get("auth")
            or get_node_setting(node, "authentication")
        )
        # A downstream or external control may still protect this endpoint.
        if str(auth).lower() in ("", "none", "null", "undefined"):
            findings.append(
                Finding(
                    check_id="WH-001",
                    title=f"Webhook has no configured node authentication: {name}",
                    severity=Severity.CRITICAL,
                    node_name=name,
                    description=(
                        f"Webhook node '{name}' appears to accept requests without authentication. "
                        "External authentication or signature checks may exist and must be verified."
                    ),
                    evidence=f"parameters.authentication = {auth!r}",
                    recommendation=(
                        "Enable authentication on the Webhook node (Header Auth, Basic Auth, "
                        "or a custom header check). Prefer a shared secret validated in an "
                        "IF node immediately after the webhook. Rotate the secret periodically."
                    ),
                    effort_minutes=10,
                    tags=["security", "webhook"],
                )
            )

        # responseMode / response handling (less critical but useful)
        response_mode = params.get("responseMode") or params.get("response_mode")
        if response_mode in (None, "onReceived"):
            # Fine for many use cases; only note if the workflow looks long-running
            pass

    return findings