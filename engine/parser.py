"""
Parse and normalize n8n workflow JSON exports.
Handles both modern (connections as dict) and older formats.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any


def load_workflow(source: str | Path | dict) -> dict:
    """Load a workflow from path or already-parsed dict."""
    if isinstance(source, dict):
        return source
    path = Path(source)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Workflow root must be a JSON object")
    return data


def normalize(workflow: dict) -> dict:
    """
    Return a normalized view used by all checks.
    Keys:
      - name, id, active, settings
      - nodes: list of node dicts (with guaranteed 'name', 'type', 'parameters', 'settings')
      - connections: dict[node_name] -> connection structure
      - node_by_name: quick lookup
    """
    if not isinstance(workflow, dict) or not isinstance(workflow.get("nodes"), list):
        raise ValueError("Expected n8n workflow object with a nodes array")
    nodes = workflow["nodes"]
    connections = workflow.get("connections", {})
    if not isinstance(connections, dict):
        raise ValueError("connections must be an object")
    names = set()
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("name"), str) or not node["name"] or not isinstance(node.get("type"), str) or not node["type"]:
            raise ValueError("Each node must have a nonempty string name and type")
        if node["name"] in names:
            raise ValueError("Duplicate node name")
        names.add(node["name"])
        if not isinstance(node.get("parameters", {}), dict) or not isinstance(node.get("settings", {}), dict):
            raise ValueError("Node parameters and settings must be objects")
    if not isinstance(workflow.get("settings", {}), dict):
        raise ValueError("Workflow settings must be an object")
    for source, outputs in connections.items():
        if source not in names or not isinstance(outputs, dict):
            raise ValueError("Unknown connection source or invalid outputs")
        for branches in outputs.values():
            if not isinstance(branches, list):
                raise ValueError("Connection branches must be arrays")
            for branch in branches:
                if branch is None: continue
                if not isinstance(branch, list): raise ValueError("Connection branch must be an array")
                for link in branch:
                    if not isinstance(link, dict) or link.get("node") not in names:
                        raise ValueError("Connection target is invalid or missing")

    # Ensure every node has a stable name and basic settings dict
    normalized_nodes = []
    for n in nodes:
        node = dict(n)  # shallow copy
        if "name" not in node:
            node["name"] = node.get("id", "unnamed")
        # n8n stores many operational flags at the top level of the node
        # (retryOnFail, maxTries, waitBetweenTries, onError, continueOnFail, etc.)
        # We also surface a convenient .get("settings", {}) for future compatibility.
        if "settings" not in node:
            node["settings"] = {}
        normalized_nodes.append(node)

    node_by_name = {n["name"]: n for n in normalized_nodes}

    return {
        "name": workflow.get("name") or workflow.get("id") or "Unnamed Workflow",
        "id": workflow.get("id"),
        "active": workflow.get("active", False),
        "settings": workflow.get("settings") or {},
        "nodes": normalized_nodes,
        "connections": connections,
        "node_by_name": node_by_name,
        "raw": workflow,
    }


def get_node_setting(node: dict, key: str, default: Any = None) -> Any:
    """
    Read a setting that may live at the top level of the node object
    (current n8n style) or under node['settings'].
    """
    if key in node:
        return node[key]
    return node.get("settings", {}).get(key, default)


def is_trigger_node(node: dict) -> bool:
    t = (node.get("type") or "").lower()
    return any(
        x in t
        for x in (
            "trigger",
            "webhook",
            "cron",
            "schedule",
            "manual",
            "form",
            "chat",
            "emailreadimap",
            "gmailtrigger",
        )
    )


def is_http_or_api_node(node: dict) -> bool:
    t = (node.get("type") or "").lower()
    name = (node.get("name") or "").lower()
    return any(
        x in t or x in name
        for x in (
            "httprequest",
            "http request",
            "webhook",
            "api",
            "rest",
            "graphql",
            "openai",
            "anthropic",
            "llm",
            "ai",
        )
    )


def is_write_side_effect_node(node: dict) -> bool:
    """Nodes that create/update external state (risk of duplicates on retry)."""
    t = (node.get("type") or "").lower()
    name = (node.get("name") or "").lower()
    keywords = (
        "create",
        "insert",
        "update",
        "upsert",
        "send",
        "email",
        "slack",
        "discord",
        "twilio",
        "stripe",
        "shopify",
        "airtable",
        "notion",
        "google sheets",
        "sheets",
        "crm",
        "hubspot",
        "pipedrive",
        "mailchimp",
        "resend",
        "sendgrid",
        "post",
        "put",
        "patch",
    )
    return any(k in t or k in name for k in keywords)


def has_error_output_connected(node_name: str, connections: dict) -> bool:
    """Rough check whether the node has an error/continue branch wired."""
    conn = connections.get(node_name) or {}
    # Modern n8n: connections[node] = {"main": [[{...}], [{...}]]}
    # Error output is often index 1 when "Continue (using error output)" is used.
    main = conn.get("main") or []
    return len(main) > 1 and bool(main[1])