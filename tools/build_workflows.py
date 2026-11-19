"""Writes importable n8n workflow JSON for all 7 demo projects.
Run: python tools/build_workflows.py   (from repo root)
After import: attach your own credentials (Google, OpenAI/Anthropic, Gmail) and set the Config values.
"""
import json, os, glob, uuid

ROOT = os.path.join(os.path.dirname(__file__), "..")
def rd(p): return open(os.path.join(ROOT, p), encoding="utf-8").read()

class WF:
    def __init__(self, name):
        self.name, self.nodes, self.conn = name, [], {}
    def add(self, name, type_, params=None, pos=(0, 0), v=1, extra=None):
        n = {"id": str(uuid.uuid4()), "name": name, "type": type_, "typeVersion": v,
             "position": list(pos), "parameters": params or {}}
        if extra: n.update(extra)
        self.nodes.append(n); return name
    def link(self, a, b, out=0):
        self.conn.setdefault(a, {"main": []})
        m = self.conn[a]["main"]
        while len(m) <= out: m.append([])
        m[out].append({"node": b, "type": "main", "index": 0})
    def chain(self, *names):
        for a, b in zip(names, names[1:]): self.link(a, b)
    def note(self, text, pos):
        self.add("Note " + str(len(self.nodes)), "n8n-nodes-base.stickyNote", {"content": text, "height": 140, "width": 360}, pos, 1)
    def save(self, path):
        data = {"name": self.name, "nodes": self.nodes, "connections": self.conn, "active": False,
                "settings": {"executionOrder": "v1"}, "pinData": {}, "meta": {"templateCredsSetupCompleted": False}}
        with open(os.path.join(ROOT, path), "w", encoding="utf-8") as f: json.dump(data, f, indent=2)

def code(w, name, js, pos, each=False):
    p = {"jsCode": js}
    if each: p["mode"] = "runOnceForEachItem"
    return w.add(name, "n8n-nodes-base.code", p, pos, 2)

def llm(w, name, pos):
    """OpenAI chat completions via HTTP. To use Claude instead, swap URL/headers (see README)."""
    return w.add(name, "n8n-nodes-base.httpRequest", {
        "method": "POST", "url": "https://api.openai.com/v1/chat/completions",
        "authentication": "predefinedCredentialType", "nodeCredentialType": "openAiApi",
        "sendBody": True, "specifyBody": "json", "jsonBody": "={{ JSON.stringify($json.body) }}"}, pos, 4.2)

def sheets(w, name, op, sheet, pos, extra=None):
    p = {"operation": op, "documentId": {"__rl": True, "mode": "url", "value": "PASTE_GOOGLE_SHEET_URL"},
         "sheetName": {"__rl": True, "mode": "name", "value": sheet}}
    if op == "append": p["columns"] = {"mappingMode": "autoMapInputData", "value": {}}
    if extra: p.update(extra)
    return w.add(name, "n8n-nodes-base.googleSheets", p, pos, 4.5)

def gmail_draft(w, name, to_expr, subj_expr, msg_expr, pos):
    return w.add(name, "n8n-nodes-base.gmail", {"resource": "draft", "operation": "create",
        "subject": subj_expr, "message": msg_expr, "options": {"sendTo": to_expr}}, pos, 2.1)

# ------------------------------------------------------------------ 1. Invoice ingestion
CATS = ["Software & Subscriptions", "Office Supplies", "Travel", "Meals & Entertainment", "Utilities", "Professional Fees",
        "Marketing & Advertising", "Rent", "Insurance", "Telecoms", "Equipment", "Bank Charges", "Other"]
INV_PROMPT = rd("01-invoice-ingestion/prompt.md") if os.path.exists(os.path.join(ROOT, "01-invoice-ingestion/prompt.md")) else ""
w = WF("01 - Invoice ingestion and auto-categorization (DEMO)")
t = w.add("Drive Trigger: new invoice PDF", "n8n-nodes-base.googleDriveTrigger", {
    "event": "fileCreated", "triggerOn": "specificFolder",
    "folderToWatch": {"__rl": True, "mode": "url", "value": "PASTE_DRIVE_FOLDER_URL"},
    "pollTimes": {"item": [{"mode": "everyMinute"}]}}, (0, 0), 1)
d = w.add("Download PDF", "n8n-nodes-base.googleDrive", {"operation": "download", "fileId": {"__rl": True, "mode": "id", "value": "={{ $json.id }}"}}, (220, 0), 3)
x = w.add("Extract text from PDF", "n8n-nodes-base.extractFromFile", {"operation": "pdf"}, (440, 0), 1)
b = code(w, "Build LLM request", """const text = $json.text || '';
const prompt = %s;
return { json: {
  fileName: $('Drive Trigger: new invoice PDF').item.json.name,
  fileUrl: $('Drive Trigger: new invoice PDF').item.json.webViewLink || '',
  body: { model: 'gpt-4o-mini', temperature: 0, response_format: { type: 'json_object' },
    messages: [ { role: 'system', content: prompt }, { role: 'user', content: text.slice(0, 12000) } ] } } };""" % json.dumps(INV_PROMPT), (660, 0), True)
