"""Workflow-level settings hygiene."""

from __future__ import annotations
from .base import Finding, Severity


def check_workflow_settings(wf: dict) -> list[Finding]:
    findings: list[Finding] = []
    settings = wf["settings"] or {}

    # Save failed executions (important for debugging)
    save_error = settings.get("saveDataErrorExecution") or settings.get(
        "save_data_error_execution"
    )
    if save_error in (None, "none", False):
        findings.append(
            Finding(
                check_id="SET-001",
                title="Failed execution data may not be saved",
                severity=Severity.MEDIUM,
                node_name=None,
                description=(
                    "Workflow settings do not clearly indicate that data for failed executions "
                    "is retained. Without the input/output of the failing run, root-cause analysis "
                    "becomes guesswork."
                ),
                evidence=f"saveDataErrorExecution = {save_error!r}",
                recommendation=(
                    "In Workflow Settings set 'Save failed production executions' (or equivalent) "
                    "to at least a few days. Pair with an Error Workflow so you are notified."
                ),
                effort_minutes=5,
                tags=["settings", "observability"],
            )
        )

    # Timezone / execution timeout (informational)
    if not settings.get("timezone") and not settings.get("timezoneId"):
        findings.append(
            Finding(
                check_id="SET-002",
                title="No explicit timezone set",
                severity=Severity.LOW,
                node_name=None,
                description="Workflow has no explicit timezone. Cron schedules and date logic may surprise you.",
                evidence="settings.timezone is empty",
                recommendation="Set a timezone that matches the business (e.g. America/Chicago).",
                effort_minutes=2,
                tags=["settings"],
            )
        )

    return findings