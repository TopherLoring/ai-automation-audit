"""Detect patterns that commonly produce duplicate executions or side-effects."""

from __future__ import annotations
from .base import Finding, Severity
from ..parser import get_node_setting, is_write_side_effect_node, is_trigger_node


def check_duplicate_risk(wf: dict) -> list[Finding]:
    findings: list[Finding] = []
    nodes = wf["nodes"]
    connections = wf["connections"]

    # 1. Webhook triggers without any obvious deduplication / unique check downstream
    webhook_nodes = [
        n
        for n in nodes
        if "webhook" in (n.get("type") or "").lower()
        or (is_trigger_node(n) and "webhook" in (n.get("name") or "").lower())
    ]

    for wh in webhook_nodes:
        name = wh["name"]
        # Look for a downstream IF / Code / Set that mentions unique / id / already processed
        findings.append(
            Finding(
                check_id="DUP-001",
                title=f"Verify webhook deduplication: {name}",
                severity=Severity.HIGH,
                node_name=name,
                description=(
                    f"Webhook '{name}' can be delivered more than once by the source system "
                    "or replay. The export alone does not establish whether an effective "
                    "idempotency control exists; duplicate effects are not demonstrated."
                ),
                evidence="Webhook node present; durable deduplication has not been verified.",
                recommendation=(
                    "Immediately after the webhook: extract a stable event/message ID. "
                    "Query a small dedupe store (Data Table, Postgres, Redis, or even a Sheet) "
                    "for that ID. Only continue if it is new; otherwise exit early. "
                    "Store the ID with a TTL after successful processing."
                ),
                effort_minutes=30,
                tags=["duplicates", "webhook", "idempotency"],
            )
        )

    # 2. Write nodes that sit directly after a trigger with no intermediate guard
    for node in nodes:
        if not is_write_side_effect_node(node):
            continue
        name = node["name"]
        # Heuristic: if the node is only one hop from a trigger and has no guard, flag it
        if _is_near_trigger(name, nodes, connections) and not _has_idempotency_hint(node):
            findings.append(
                Finding(
                    check_id="DUP-002",
                    title=f"Write node close to trigger with no idempotency: {name}",
                    severity=Severity.MEDIUM,
                    node_name=name,
                    description=(
                        f"'{name}' performs a create/update/send action and sits close to a trigger. "
                        "Without an explicit uniqueness check, any re-delivery or partial retry will "
                        "potentially duplicate the side-effect; confirm destination behavior."
                    ),
                    evidence="Write node appears early in the graph and parameters contain no clear unique-key / upsert / exists check.",
                    recommendation=(
                        "Add a lookup step before the write. Prefer native upserts where the "
                        "destination supports them. Pass an idempotency key on HTTP calls."
                    ),
                    effort_minutes=20,
                    tags=["duplicates", "idempotency"],
                )
            )

    return findings


def _has_downstream_guard(start_name: str, nodes: list, connections: dict) -> bool:
    """Very light BFS looking for validation / unique-key language in the next few nodes."""
    visited = set()
    queue = [start_name]
    keywords = (
        "unique",
        "idempoten",
        "already",
        "exists",
        "dedupe",
        "deduplicate",
        "event_id",
        "message_id",
        "if",
        "filter",
        "switch",
    )

    depth = 0
    while queue and depth < 4:
        next_queue = []
        for curr in queue:
            if curr in visited:
                continue
            visited.add(curr)
            conn = connections.get(curr) or {}
            main = conn.get("main") or []
            for branch in main:
                for link in branch or []:
                    target = link.get("node")
                    if not target:
                        continue
                    target_node = next((n for n in nodes if n["name"] == target), None)
                    if not target_node:
                        continue
                    blob = (
                        (target_node.get("name") or "")
                        + " "
                        + str(target_node.get("parameters") or {})
                    ).lower()
                    if any(k in blob for k in keywords):
                        return True
                    next_queue.append(target)
        queue = next_queue
        depth += 1
    return False


def _is_near_trigger(node_name: str, nodes: list, connections: dict) -> bool:
    """True if any trigger can reach this node in ≤ 2 hops."""
    triggers = [n["name"] for n in nodes if is_trigger_node(n)]
    for t in triggers:
        if _reachable_in(t, node_name, connections, max_hops=2):
            return True
    return False


def _reachable_in(start: str, target: str, connections: dict, max_hops: int) -> bool:
    visited = set()
    queue = [(start, 0)]
    while queue:
        curr, dist = queue.pop(0)
        if curr == target:
            return True
        if dist >= max_hops or curr in visited:
            continue
        visited.add(curr)
        conn = connections.get(curr) or {}
        for branch in conn.get("main") or []:
            for link in branch or []:
                nxt = link.get("node")
                if nxt:
                    queue.append((nxt, dist + 1))
    return False


def _has_idempotency_hint(node: dict) -> bool:
    params = str(node.get("parameters") or {}).lower()
    hints = (
        "idempotency",
        "idempotent",
        "unique_key",
        "dedupe",
        "upsert",
        "if not exists",
        "already_exists",
    )
    return any(h in params for h in hints)