l = llm(w, "LLM: extract + categorize", (880, 0))
p = code(w, "Parse + validate", """const meta = $('Build LLM request').item.json;
let r; try { r = JSON.parse($json.choices[0].message.content); } catch (e) { r = null; }
const flags = [];
if (!r) { flags.push('unparseable model output'); r = {}; }
const n = v => (v === null || v === undefined || v === '') ? null : Number(v);
const sub = n(r.subtotal), tax = n(r.tax), tot = n(r.total);
if (sub !== null && tax !== null && tot !== null && Math.abs(sub + tax - tot) > 0.02) flags.push('subtotal + tax != total');
if (tot === null) flags.push('missing total');
if (!r.vendor) flags.push('missing vendor');
if (!r.date) flags.push('missing date');
const conf = Number(r.category_confidence || 0);
if (conf < 0.8) flags.push('low category confidence');
return { json: { file: meta.fileName, link: meta.fileUrl, vendor: r.vendor || '', invoice_number: r.invoice_number || '',
  date: r.date || '', currency: r.currency || '', subtotal: sub, tax_label: r.tax_label || '', tax, total: tot,
  category: r.category || '', category_confidence: conf, reasoning: r.category_reasoning || '',
  needs_review: flags.length > 0 ? 'YES' : 'no', review_reasons: flags.join('; '), processed_at: new Date().toISOString() } };""", (1100, 0), True)
i = w.add("Needs review?", "n8n-nodes-base.if", {"conditions": {"options": {"caseSensitive": True, "typeValidation": "strict"},
    "combinator": "and", "conditions": [{"id": "c1", "leftValue": "={{ $json.needs_review }}", "rightValue": "YES",
    "operator": {"type": "string", "operation": "equals"}}]}}, (1320, 0), 2)
s1 = sheets(w, "Append: Needs Review", "append", "Needs Review", (1560, -100))
s2 = sheets(w, "Append: Processed", "append", "Processed", (1560, 100))
w.add("All rows (audit log)", "n8n-nodes-base.googleSheets", {"operation": "append", "documentId": {"__rl": True, "mode": "url", "value": "PASTE_GOOGLE_SHEET_URL"},
      "sheetName": {"__rl": True, "mode": "name", "value": "All"}, "columns": {"mappingMode": "autoMapInputData", "value": {}}}, (1560, 300), 4.5)
w.chain(t, d, x, b, l, p, i); w.link(i, s1, 0); w.link(i, s2, 1); w.link(p, "All rows (audit log)")
w.note("DEMO BUILD on synthetic invoices. Create a Sheet with tabs: Processed, Needs Review, All. Columns = field names in 'Parse + validate'. Swap model/URL in the LLM node to use Claude (see README).", (0, 200))
w.save("01-invoice-ingestion/workflow.json")

# ------------------------------------------------------------------ 2. Overdue invoice chaser
w = WF("02 - Overdue invoice chaser (DEMO, drafts only)")
t = w.add("Daily 9am", "n8n-nodes-base.scheduleTrigger", {"rule": {"interval": [{"field": "cronExpression", "expression": "0 9 * * *"}]}}, (0, 0), 1.2)
r = sheets(w, "Read invoices", "getAll", "Invoices", (220, 0))
c = code(w, "Decide tier + write email", """const today = new Date(); today.setHours(0,0,0,0);
const OWNER = 'Meridian Bookkeeping & Tax';
const T = {
 US: {
  1: { s: 'Friendly reminder: invoice {no} was due {due}', b: 'Hi {client},\\n\\nA quick reminder that invoice {no} for {amt} was due on {due}. If you have already paid, thank you, and please ignore this note.\\n\\nThanks,\\n' + OWNER },
  2: { s: 'Follow-up: invoice {no} is {days} days past due', b: 'Hi {client},\\n\\nInvoice {no} for {amt} is now {days} days past due. Could you let me know when we can expect payment, or reply if there is a problem with the invoice?\\n\\nThank you,\\n' + OWNER },
  3: { s: 'Final notice: invoice {no} ({amt})', b: 'Hello {client},\\n\\nThis is a final notice for invoice {no} for {amt}, now {days} days overdue. Please arrange payment within 7 days to avoid a pause on non-essential work under our fee policy.\\n\\nRegards,\\n' + OWNER } },
 UK: {
  1: { s: 'Gentle reminder: invoice {no} fell due on {due}', b: 'Dear {client},\\n\\nJust a gentle reminder that invoice {no} for {amt} fell due on {due}. If payment is already on its way, please disregard this message and thank you.\\n\\nKind regards,\\n' + OWNER },
  2: { s: 'Invoice {no} is now {days} days overdue', b: 'Dear {client},\\n\\nOur records show invoice {no} for {amt} is {days} days overdue. We would be grateful if you could confirm a payment date, or let us know if anything needs correcting.\\n\\nKind regards,\\n' + OWNER },
  3: { s: 'Final reminder: invoice {no} ({amt})', b: 'Dear {client},\\n\\nThis is our final reminder regarding invoice {no} for {amt}, now {days} days overdue. Please arrange payment within 7 days; otherwise we may need to pause non-essential work in line with our fee policy.\\n\\nYours sincerely,\\n' + OWNER } } };
const sym = { USD: '$', GBP: '\\u00a3' };
const out = [];
for (const it of $input.all()) {
  const r = it.json;
  if (String(r.status).toLowerCase() === 'paid') continue;
  const due = new Date(r.due_date); due.setHours(0,0,0,0);
  const days = Math.floor((today - due) / 86400000);
  const tier = days >= 30 ? 3 : days >= 14 ? 2 : days >= 1 ? 1 : 0;
  const last = Number(r.last_tier_sent || 0);
  if (tier === 0 || tier <= last) continue;
  const reg = String(r.region).toUpperCase() === 'UK' ? 'UK' : 'US';
  const fill = s => s.replace(/{no}/g, r.invoice_no).replace(/{client}/g, r.client).replace(/{due}/g, r.due_date)
    .replace(/{days}/g, days).replace(/{amt}/g, (sym[r.currency] || '') + Number(r.amount).toFixed(2));
  out.push({ json: { invoice_no: r.invoice_no, to: r.email, tier, days_overdue: days,
    subject: fill(T[reg][tier].s), message: fill(T[reg][tier].b) } });
}
return out;""", (440, 0))
g = gmail_draft(w, "Gmail: create DRAFT", "={{ $json.to }}", "={{ $json.subject }}", "={{ $json.message }}", (660, 0))
u = sheets(w, "Mark tier sent", "update", "Invoices", (880, 0), {"columns": {"mappingMode": "defineBelow", "value": {
    "invoice_no": "={{ $('Decide tier + write email').item.json.invoice_no }}", "last_tier_sent": "={{ $('Decide tier + write email').item.json.tier }}"},
    "matchingColumns": ["invoice_no"], "schema": []}})
