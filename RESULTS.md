# Test results (live n8n runs, 22 Nov 2026)

All data is synthetic. These are demo builds, not client results.

## Project 1: invoice extraction accuracy (20 test invoices, live model)
Run through the same extraction prompt and validation logic as workflow 01, using n8n's built-in Gemini node (gemini-3-flash-preview) on n8n AI credits.

| Field | Correct |
|---|---|
| vendor | 20/20 |
| date | 20/20 |
| subtotal | 20/20 |
| tax | 20/20 |
| total | 20/20 |
| category | 20/20 |

- Fully correct invoices: **20/20**. Flagged for human review: **0**. Not flagged but wrong: **0**.
- Run time for all 20 invoices: about 36 seconds, end to end.
- A separate single-invoice run went through the full live path (Google Drive download, PDF text extraction, model, Google Sheets write) and matched the answer key on every field.

### Read this before quoting the numbers
- The 20 invoices are clean, computer-generated PDFs in 5 layouts. The answer key was written by me too, and the categories are fairly obvious from vendor names (an electric company is Utilities).
- 20/20 on this set shows the pipeline works. It does NOT show 100% accuracy on real invoices, which are messier (scans, odd layouts, ambiguous vendors). Test on real, anonymised invoices before making any accuracy claim.
- Text for this test was taken directly from the PDFs (verified identical to n8n's PDF extractor on invoice 01), not re-extracted from Drive for all 20.
- Manual-versus-automated time is yours to measure; see `timing_log.csv`.

## Other workflows (live runs on fictional data)
| # | Workflow | What ran live |
|---|---|---|
| 2 | Overdue chaser | Read the Sheet, created 8 Gmail drafts (tiers 1,1,2,3,3,3,3,1; US and UK wording), updated tiers in the Sheet |
| 3 | Bank reconciliation | 6-row slice: 4 matched, 2 flagged for review, fee-short payment surfaced as an exception and the model suggested the correct ledger entry |
| 4 | Client onboarding | Created client folder and 5 subfolders, copied and filled the engagement letter, 2 Gmail drafts, 5 task rows |
| 5 | FAQ assistant | Live model: answered a fee question with the right source, refused a tax-advice question, escalated an out-of-scope one |
| 6 | Monthly report | Sheet read, maths checked by hand (net profit 6,591, margin 21.1%), model summary, HTML report built |
| 7 | AUDIT lead magnet | Scored a test lead 36/100, sent a notification email, logged the lead to the Sheet |

## Not tested live
- HTML to PDF conversion (projects 6 and 7 need a Gotenberg server reachable from n8n).
- Real form and webhook submissions, the 2 and 3 day waits, and the weekly summary email.
- The bank reconciliation matcher on all 100 transactions inside n8n. Offline, `03-bank-reconciliation/test_matcher.js` matched 85 of 100 with 0 wrong matches.

## Bugs found by live testing (now fixed in `n8n-tested/`)
- FAQ assistant: response parser misread the model output and wrongly escalated a correct answer.
- Monthly report: the model's summary was cut off mid-sentence until the output limit was raised.
- AUDIT lead magnet: the empty Leads tab saved a junk row instead of the lead; fixed by building the row explicitly.
