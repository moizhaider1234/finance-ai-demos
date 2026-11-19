"""POST the 20 test questions to your n8n webhook and score status vs expected. python run_faq_eval.py https://YOUR-N8N/webhook/firm-faq"""
import csv, json, sys, os, urllib.request
url = sys.argv[1]; here = os.path.dirname(__file__); ok = 0; rows = list(csv.DictReader(open(os.path.join(here, "test_questions.csv"))))
for r in rows:
    req = urllib.request.Request(url, data=json.dumps({"question": r["question"]}).encode(), headers={"Content-Type": "application/json"})
    got = json.load(urllib.request.urlopen(req))["status"]; want = {"answer": "answered", "refuse": "refuse", "escalate": "escalate"}[r["expected"]]
    ok += (got == want); print(("PASS " if got == want else "FAIL ") + f"#{r['id']} expected={want} got={got} | {r['question']}")
print(f"\n{ok}/{len(rows)} correct (answered / refused / escalated as expected)")