w.chain(t, r, c, g, u)
t2 = w.add("Monday 8am weekly summary", "n8n-nodes-base.scheduleTrigger", {"rule": {"interval": [{"field": "cronExpression", "expression": "0 8 * * 1"}]}}, (0, 300), 1.2)
r2 = sheets(w, "Read invoices (summary)", "getAll", "Invoices", (220, 300))
c2 = code(w, "Build weekly summary", """const today = new Date(); today.setHours(0,0,0,0);
let n = 0, tot = { USD: 0, GBP: 0 }; const lines = [];
for (const it of $input.all()) { const r = it.json; if (String(r.status).toLowerCase() === 'paid') continue;
  const d = Math.floor((today - new Date(r.due_date)) / 86400000); if (d < 1) continue; n++; tot[r.currency] = (tot[r.currency] || 0) + Number(r.amount);
  lines.push(`${r.invoice_no} | ${r.client} | ${r.currency} ${Number(r.amount).toFixed(2)} | ${d} days overdue | tier sent: ${r.last_tier_sent}`); }
const msg = `Weekly receivables summary\\n\\nOverdue invoices: ${n}\\nOutstanding overdue: USD ${(tot.USD||0).toFixed(2)} / GBP ${(tot.GBP||0).toFixed(2)}\\n\\n` + lines.join('\\n');
return [{ json: { subject: 'Weekly overdue invoice summary', message: msg } }];""", (440, 300))
g2 = gmail_draft(w, "Gmail: summary DRAFT to owner", "OWNER_EMAIL@example.com", "={{ $json.subject }}", "={{ $json.message }}", (660, 300))
w.chain(t2, r2, c2, g2)
w.note("Drafts only. To go live later, change the Gmail node to resource=message, operation=send. Sheet tab 'Invoices' columns: see invoices.csv.", (0, 500))
w.save("02-overdue-invoice-chaser/workflow.json")

# ------------------------------------------------------------------ 3. Bank reconciliation
MATCHER = rd("03-bank-reconciliation/matcher.js").replace("if(typeof module!=='undefined')module.exports={reconcile,sim};", "")
w = WF("03 - Bank reconciliation helper (DEMO)")
f = w.add("Upload form (bank + ledger CSV)", "n8n-nodes-base.formTrigger", {"formTitle": "Bank reconciliation (demo)",
    "formDescription": "Upload a bank CSV (id,date,description,amount) and a ledger CSV (id,date,memo,amount).",
    "formFields": {"values": [{"fieldLabel": "bank_csv", "fieldType": "file", "multipleFiles": False, "acceptFileTypes": ".csv", "requiredField": True},
                              {"fieldLabel": "ledger_csv", "fieldType": "file", "multipleFiles": False, "acceptFileTypes": ".csv", "requiredField": True}]}}, (0, 0), 2.1)
eb = w.add("Read bank CSV", "n8n-nodes-base.extractFromFile", {"operation": "csv", "binaryPropertyName": "bank_csv"}, (240, -80), 1)
el = w.add("Read ledger CSV", "n8n-nodes-base.extractFromFile", {"operation": "csv", "binaryPropertyName": "ledger_csv"}, (240, 80), 1)
mg = w.add("Merge", "n8n-nodes-base.merge", {"mode": "combine", "combineBy": "combineByPosition", "options": {"includeUnpaired": True}}, (460, 0), 3)
m = code(w, "Fuzzy match", MATCHER + """
const bank = $('Read bank CSV').all().map(i => i.json);
const ledger = $('Read ledger CSV').all().map(i => i.json);
const r = reconcile(bank, ledger, { window: 3 });
const matchRate = ((r.matched.length / bank.length) * 100).toFixed(1);
return [{ json: { summary: { bank_rows: bank.length, ledger_rows: ledger.length, matched: r.matched.length, match_rate_pct: matchRate,
  review_flags: r.matched.filter(x => x.confidence === 'review').length, unmatched_bank: r.unmatchedBank.length, unmatched_ledger: r.unmatchedLedger.length },
  matched: r.matched, exceptions: r.exceptions, unmatchedLedger: r.unmatchedLedger } }];""", (680, 0))
