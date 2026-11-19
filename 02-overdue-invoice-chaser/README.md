# 02 - Overdue invoice chaser (DEMO BUILD, drafts only)
**Problem:** chasing late payers is repetitive and awkward, so it gets skipped.
**How it works:** daily 9am run reads the `Invoices` tab. Paid rows are skipped. Overdue days decide the tier: 1 to 13 days = friendly reminder, 14 to 29 = firmer follow-up, 30+ = final notice. A tier is only sent once (tracked in `last_tier_sent`). US and UK variants differ in tone and wording and use $ or GBP symbols. Gmail creates DRAFTS only. A Monday 8am flow drafts a weekly summary to the owner.
**Test data:** `invoices.csv` (12 fictional invoices, 2 paid, 2 not yet due). Import it as the `Invoices` tab.
**Verified offline:** with the demo date 2026-11-19 the logic drafts 8 emails (tiers 1,1,2,3,3,3,3,1) and skips the paid and not-yet-due rows (`node tools/check_code_nodes.js`).
**To go live later:** change Gmail resource to message/send, and add your signature and payment link.
## What I measured
Reminders drafted per run: [X]. Manual time per week [Y] min vs automated review time [Z] min.
