#!/usr/bin/env python3
"""
One-command demonstration of the AI Automation Audit & Rescue engine.

Runs the audit against the intentionally defective sample workflow and
prints a clear summary showing that the three required failure modes
(failed retry, duplicate risk, missing validation) are detected.
"""

from __future__ import annotations
import sys
from pathlib import Path

# Allow running from the project root without installation
sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine.runner import run_audit
from engine.reporter import write_reports, render_markdown
from engine import __version__


def main() -> int:
    sample = Path(__file__).parent / "sample_workflows" / "defective_lead_ingest.json"
    if not sample.exists():
        print(f"Sample workflow missing: {sample}", file=sys.stderr)
        return 1

    print("=" * 64)
    print("AI Automation Audit & Rescue — Demonstration")
    print(f"Engine v{__version__}")
    print("=" * 64)
    print()
    print("Target : Intentionally defective n8n workflow")
    print("        (failed retry + duplicate risk + missing validation)")
    print()

    wf, findings = run_audit(sample)
    meta = {"engine_version": __version__}
    out_dir = Path(__file__).parent / "reports"
    md_path, json_path = write_reports(wf["name"], findings, out_dir, meta)

    # Highlight the three required demo findings
    required_signals = {
        "retry": False,
        "duplicate": False,
        "validation": False,
        "unauthenticated_webhook": False,
        "no_error_workflow": False,
    }

    for f in findings:
        cid = f.check_id
        title = f.title.lower()
        if cid.startswith("RTY-") or "retry" in title:
            required_signals["retry"] = True
        if cid.startswith("DUP-") or "duplicate" in title or "idempoten" in title:
            required_signals["duplicate"] = True
        if cid.startswith("VAL-") or "validation" in title:
            required_signals["validation"] = True
        if cid == "WH-001":
            required_signals["unauthenticated_webhook"] = True
        if cid == "ERR-001":
            required_signals["no_error_workflow"] = True

    print("Detection checklist (must all be True for a valid demo):")
    print(f"  [ {'x' if required_signals['retry'] else ' '} ] Failed / missing retry configuration")
    print(f"  [ {'x' if required_signals['duplicate'] else ' '} ] Duplicate execution risk")
    print(f"  [ {'x' if required_signals['validation'] else ' '} ] Missing input validation")
    print(f"  [ {'x' if required_signals['unauthenticated_webhook'] else ' '} ] Unauthenticated webhook (bonus)")
    print(f"  [ {'x' if required_signals['no_error_workflow'] else ' '} ] No Error Workflow assigned (bonus)")
    print()
    print(f"Total findings : {len(findings)}")
    print(f"Report (MD)    : {md_path}")
    print(f"Report (JSON)  : {json_path}")
    print()
    print("-" * 64)
    print(render_markdown(wf["name"], findings, meta))
    print("-" * 64)

    all_core = all(
        [
            required_signals["retry"],
            required_signals["duplicate"],
            required_signals["validation"],
        ]
    )
    if all_core:
        print("\nDEMO PASSED — all three required failure modes were identified.")
        return 0
    else:
        print("\nDEMO INCOMPLETE — one or more required signals were not raised.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())