bq = code(w, "Build LLM request (exceptions)", """const ex = $json.exceptions.filter(e => e.candidates.length > 0);
const sys = 'You are a bookkeeping assistant. For each unmatched bank transaction you get up to 3 candidate ledger entries. Pick the most likely match or say none. Explain in one short sentence (e.g. bank fee deducted, timing difference). Respond ONLY with JSON: {"suggestions":[{"bank_id":"","ledger_id":"" or null,"confidence":0-1,"reason":""}]}. Never invent ids.';
return { json: { data: $json, body: { model: 'gpt-4o-mini', temperature: 0, response_format: { type: 'json_object' },
  messages: [ { role: 'system', content: sys }, { role: 'user', content: JSON.stringify(ex) } ] } } };""", (900, 0), True)
ll = llm(w, "LLM: suggest matches for exceptions", (1120, 0))
rp = code(w, "Assemble report", """const d = $('Build LLM request (exceptions)').item.json.data;
let sug = []; try { sug = JSON.parse($json.choices[0].message.content).suggestions || []; } catch (e) {}
const rows = [];
d.matched.forEach(x => rows.push({ status: 'MATCHED (' + x.confidence + ')', bank_id: x.bank.id, bank_date: x.bank.date, bank_desc: x.bank.description, amount: x.bank.amount, ledger_id: x.ledger.id, note: '' }));
d.exceptions.forEach(e => { const s = sug.find(z => z.bank_id === e.bank.id); rows.push({ status: 'UNMATCHED BANK', bank_id: e.bank.id, bank_date: e.bank.date, bank_desc: e.bank.description, amount: e.bank.amount,
  ledger_id: s && s.ledger_id ? s.ledger_id : '', note: s ? ('AI suggestion (' + s.confidence + '): ' + s.reason) : 'no candidate' }); });
d.unmatchedLedger.forEach(l => rows.push({ status: 'UNMATCHED LEDGER', bank_id: '', bank_date: l.date, bank_desc: '', amount: l.amount, ledger_id: l.id, note: l.memo }));
return rows.map(r => ({ json: r })).concat([{ json: { status: 'SUMMARY', note: JSON.stringify(d.summary) } }]);""", (1340, 0))
o = sheets(w, "Write report to Sheet", "append", "Reconciliation Report", (1560, 0))
w.link(f, eb); w.link(f, el); w.link(eb, mg, 0); w.link(el, mg, 1); w.chain(mg, m, bq, ll, rp, o)
w.note("Matching is deterministic code (amount + date window + description). The LLM only suggests matches for EXCEPTIONS; a human approves them.", (0, 220))
w.save("03-bank-reconciliation/workflow.json")

# ------------------------------------------------------------------ 4. Client onboarding
w = WF("04 - Client onboarding workflow (DEMO)")
f = w.add("Intake form", "n8n-nodes-base.formTrigger", {"formTitle": "New client intake (demo)", "formFields": {"values": [
    {"fieldLabel": "Client name", "requiredField": True}, {"fieldLabel": "Contact email", "fieldType": "email", "requiredField": True},
    {"fieldLabel": "Region", "fieldType": "dropdown", "fieldOptions": {"values": [{"option": "US"}, {"option": "UK"}]}, "requiredField": True},
    {"fieldLabel": "Entity type", "fieldType": "dropdown", "fieldOptions": {"values": [{"option": "Sole proprietor"}, {"option": "LLC / Ltd"}, {"option": "Corporation"}]}},
    {"fieldLabel": "Services", "fieldType": "dropdown", "fieldOptions": {"values": [{"option": "Monthly bookkeeping"}, {"option": "Bookkeeping + payroll"}, {"option": "Year-end only"}]}},
    {"fieldLabel": "Monthly fee", "fieldType": "number"}, {"fieldLabel": "Start date", "fieldType": "date"}]}}, (0, 0), 2.1)
n = code(w, "Normalize intake", """const j = $json;
const slug = String(j['Client name']).replace(/[^A-Za-z0-9 ]/g, '').trim().replace(/ +/g, '_');
const uk = j['Region'] === 'UK';
const checklist = [ 'Bank statements (last 3 months, all accounts)', 'Credit card statements', 'Sales invoices issued this year', 'Purchase invoices and receipts',
  uk ? 'VAT registration details and last VAT return' : 'State sales tax registration details (if any)', 'Payroll summary (if applicable)', 'Prior year filed accounts / tax return',
  'Loan agreements and statements', 'Authority form signed (to deal with tax authority on your behalf)' ];
return { json: { client: j['Client name'], slug, email: j['Contact email'], region: j['Region'], entity: j['Entity type'], services: j['Services'],
  fee: j['Monthly fee'], start: j['Start date'], currency: uk ? 'GBP' : 'USD', checklist,
  checklist_text: checklist.map((c, i) => (i + 1) + '. ' + c).join('\\n') } };""", (220, 0), True)
