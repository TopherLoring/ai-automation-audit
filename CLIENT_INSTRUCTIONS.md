> **Historical draft:** Not approved for client use. See `SERVICE_CONTRACT.md` and `docs/BASELINE_AUDIT.md`.

# AI Automation Audit — Client Instructions

**What this is**  
A fixed-scope diagnostic of one existing automation workflow (n8n preferred; Make or Zapier also accepted). You receive a clear, prioritized list of problems that cause failures, duplicates, silent stops, or data issues — plus exact recommended fixes.

**Price range**  
$290 – $590 depending on workflow size and complexity.  
Quoted after a quick review of the export.

---

### What you need to send

1. **Workflow export (required)**  
   - n8n: Open the workflow → three-dot menu (⋯) → **Download**  
   - Make: Export the scenario as JSON/blueprint  
   - Zapier: Export the Zap (or provide screenshots + description if export is limited)

2. **One-sentence purpose**  
   What is this workflow supposed to do?  
   Example: “When a new lead submits the form, create a CRM contact and send a welcome email.”

3. **Known problems (optional but helpful)**  
   Any errors, missing records, duplicates, or manual workarounds you already see.

4. **Redaction**  
   Remove or replace real API keys, tokens, passwords, and personal customer data before sending. Credential *names* are fine; actual secrets are not needed.

---

### What you will receive

- Prioritized findings report (Markdown + PDF available)
- Severity rating for every issue (Critical / High / Medium / Low)
- Exact evidence from your workflow
- Concrete fix recommendations with estimated effort
- Optional separate quote for implementation of the repairs

---

### Process & timeline

| Step | What happens | Typical time |
|------|--------------|--------------|
| 1 | You send the export + purpose | — |
| 2 | Quick scope check & firm price confirmation | Same day |
| 3 | Audit runs + report written | 1–2 business days |
| 4 | Report delivered + short walkthrough (Loom or call) | Included |

Active diagnostic time is normally 1–3 hours.

---

### In scope

- Static analysis of the supplied workflow(s)
- Identification of missing error handling, weak/missing retries, duplicate risks, missing validation, unauthenticated webhooks, and related reliability issues
- Clear, actionable repair recommendations

### Out of scope (available as separate work)

- Full rebuilds or major redesigns
- Ongoing monitoring or support retainers
- Access to paid third-party platforms beyond what is required for the audit
- Security penetration testing or formal compliance certification

---

### How to get started

Reply with:

1. The workflow export file(s)  
2. The one-sentence purpose  
3. Any known problems (optional)

You will receive a firm price and estimated delivery window before any work begins.

---

*Questions? Just reply to this message.*  
*This is a diagnostic service only. Implementation of fixes is quoted separately.*