"""FAKE bank + ledger CSVs (100 bank rows) with known ground truth. Run: python tools/make_bank_data.py"""
import csv, random, os
from datetime import date, timedelta
random.seed(7)
OUT=os.path.join(os.path.dirname(__file__),"..","03-bank-reconciliation")
V=[("ADOBE *CREATIVE CLD","Adobe Creative Cloud subscription",-54.99),("AMZN MKTP US*2K4","Amazon office supplies",-86.40),
("SHELL OIL 5721","Shell fuel van",-62.15),("STARBUCKS 0412","Starbucks client coffee",-18.30),("ZOOM.US 888","Zoom annual plan",-149.90),
("GOOGLE *WORKSPACE","Google Workspace users",-72.00),("COMCAST BUSINESS","Comcast business internet",-129.99),("UBER TRIP","Uber client travel",-27.45),
("STAPLES 1180","Staples printer toner",-94.20),("SLACK T0123","Slack subscription",-87.50),("MAILCHIMP*","Mailchimp newsletter",-45.00),
("DELTA AIR 0062","Delta flight Boston",-318.00),("HILTON HOTELS","Hilton hotel stay",-241.60),("QUICKBOOKS ONLINE","QuickBooks Online fee",-65.00),
("WEWORK HOT DESK","WeWork hot desk rent",-450.00),("CHASE CARD PMT","Insurance premium Hiscox",-212.00),("DROPBOX*BUS","Dropbox business plan",-60.00),
("LINKEDIN ADS","LinkedIn ads campaign",-300.00),("TRADER JOES 88","Team lunch groceries",-76.80),("FEDEX 7788","FedEx shipping client docs",-38.25),
("CANVA PRO","Canva Pro subscription",-54.99),("NOTION LABS","Notion team plan",-48.00),("USPS PO 3321","USPS postage",-21.60),("VERIZON WIRELESS","Verizon mobile plans",-156.40),
("INVOICE 4471 PAYMENT","Client payment Acme Corp",1850.00),("INVOICE 4472 PAYMENT","Client payment Birch Dental",920.00),("INVOICE 4480 PAYMENT","Client payment Cobalt Studio",2400.00),
("INVOICE 4491 PAYMENT","Client payment Delta Realty",1275.50),("STRIPE PAYOUT","Stripe payout weekly",3120.75),("INVOICE 4503 PAYMENT","Client payment Evergreen Cafe",640.00)]
start=date(2026,3,1); bank=[]; ledger=[]; truth=[]
pool=[random.choice(V) for _ in range(88)]
# force 4 same-amount ambiguity pairs
pool[10]=("DROPBOX*BUS","Dropbox business plan",-60.00); pool[11]=("NOTION LABS","Notion team plan",-60.00)
pool[20]=("MAILCHIMP*","Mailchimp newsletter",-45.00); pool[21]=("SLACK T0123","Slack subscription",-45.00)
for k,(bd,lm,amt) in enumerate(pool):
    if k not in (10,11,20,21): amt=round(amt*random.uniform(0.85,1.15),2)
    d=start+timedelta(days=random.randint(0,29)); ld=d-timedelta(days=random.choice([0,0,1,2,3]))
    tail=f"{random.randint(100,999)}" if amt<0 else ""
    bank.append(dict(id=f"B{k+1:03d}",date=d.isoformat(),description=f"{bd} {tail}".strip(),amount=f"{amt:.2f}"))
    ledger.append(dict(id=f"L{k+1:03d}",date=ld.isoformat(),memo=lm,amount=f"{amt:.2f}"))
    truth.append((f"B{k+1:03d}",f"L{k+1:03d}"))
# 3 fee-difference exceptions: bank amount differs from ledger by a small fee
for k in (30,45,60):
    b=bank[k]; l=ledger[k]; fee=round(random.choice([2.5,3.0,1.5]),2)
    b["amount"]=f"{float(l['amount'])-fee:.2f}"
# 12 bank-only rows (fees, interest) -> 100 total
extras=[("MONTHLY SERVICE FEE",-15.00),("WIRE FEE",-25.00),("INTEREST PAID",3.42),("OVERDRAFT FEE",-35.00),("ATM WITHDRAWAL 7731",-200.00),
("CARD ANNUAL FEE",-95.00),("SERVICE CHARGE",-12.50),("INTEREST PAID",2.87),("WIRE FEE",-25.00),("ACH RETURN FEE",-6.00),("MONTHLY SERVICE FEE",-15.00),("CHECK ORDER",-28.40)]
for n,(desc,amt) in enumerate(extras):
    bank.append(dict(id=f"B{89+n:03d}",date=(start+timedelta(days=random.randint(0,29))).isoformat(),description=desc,amount=f"{amt:.2f}"))
# 7 ledger-only rows (outstanding items)
lo=[("Cheque 1042 Smith Plumbing",-380.00),("Cheque 1043 Garcia Print",-215.00),("Cash petty float",-100.00),("Client payment Foxglove (not yet cleared)",1500.00),
("Cheque 1044 City Parking",-64.00),("Accrual: courier",-42.10),("Client payment Granite Law (deposit in transit)",980.00)]
for n,(m,amt) in enumerate(lo):
    ledger.append(dict(id=f"L{89+n:03d}",date=(start+timedelta(days=random.randint(20,30))).isoformat(),memo=m,amount=f"{amt:.2f}"))
random.shuffle(bank); random.shuffle(ledger)
bank.sort(key=lambda r:r["date"]); ledger.sort(key=lambda r:r["date"])
def w(name,rows):
    with open(os.path.join(OUT,name),"w",newline="") as f:
        wr=csv.DictWriter(f,fieldnames=list(rows[0].keys()),lineterminator="\n"); wr.writeheader(); wr.writerows(rows)
w("bank.csv",bank); w("ledger.csv",ledger)
# ground truth: only pairs whose amounts agree are expected to auto-match (fee-difference pairs are intended exceptions)
fee_ids={bank_row["id"] for bank_row in bank if any(bank_row["id"]==t[0] and abs(float(bank_row["amount"])-float(next(l for l in ledger if l["id"]==t[1])["amount"]))>0.005 for t in truth)}
with open(os.path.join(OUT,"ground_truth.csv"),"w",newline="") as f:
    wr=csv.writer(f,lineterminator="\n"); wr.writerow(["bank_id","ledger_id","expected"])
    for b,l in truth: wr.writerow([b,l,"exception" if b in fee_ids else "match"])
print(len(bank),"bank rows;",len(ledger),"ledger rows;",len(fee_ids),"intended exceptions")