d1 = w.add("Drive: create client folder", "n8n-nodes-base.googleDrive", {"resource": "folder", "operation": "create", "name": "={{ $json.slug }}",
    "driveId": {"__rl": True, "mode": "list", "value": "My Drive"}, "folderId": {"__rl": True, "mode": "url", "value": "PASTE_CLIENTS_ROOT_FOLDER_URL"}}, (440, 0), 3)
sub = code(w, "List subfolders", """const names = ['01 Engagement', '02 Source Documents', '03 Bookkeeping', '04 Tax and Filings', '05 Correspondence'];
return names.map(n => ({ json: { name: n, parent: $json.id } }));""", (660, 0))
d2 = w.add("Drive: create subfolders", "n8n-nodes-base.googleDrive", {"resource": "folder", "operation": "create", "name": "={{ $json.name }}",
    "driveId": {"__rl": True, "mode": "list", "value": "My Drive"}, "folderId": {"__rl": True, "mode": "id", "value": "={{ $json.parent }}"}}, (880, 0), 3)
cp = w.add("Drive: copy engagement letter template", "n8n-nodes-base.googleDrive", {"resource": "file", "operation": "copy",
    "fileId": {"__rl": True, "mode": "url", "value": "PASTE_ENGAGEMENT_LETTER_TEMPLATE_URL"},
    "name": "={{ 'Engagement Letter - ' + $('Normalize intake').item.json.client }}", "sameFolder": False,
    "driveId": {"__rl": True, "mode": "list", "value": "My Drive"}, "folderId": {"__rl": True, "mode": "id", "value": "={{ $('Drive: create client folder').first().json.id }}"}}, (1100, 0), 3)
doc = w.add("Docs: fill placeholders", "n8n-nodes-base.googleDocs", {"operation": "update", "documentURL": "={{ $json.id }}", "actionsUi": {"actionFields": [
    {"action": "replaceAll", "text": "{{CLIENT_NAME}}", "replaceText": "={{ $('Normalize intake').item.json.client }}"},
    {"action": "replaceAll", "text": "{{SERVICES}}", "replaceText": "={{ $('Normalize intake').item.json.services }}"},
    {"action": "replaceAll", "text": "{{FEE}}", "replaceText": "={{ $('Normalize intake').item.json.currency + ' ' + $('Normalize intake').item.json.fee }}"},
    {"action": "replaceAll", "text": "{{START_DATE}}", "replaceText": "={{ $('Normalize intake').item.json.start }}"},
    {"action": "replaceAll", "text": "{{DATE}}", "replaceText": "={{ $now.toFormat('yyyy-LL-dd') }}"}]}}, (1320, 0), 2)
cl = gmail_draft(w, "Gmail: document checklist DRAFT", "={{ $('Normalize intake').item.json.email }}", "={{ 'Documents we need to get started - ' + $('Normalize intake').item.json.client }}",
    "={{ 'Hi ' + $('Normalize intake').item.json.client + ',\\n\\nTo get started please send the following through the secure client portal:\\n\\n' + $('Normalize intake').item.json.checklist_text + '\\n\\nScanned or phone-photo copies are fine if every figure is readable.\\n\\nThank you!' }}", (1540, -100))
wl = gmail_draft(w, "Gmail: welcome email DRAFT", "={{ $('Normalize intake').item.json.email }}", "={{ 'Welcome to Meridian, ' + $('Normalize intake').item.json.client }}",
    "={{ 'Hi,\\n\\nWelcome aboard! Your engagement letter is in your secure folder for review and e-signature. Next: a 30-minute kickoff call within 5 working days.\\n\\nSpeak soon.' }}", (1540, 100))
tk = sheets(w, "Sheet: onboarding tasks", "append", "Onboarding Tasks", (1760, 0))
tk_prep = code(w, "Build task rows", """const c = $('Normalize intake').item.json;
const steps = ['Review signed engagement letter', 'Confirm bank feeds / software access', 'Receive first documents', 'Kickoff call', 'First month bookkeeping start'];
return steps.map((s, i) => ({ json: { client: c.client, task: s, owner: 'Bookkeeper', status: 'Open', due_in_days: [2, 3, 5, 5, 10][i], created: new Date().toISOString() } }));""", (1760, 150))
w.chain(f, n, d1, sub, d2); w.link(d1, cp); w.chain(cp, doc); w.link(doc, cl); w.link(doc, wl); w.link(doc, tk_prep); w.link(tk_prep, tk)
w.note("Create a Google Doc template using the placeholders in engagement_letter_template.md. 'Copy template' runs once per client (connect from the folder node).", (0, 220))
w.save("04-client-onboarding/workflow.json")

