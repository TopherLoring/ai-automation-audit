#!/usr/bin/env python3
"""
CLI entrypoint for the Automation Audit engine.

Usage:
  python -m engine.runner path/to/workflow.json
  python -m engine.runner path/to/workflow.json --out reports/
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

from . import __version__
from .parser import load_workflow, normalize
from .checks import ALL_CHECKS
from .reporter import write_reports, render_markdown


def run_audit(source: str | Path | dict) -> tuple[dict, list]:
    raw = load_workflow(source)
    wf = normalize(raw)
    findings = []
    for check in ALL_CHECKS:
        findings.extend(check(wf))
    return wf, findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AI Automation Audit & Rescue — static analysis for n8n workflows"
    )
    parser.add_argument("workflow", help="Path to n8n workflow JSON export")
    parser.add_argument(
        "--out",
        default="reports",
        help="Output directory for Markdown + JSON reports (default: reports/)",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Also print the Markdown report to stdout",
    )
    args = parser.parse_args(argv)

    path = Path(args.workflow)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 1

    wf, findings = run_audit(path)
    meta = {"engine_version": __version__}
    md_path, json_path = write_reports(wf["name"], findings, args.out, meta)

    print(f"Workflow : {wf['name']}")
    print(f"Findings : {len(findings)}")
    print(f"Markdown : {md_path}")
    print(f"JSON     : {json_path}")

    if args.stdout:
        print("\n" + render_markdown(wf["name"], findings, meta))

    # Exit non-zero if any critical or high findings exist (useful in CI)
    has_blocking = any(f.severity.value in ("critical", "high") for f in findings)
    return 2 if has_blocking else 0


if __name__ == "__main__":
    sys.exit(main())