# Finance AI Automation Demos (n8n) - Moiz Haider
Seven demo builds for accounting firms and bookkeepers (US and UK). **All data is synthetic. These are demo builds, not client results.**

| # | Project | Folder | Offline-verified here |
|---|---|---|---|
| 1 | Invoice ingestion + categorization | `01-invoice-ingestion` | 20 PDFs extract cleanly; evaluator self-tested |
| 2 | Overdue invoice chaser | `02-overdue-invoice-chaser` | tier logic: 8 drafts from 12 invoices |
| 3 | Bank reconciliation helper | `03-bank-reconciliation` | 85/100 matched, 0 wrong, 3/3 exceptions surfaced |
| 4 | Client onboarding | `04-client-onboarding` | workflow structure only |
| 5 | SOP/FAQ assistant | `05-sop-faq-assistant` | retriever 14/16 |
| 6 | Monthly report generator | `06-monthly-report-generator` | calculations + sample PDF |
| 7 | AUDIT lead magnet | `07-audit-lead-magnet` | scoring + sample PDF |

## Honest status
- **Import these:** `n8n-tested/*.json` are exports of the workflows that were built and run in a real n8n cloud instance (see `RESULTS.md`). Credentials, Sheet/Drive/folder IDs and email addresses were removed: replace every `PASTE_...`, `YOUR_...` and `...@example.com` value and attach your own credentials.
- **AI step:** the tested workflows use n8n's built-in Google Gemini node (works on n8n AI credits, no API key). Per-project READMEs written earlier still mention OpenAI via HTTP; the Gemini version is what was tested.
- **Not tested live:** HTML to PDF (needs a Gotenberg server n8n can reach), real form/webhook submissions, the multi-day waits.
- Older per-project `workflow.json` files were removed because they were never run in n8n.

## Order
Import and test 1, then 2, 3, 5, then 4, 6, 7. Record timings in `timing_log.csv`, a 1 to 2 minute screen recording each, screenshot the canvas.

## Tools
`tools/` regenerates the sample invoices (`make_invoices.py`) and bank data (`make_bank_data.py`).