# ------------------------------------------------------------------ 5. SOP / FAQ assistant
docs = [{"name": os.path.basename(p), "text": open(p, encoding="utf-8").read()} for p in sorted(glob.glob(os.path.join(ROOT, "05-sop-faq-assistant/firm_docs/*.md")))]
RET = rd("05-sop-faq-assistant/retriever.js").replace("if(typeof module!=='undefined')module.exports={retrieve};", "")
SYS = rd("05-sop-faq-assistant/system_prompt.md") if os.path.exists(os.path.join(ROOT, "05-sop-faq-assistant/system_prompt.md")) else ""
w = WF("05 - SOP and FAQ assistant (DEMO)")
wh = w.add("Webhook: question", "n8n-nodes-base.webhook", {"httpMethod": "POST", "path": "firm-faq", "responseMode": "responseNode"}, (0, 0), 2)
rt = code(w, "Retrieve + build request", RET + """
const DOCS = %s;
const q = String($json.body.question || '').slice(0, 1000);
const top = retrieve(q, DOCS, 3);
const scope = DOCS.find(d => d.name.startsWith('08_'));
const ctx = [...top, ...(top.find(t => t.name === scope.name) ? [] : [scope])];
const SYSTEM = %s;
const sources = ctx.map(c => c.name);
const content = ctx.map(c => '### ' + c.name + '\\n' + c.text).join('\\n\\n');
return { json: { question: q, sources, body: { model: 'gpt-4o-mini', temperature: 0, response_format: { type: 'json_object' },
  messages: [ { role: 'system', content: SYSTEM }, { role: 'user', content: 'FIRM DOCUMENTS:\\n' + content + '\\n\\nCLIENT QUESTION:\\n' + q } ] } } };""" % (json.dumps(docs), json.dumps(SYS)), (220, 0), True)
ll = llm(w, "LLM: answer from docs only", (440, 0))
pr = code(w, "Parse answer", """const m = $('Retrieve + build request').item.json;
let r; try { r = JSON.parse($json.choices[0].message.content); } catch (e) { r = { status: 'escalate', answer: '' }; }
let status = ['answered', 'escalate', 'refuse'].includes(r.status) ? r.status : 'escalate';
let answer = r.answer || '';
if (status === 'escalate') answer = "I'll pass this to the team. They will reply by email within 1 working day.";
if (status === 'refuse') answer = r.answer || "I can't give tax or investment advice here. I can book you a paid consultation with a qualified accountant.";
return { json: { question: m.question, status, answer, sources: status === 'answered' ? (r.source_docs || m.sources) : [], logged_at: new Date().toISOString() } };""", (660, 0), True)
ifn = w.add("Needs a human?", "n8n-nodes-base.if", {"conditions": {"options": {"caseSensitive": True, "typeValidation": "strict"}, "combinator": "and",
    "conditions": [{"id": "c1", "leftValue": "={{ $json.status }}", "rightValue": "answered", "operator": {"type": "string", "operation": "notEquals"}}]}}, (880, 0), 2)
gm = w.add("Gmail: notify team", "n8n-nodes-base.gmail", {"resource": "message", "operation": "send", "sendTo": "TEAM_EMAIL@example.com",
    "subject": "={{ 'FAQ bot escalation (' + $json.status + ')' }}", "message": "={{ 'Question: ' + $json.question + '\\nBot status: ' + $json.status }}", "options": {}}, (1100, -80), 2.1)
lg = sheets(w, "Log Q&A", "append", "FAQ Log", (1100, 120))
rs = w.add("Respond", "n8n-nodes-base.respondToWebhook", {"respondWith": "json", "responseBody": "={{ JSON.stringify({ status: $('Parse answer').item.json.status, answer: $('Parse answer').item.json.answer, sources: $('Parse answer').item.json.sources }) }}"}, (1320, 0), 1.1)
w.chain(wh, rt, ll, pr, ifn); w.link(ifn, gm, 0); w.link(ifn, lg, 1); w.link(gm, lg); w.link(lg, rs)
w.note("POST {\"question\": \"...\"} to the webhook. Bot answers ONLY from firm_docs; escalates when unsure; refuses tax/investment advice.", (0, 220))
w.save("05-sop-faq-assistant/workflow.json")

