"""Detect missing or weak error handling."""

from __future__ import annotations
from .base import Finding, Severity
from ..parser import get_node_setting, is_http_or_api_node, is_write_side_effect_node


def check_error_handling(wf: dict) -> list[Finding]:
    findings: list[Finding] = []
    nodes = wf["nodes"]
    settings = wf["settings"]
    connections = wf["connections"]

    # 1. Workflow-level error workflow
    error_workflow = settings.get("errorWorkflow") or settings.get("error_workflow")
    if not error_workflow:
        findings.append(
            Finding(
                check_id="ERR-001",
                title="No Error Workflow assigned",
                severity=Severity.HIGH,
                node_name=None,
                description=(
                    "This workflow has no Error Workflow configured. "
                    "Notification and recovery may exist outside this export; verify them."
                ),
                evidence="Workflow settings → Error workflow is empty.",
                recommendation=(
                    "Create a shared Error Trigger workflow that posts to Slack/email/Telegram "
                    "with workflow name, failed node, and error message. Then assign it under "
                    "Workflow Settings → Error workflow on every production workflow."
                ),
                effort_minutes=20,
                tags=["error-handling", "alerting"],
            )
        )

    # 2. Per-node onError / continueOnFail analysis for critical nodes
    for node in nodes:
        name = node["name"]
        ntype = node.get("type") or ""
        if "errorTrigger" in ntype.lower() or "manual" in ntype.lower():
            continue

        on_error = get_node_setting(node, "onError") or get_node_setting(node, "on_error")
        continue_on_fail = get_node_setting(node, "continueOnFail") or get_node_setting(
            node, "continue_on_fail"
        )
        retry_on_fail = get_node_setting(node, "retryOnFail") or get_node_setting(
            node, "retry_on_fail"
        )

        is_critical = is_http_or_api_node(node) or is_write_side_effect_node(node)

        if is_critical and not on_error and not continue_on_fail and not retry_on_fail:
            findings.append(
                Finding(
                    check_id="ERR-002",
                    title=f"Critical node has no error strategy: {name}",
                    severity=Severity.HIGH,
                    node_name=name,
                    description=(
                        f"Node '{name}' performs an external call or write but has neither "
                        "Retry On Fail, Continue On Fail, nor a custom On Error path. "
                        "A single transient failure will stop the entire execution with no recovery."
                    ),
                    evidence=f"Node type={ntype}; retryOnFail={retry_on_fail}; onError={on_error}; continueOnFail={continue_on_fail}",
                    recommendation=(
                        "For flaky APIs: enable Retry On Fail (3 tries, 2000–3000 ms wait). "
                        "For non-idempotent writes: prefer Continue (using error output) and "
                        "route the error branch to a logging / dead-letter path. "
                        "Never leave critical nodes on the default 'Stop Workflow' with zero retries."
                    ),
                    effort_minutes=10,
                    tags=["error-handling", "critical-node"],
                )
            )

    return findings