"""Score the workflow against ground truth. Export your Sheet tab 'All' to results.csv, then: python evaluate.py results.csv
Reports field accuracy, category accuracy, and review-queue stats. Self-test: python evaluate.py --selftest"""
import csv, sys, os
here = os.path.dirname(__file__)
gt = {r["file"]: r for r in csv.DictReader(open(os.path.join(here, "ground_truth.csv")))}
def load(path): return {r["file"]: r for r in csv.DictReader(open(path))}
res = gt if "--selftest" in sys.argv else load(sys.argv[1])
n = len(gt); tot = {"vendor": 0, "date": 0, "total": 0, "tax": 0, "category": 0}; flagged = 0; correct_unflagged = 0; wrong_unflagged = 0
for f, g in gt.items():
    r = res.get(f)
    if not r: continue
    ok = {"vendor": r["vendor"].strip().lower() == g["vendor"].lower(), "date": r["date"][:10] == g["date"],
          "total": abs(float(r["total"] or 0) - float(g["total"])) < 0.015, "tax": abs(float(r["tax"] or 0) - float(g["tax"])) < 0.015,
          "category": r["category"].strip() == g["category"]}
    for k, v in ok.items(): tot[k] += v
    fl = str(r.get("needs_review", "no")).upper() == "YES"; flagged += fl
    if not fl: correct_unflagged += all(ok.values()); wrong_unflagged += (not all(ok.values()))
print(f"Invoices scored: {len([f for f in gt if f in res])}/{n}")
for k, v in tot.items(): print(f"  {k:9s}: {v}/{n} ({100*v/n:.0f}%)")
print(f"Flagged for human review: {flagged}/{n}")
print(f"Not flagged and fully correct: {correct_unflagged}; not flagged but WRONG (the number that matters): {wrong_unflagged}")
