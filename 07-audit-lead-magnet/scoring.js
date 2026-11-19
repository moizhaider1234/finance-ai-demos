const j = $json;
const Q = [
  ['Invoices and receipts are entered by hand', 'Invoice entry', 'Automate invoice capture: extract vendor, date, tax and total from PDFs and auto-suggest categories, with a human review queue for low-confidence items.'],
  ['Bank reconciliation takes more than a day each month', 'Bank reconciliation', 'Auto-match bank lines to ledger entries on amount, date window and description; review only the exceptions.'],
  ['Overdue invoices are chased manually', 'Receivables chasing', 'Set tiered reminders (friendly, firm, final) that stop when an invoice is marked paid, plus a weekly summary to the owner.'],
  ['New client onboarding uses a manual checklist', 'Client onboarding', 'One intake form that creates folders, fills the engagement letter, emails the document checklist and creates tasks.'],
  ['Clients ask the same questions repeatedly', 'Client FAQs', 'A document-grounded assistant that answers routine questions, hands unclear ones to your team and declines to give tax advice.'],
  ['Monthly reports are built by hand in spreadsheets', 'Monthly reporting', 'Generate the calculations, a plain-English summary and a PDF from your monthly figures, then draft the client email.'],
  ['Documents are collected over email chains', 'Document collection', 'Send a standard checklist per client type and track what has arrived in one shared sheet.']
];
const val = { 'Never': 0, 'Sometimes': 1, 'Always': 2 };
const rated = Q.map(([q, area, advice]) => ({ area, advice, v: val[j[q]] ?? 0 }));
const raw = rated.reduce((a, r) => a + r.v, 0);
const score = Math.round((raw / (Q.length * 2)) * 100);
const tier = score >= 60 ? 'High opportunity' : score >= 30 ? 'Medium opportunity' : 'Low opportunity';
const headline = score >= 60 ? 'A lot of your week is likely going on repeatable manual work. Start with your top two items below.'
  : score >= 30 ? 'You have a few clear automation wins. Start with the first item below.'
  : 'Your processes are already fairly streamlined. The items below are optional polish.';
const actions = rated.filter(r => r.v > 0).sort((a, b) => b.v - a.v);
if (actions.length === 0) actions.push({ area: 'Review', advice: 'Re-run this AUDIT in three months or when your client count grows.', v: 0 });
return { json: { name: j['Name'], email: j['Email'], firm: j['Firm name'] || '', score, tier, headline, actions: actions.map(({ area, advice }) => ({ area, advice })) } };
