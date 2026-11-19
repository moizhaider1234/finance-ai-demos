# 01 - Invoice ingestion and auto-categorization (DEMO BUILD)
**Problem:** bookkeepers retype supplier invoices and decide categories one by one.
**Tools:** n8n, Google Drive, Google Sheets, OpenAI API (swap for Claude), synthetic invoices.
**How it works:** PDF lands in a Drive folder -> text extracted -> LLM returns vendor, invoice no., date, currency, subtotal, tax, total, category + confidence -> code validates (subtotal + tax = total, required fields, confidence >= 0.8) -> clean rows go to `Processed`, anything doubtful goes to `Needs Review`. Every row is also kept in `All`.
**Test data:** 20 invented invoices, 5 layouts, 10 US (sales tax) and 10 UK (VAT), `sample_invoices/` + `ground_truth.csv` (regenerate with `python tools/make_invoices.py`).

## Set up (about 20 minutes)
1. Import `workflow.json` into n8n. Add Google Drive, Google Sheets and OpenAI credentials.
2. Make a Sheet with tabs `Processed`, `Needs Review`, `All` and header row: `file, link, vendor, invoice_number, date, currency, subtotal, tax_label, tax, total, category, category_confidence, reasoning, needs_review, review_reasons, processed_at`.
3. Paste the Sheet URL and Drive folder URL into the nodes marked PASTE_.
4. Drop the 20 PDFs into the folder, wait for the Sheet to fill.
5. Export the `All` tab as `results.csv`, run `python evaluate.py results.csv`.

## Using Claude instead of OpenAI
In the HTTP node: URL `https://api.anthropic.com/v1/messages`, headers `x-api-key` and `anthropic-version: 2023-06-01`, body `{model, max_tokens:1024, system, messages}`; read the answer from `content[0].text` in the Parse node.

## What I measured (fill in with YOUR numbers; see ../timing_log.csv)
- Manual: [X] minutes for 20 invoices. Automated: [Y] minutes including review queue.
- Field accuracy and category accuracy from `evaluate.py`: [paste]
- "Not flagged but wrong" count: [paste] (the number finance clients care about)