# ------------------------------------------------------------------ 6. Monthly report
w = WF("06 - Monthly report generator (DEMO)")
t = w.add("Manual or monthly (1st, 8am)", "n8n-nodes-base.scheduleTrigger", {"rule": {"interval": [{"field": "cronExpression", "expression": "0 8 1 * *"}]}}, (0, 0), 1.2)
r = sheets(w, "Read monthly figures", "getAll", "Figures", (220, 0))
cc = code(w, "Calculate", """const rows = $input.all().map(i => i.json).sort((a, b) => a.month.localeCompare(b.month));
const N = x => Number(x || 0);
const calc = rows.map(r => { const opex = N(r.payroll) + N(r.rent) + N(r.marketing) + N(r.software) + N(r.other);
  const gp = N(r.revenue) - N(r.cost_of_sales); const np = gp - opex;
  return { month: r.month, revenue: N(r.revenue), gross_profit: gp, expenses: opex + N(r.cost_of_sales), net_profit: np, margin: N(r.revenue) ? np / N(r.revenue) : 0, marketing: N(r.marketing), payroll: N(r.payroll) }; });
const cur = calc[calc.length - 1], prev = calc[calc.length - 2];
const pct = (a, b) => b ? ((a - b) / b) * 100 : null;
const mom = { revenue_pct: pct(cur.revenue, prev.revenue), expenses_pct: pct(cur.expenses, prev.expenses), net_profit_pct: pct(cur.net_profit, prev.net_profit), margin_pts: (cur.margin - prev.margin) * 100 };
return [{ json: { client: 'Sample Client Ltd (fictional)', cur, prev, mom, history: calc } }];""", (440, 0))
bq = code(w, "Build LLM request", """const d = $json;
const sys = 'You write a plain-English monthly summary for a small business owner who is not an accountant. 120-160 words. Use ONLY the numbers provided; never invent causes. Mention revenue, profit, margin, the biggest month-on-month change, and one question the owner should ask their bookkeeper. No jargon. No tax or investment advice.';
return { json: { data: d, body: { model: 'gpt-4o-mini', temperature: 0.2, messages: [ { role: 'system', content: sys }, { role: 'user', content: JSON.stringify({ cur: d.cur, prev: d.prev, mom: d.mom }) } ] } } };""", (660, 0), True)
ll = llm(w, "LLM: plain-English summary", (880, 0))
h = code(w, "Build HTML report", """const d = $('Build LLM request').item.json.data; const summary = $json.choices[0].message.content;
const f = n => n.toLocaleString('en-US', { maximumFractionDigits: 0 });
const pc = v => v === null ? 'n/a' : (v >= 0 ? '+' : '') + v.toFixed(1) + '%';
const bars = d.history.slice(-6).map(h => `<tr><td>${h.month}</td><td>${f(h.revenue)}</td><td>${f(h.net_profit)}</td><td>${(h.margin * 100).toFixed(1)}%</td></tr>`).join('');
const html = `<html><body style="font-family:Helvetica,Arial;margin:40px;color:#222"><h1>Monthly Report: ${d.cur.month}</h1><p><i>${d.client}. Demo report on fictional data.</i></p>
<table border="0" cellpadding="8"><tr><td><b>Revenue</b><br>${f(d.cur.revenue)}<br>${pc(d.mom.revenue_pct)} vs prior month</td><td><b>Expenses</b><br>${f(d.cur.expenses)}<br>${pc(d.mom.expenses_pct)}</td><td><b>Net profit</b><br>${f(d.cur.net_profit)}<br>${pc(d.mom.net_profit_pct)}</td><td><b>Margin</b><br>${(d.cur.margin * 100).toFixed(1)}%<br>${d.mom.margin_pts.toFixed(1)} pts</td></tr></table>
<h2>In plain English</h2><p>${summary.replace(/\\n/g, '<br>')}</p><h2>Last 6 months</h2><table border="1" cellpadding="6" style="border-collapse:collapse"><tr><th>Month</th><th>Revenue</th><th>Net profit</th><th>Margin</th></tr>${bars}</table></body></html>`;
return { json: { month: d.cur.month, html }, binary: { files: { data: Buffer.from(html).toString('base64'), mimeType: 'text/html', fileName: 'index.html' } } };""", (1100, 0), True)
pdf = w.add("HTML to PDF (Gotenberg)", "n8n-nodes-base.httpRequest", {"method": "POST", "url": "http://localhost:3000/forms/chromium/convert/html",
    "sendBody": True, "contentType": "multipart-form-data", "bodyParameters": {"parameters": [{"parameterType": "formBinaryData", "name": "files", "inputDataFieldName": "files"}]},
    "options": {"response": {"response": {"responseFormat": "file", "outputPropertyName": "report"}}}}, (1320, 0), 4.2)
dr = w.add("Gmail: email DRAFT with PDF", "n8n-nodes-base.gmail", {"resource": "draft", "operation": "create", "subject": "={{ 'Your monthly report - ' + $('Build HTML report').item.json.month }}",
    "message": "Hi,\\n\\nYour monthly report is attached with a short plain-English summary. Happy to walk you through it on a call.\\n\\nKind regards", "options": {"sendTo": "CLIENT_EMAIL@example.com", "attachmentsUi": {"attachmentsBinary": [{"property": "report"}]}}}, (1540, 0), 2.1)
w.chain(t, r, cc, bq, ll, h, pdf, dr)
w.note("PDF step uses Gotenberg: docker run -p 3000:3000 gotenberg/gotenberg:8  (free, self-hosted). Alternative: any HTML-to-PDF API.", (0, 220))
w.save("06-monthly-report-generator/workflow.json")

# ------------------------------------------------------------------ 7. AUDIT lead magnet
w = WF("07 - AUDIT lead magnet system (DEMO)")
f = w.add("AUDIT readiness form", "n8n-nodes-base.formTrigger", {"formTitle": "Automation readiness AUDIT", "formDescription": "7 quick questions. Get a personalised checklist by email.",
    "formFields": {"values": [{"fieldLabel": "Name", "requiredField": True}, {"fieldLabel": "Email", "fieldType": "email", "requiredField": True}, {"fieldLabel": "Firm name"}] + [
        {"fieldLabel": q, "fieldType": "dropdown", "requiredField": True, "fieldOptions": {"values": [{"option": "Never"}, {"option": "Sometimes"}, {"option": "Always"}]}} for q in [
            "Invoices and receipts are entered by hand", "Bank reconciliation takes more than a day each month", "Overdue invoices are chased manually",
            "New client onboarding uses a manual checklist", "Clients ask the same questions repeatedly", "Monthly reports are built by hand in spreadsheets",
            "Documents are collected over email chains"]]}}, (0, 0), 2.1)
