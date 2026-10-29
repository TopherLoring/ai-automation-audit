> **Work in progress:** Not ready for customer data or a paid pilot. See `docs/BASELINE_AUDIT.md` and `SERVICE_CONTRACT.md`. Existing sales materials contain unvalidated claims.

# AI Automation Audit & Rescue

Reusable static analysis engine + demonstration for the **#1 Quick-Revenue Opportunity**: diagnosing and documenting broken, unreliable, or unsafe n8n (and similar) automation workflows.

**Goal:** Produce a client-ready findings report in minutes from a workflow JSON export, with zero paid dependencies.

## What it solves for the buyer

Businesses running n8n / Make / Zapier workflows pay when:

- Integrations silently stop or produce duplicates
- Retries are missing or dangerous
- Webhooks accept unauthenticated traffic
- There is no error alerting
- Bad data reaches CRM / email / payment steps

This engine turns a workflow export into a prioritized, evidence-backed repair list that can be sold as a fixed-price audit ($290–$590 range) or used as the diagnostic step before an implementation quote.

## Quick start (demo)

```bash
cd automation-audit
python demo.py
```

This runs the engine against an intentionally defective sample workflow and prints a full Markdown report. The demo is designed to surface:

1. Missing / failed retry configuration  
2. Duplicate execution risk  
3. Missing input validation  

…plus several high-value bonus findings (unauthenticated webhook, no Error Workflow, etc.).

## Audit a real workflow

```bash
# From the project root
python -m engine.runner path/to/exported-workflow.json --out reports/ --stdout
```

Outputs:

- `reports/<workflow_name>_audit.md`  — client-ready Markdown report  
- `reports/<workflow_name>_audit.json` — machine-readable findings  

Exit codes:

- `0` — no Critical or High findings  
- `2` — Critical or High findings present (useful for CI / pre-merge gates)  
- `1` — usage / file error  

## Current checks (v1.0)

| ID prefix | Focus |
|-----------|--------|
| ERR-      | Missing Error Workflow, critical nodes with no error strategy |
| RTY-      | Missing or weak Retry On Fail; retries on non-idempotent writes |
| DUP-      | Webhook re-delivery risk, write nodes without uniqueness checks |
| VAL-      | Missing validation before external calls / state changes |
| WH-       | Unauthenticated webhooks |
| SET-      | Workflow settings hygiene (failed-execution retention, timezone) |

All checks are pure static analysis of the exported JSON. No live credentials or instance access required.

## Recommended commercial packaging

1. **Intake** — Client sends a redacted workflow JSON export (or limited view-only access).  
2. **Run** — Execute this engine + any manual review notes.  
3. **Deliver** — Markdown report + short Loom or call walkthrough of the top 3–5 fixes.  
4. **Upsell** — Separate fixed-price implementation of the recommended repairs.

Do **not** build a SaaS, client portal, or marketplace before at least one paid audit has closed.

## Project layout

```
automation-audit/
├── demo.py                          # One-command demonstration
├── engine/
│   ├── parser.py                    # Load + normalize n8n JSON
│   ├── runner.py                    # CLI
│   ├── reporter.py                  # Markdown + JSON output
│   └── checks/                      # Individual rule modules
├── sample_workflows/
│   └── defective_lead_ingest.json   # Intentionally broken demo
├── reports/                         # Generated output
└── requirements.txt
```

## Extending

Add a new file under `engine/checks/`, implement a function that accepts the normalized workflow dict and returns `list[Finding]`, then register it in `engine/checks/__init__.py`.

## Stack constraints (from opportunity brief)

- Python (stdlib + optional rich/jinja2/jsonschema)  
- No paid APIs  
- No mandatory cloud subscriptions  
- Local-first, works offline after the workflow JSON is obtained  

## License / usage

Built for direct commercial use on the AI Automation Audit & Rescue offer. Modify and rebrand freely for client work.