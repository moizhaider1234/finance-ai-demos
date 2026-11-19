# 06 - Monthly report generator (DEMO BUILD)
**Problem:** month-end reports are rebuilt by hand in spreadsheets, then written up in plain English.
**How it works:** monthly trigger -> read `Figures` tab (`figures.csv`) -> code calculates gross profit, expenses, net profit, margin and month-on-month change -> LLM writes a 120-160 word summary using ONLY those numbers -> HTML -> PDF via Gotenberg (`docker run -p 3000:3000 gotenberg/gotenberg:8`) -> Gmail DRAFT to the client with the PDF attached.
**Sample output:** `sample_report.pdf` (made by `python generate_report.py`; the summary there is a fixed template, the LLM writes it in n8n).
**Accuracy note:** all numbers come from code, not the LLM. Have a human read each summary before sending.
## What I measured
Manual report: [X] min. Automated including proofreading: [Y] min.