sc = code(w, "Score + personalise", rd("07-audit-lead-magnet/scoring.js"), (220, 0), True)
htmlb = code(w, "Build checklist HTML", """const s = $json;
const items = s.actions.map(a => `<li><b>${a.area}</b>: ${a.advice}</li>`).join('');
const html = `<html><body style="font-family:Helvetica,Arial;margin:40px;color:#222"><h1>Your Automation AUDIT</h1><p>Hi ${s.name}${s.firm ? ' (' + s.firm + ')' : ''},</p>
<p><b>Automation opportunity score: ${s.score}/100 (${s.tier})</b></p><p>${s.headline}</p><h2>Your priority checklist</h2><ol>${items}</ol><p style="color:#666">This checklist is general guidance from a demo system, not financial or tax advice.</p></body></html>`;
return { json: { ...s, html }, binary: { files: { data: Buffer.from(html).toString('base64'), mimeType: 'text/html', fileName: 'index.html' } } };""", (440, 0), True)
pdf = w.add("HTML to PDF (Gotenberg)", "n8n-nodes-base.httpRequest", {"method": "POST", "url": "http://localhost:3000/forms/chromium/convert/html", "sendBody": True,
    "contentType": "multipart-form-data", "bodyParameters": {"parameters": [{"parameterType": "formBinaryData", "name": "files", "inputDataFieldName": "files"}]},
    "options": {"response": {"response": {"responseFormat": "file", "outputPropertyName": "checklist"}}}}, (660, 0), 4.2)
em = w.add("Gmail: send checklist", "n8n-nodes-base.gmail", {"resource": "message", "operation": "send", "sendTo": "={{ $('Score + personalise').item.json.email }}",
    "subject": "Your personalised automation checklist", "message": "={{ 'Hi ' + $('Score + personalise').item.json.name + ',\\n\\nThanks for taking the AUDIT. Your personalised checklist is attached. Reply to this email if you want to talk through it.\\n\\nMoiz' }}",
    "options": {"attachmentsUi": {"attachmentsBinary": [{"property": "checklist"}]}}}, (880, -120), 2.1)
nt = w.add("Gmail: notify me", "n8n-nodes-base.gmail", {"resource": "message", "operation": "send", "sendTo": "YOUR_EMAIL@example.com",
    "subject": "={{ 'New AUDIT lead: ' + $('Score + personalise').item.json.name + ' (' + $('Score + personalise').item.json.score + ')' }}",
    "message": "={{ JSON.stringify($('Score + personalise').item.json.actions.map(a => a.area)) }}", "options": {}}, (880, 0), 2.1)
ls = w.add("Sheet: lead log", "n8n-nodes-base.googleSheets", {"operation": "append", "documentId": {"__rl": True, "mode": "url", "value": "PASTE_GOOGLE_SHEET_URL"},
    "sheetName": {"__rl": True, "mode": "name", "value": "Leads"}, "columns": {"mappingMode": "defineBelow", "value": {
        "date": "={{ $now.toISO() }}", "name": "={{ $('Score + personalise').item.json.name }}", "email": "={{ $('Score + personalise').item.json.email }}",
        "firm": "={{ $('Score + personalise').item.json.firm }}", "score": "={{ $('Score + personalise').item.json.score }}", "tier": "={{ $('Score + personalise').item.json.tier }}",
        "top_area": "={{ $('Score + personalise').item.json.actions[0].area }}", "followup_stage": "0"}, "schema": []}}, (880, 120), 4.5)
wt = w.add("Wait 2 days", "n8n-nodes-base.wait", {"resume": "timeInterval", "amount": 2, "unit": "days"}, (1100, 120), 1.1)
f1 = gmail_draft(w, "Follow-up 1 DRAFT", "={{ $('Score + personalise').item.json.email }}", "Did the checklist help?",
    "={{ 'Hi ' + $('Score + personalise').item.json.name + ',\\n\\nQuick check-in: your biggest opportunity was ' + $('Score + personalise').item.json.actions[0].area + '. Want a 15-minute walkthrough of how that could be automated?\\n\\nMoiz' }}", (1320, 120))
wt2 = w.add("Wait 3 more days", "n8n-nodes-base.wait", {"resume": "timeInterval", "amount": 3, "unit": "days"}, (1540, 120), 1.1)
f2 = gmail_draft(w, "Follow-up 2 DRAFT", "={{ $('Score + personalise').item.json.email }}", "A short demo you might like",
    "={{ 'Hi ' + $('Score + personalise').item.json.name + ',\\n\\nI built a short demo video of an automation like this (on fictional data). Reply DEMO and I will send the link.\\n\\nMoiz' }}", (1760, 120))
w.chain(f, sc, htmlb, pdf); w.link(pdf, em); w.link(pdf, nt); w.link(pdf, ls); w.chain(ls, wt, f1, wt2, f2)
w.note("Replace 'Moiz' signature/emails. Follow-ups are DRAFTS so you approve each. Demo build: not a production lead system.", (0, 220))
w.save("07-audit-lead-magnet/workflow.json")
print("workflows written")
