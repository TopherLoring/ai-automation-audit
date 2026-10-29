"""Detect missing input validation before critical actions."""

from __future__ import annotations
from .base import Finding, Severity
from ..parser import is_write_side_effect_node, is_http_or_api_node, is_trigger_node


def check_missing_validation(wf: dict) -> list[Finding]:
    findings: list[Finding] = []
    nodes = wf["nodes"]
    connections = wf["connections"]

    # Look for write / HTTP nodes that have no preceding IF / Filter / Switch / Code validation
    for node in nodes:
        if not (is_write_side_effect_node(node) or is_http_or_api_node(node)):
            continue
        if is_trigger_node(node):
            continue

        name = node["name"]
        predecessors = _immediate_predecessors(name, connections)

        has_validation = False
        for pred_name in predecessors:
            pred = next((n for n in nodes if n["name"] == pred_name), None)
            if not pred:
                continue
            ptype = (pred.get("type") or "").lower()
            pname = (pred.get("name") or "").lower()
            if any(
                x in ptype or x in pname
                for x in ("if", "switch", "filter", "validate", "code", "function", "stopanderror")
            ):
                has_validation = True
                break

        # Also accept a Set node that clearly maps required fields (weak signal)
        if not has_validation and predecessors:
            # Still flag if the only predecessor is the trigger or another write
            only_weak = all(
                is_trigger_node(next((n for n in nodes if n["name"] == p), {}))
                or is_write_side_effect_node(next((n for n in nodes if n["name"] == p), {}))
                for p in predecessors
            )
            if only_weak:
                findings.append(
                    Finding(
                        check_id="VAL-001",
                        title=f"Missing validation before critical node: {name}",
                        severity=Severity.HIGH,
                        node_name=name,
                        description=(
                            f"Node '{name}' performs an external call or state change but has no "
                            "obvious IF / Switch / Filter / validation step immediately upstream. "
                            "Malformed or incomplete payloads will reach the action and either fail "
                            "or, worse, create bad records."
                        ),
                        evidence=f"Immediate predecessors: {predecessors or 'none (possible entry node)'}",
                        recommendation=(
                            "Insert an IF (or Switch) node that checks required fields are present "
                            "and well-formed (email contains @, id is not empty, amount > 0, etc.). "
                            "On the false branch use Stop and Error or route to a dead-letter path. "
                            "This single pattern eliminates a large class of silent data corruption."
                        ),
                        effort_minutes=15,
                        tags=["validation", "data-quality"],
                    )
                )

    return findings


def _immediate_predecessors(target: str, connections: dict) -> list[str]:
    preds = []
    for src, conn in connections.items():
        main = conn.get("main") or []
        for branch in main:
            for link in branch or []:
                if link.get("node") == target:
                    preds.append(src)
    return preds