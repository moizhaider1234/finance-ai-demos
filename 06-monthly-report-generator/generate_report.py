"""Offline sample of the monthly report (same maths as the n8n 'Calculate' node). Summary here is a fixed template;
in the workflow an LLM writes it from the same numbers. Run: python generate_report.py -> sample_report.pdf"""
import csv, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
here = os.path.dirname(__file__)
rows = list(csv.DictReader(open(os.path.join(here, "figures.csv"))))
calc = []
for r in rows:
    f = {k: float(v) for k, v in r.items() if k != "month"}
    opex = f["payroll"] + f["rent"] + f["marketing"] + f["software"] + f["other"]
    gp = f["revenue"] - f["cost_of_sales"]; np_ = gp - opex
    calc.append(dict(month=r["month"], revenue=f["revenue"], expenses=opex + f["cost_of_sales"], net=np_, margin=np_ / f["revenue"]))
cur, prev = calc[-1], calc[-2]
pct = lambda a, b: (a - b) / b * 100
rev_c, exp_c, net_c = pct(cur["revenue"], prev["revenue"]), pct(cur["expenses"], prev["expenses"]), pct(cur["net"], prev["net"])
fmt = lambda x: f"{x:,.0f}"
summary = (f"In {cur['month']} revenue was {fmt(cur['revenue'])}, {'up' if rev_c>=0 else 'down'} {abs(rev_c):.1f}% on the previous month. "
           f"Total expenses were {fmt(cur['expenses'])} ({exp_c:+.1f}%), leaving a net profit of {fmt(cur['net'])} ({net_c:+.1f}%) and a margin of {cur['margin']*100:.1f}%. "
           f"The largest movement this month was net profit ({net_c:+.1f}%). Question to ask your bookkeeper: which costs moved most versus last month?")
plt.figure(figsize=(6.2, 2.6)); plt.bar([c["month"][2:] for c in calc], [c["revenue"] for c in calc], label="Revenue")
plt.plot([c["month"][2:] for c in calc], [c["net"] for c in calc], color="black", marker="o", label="Net profit")
plt.legend(); plt.xticks(rotation=45, fontsize=7); plt.tight_layout(); png = os.path.join(here, "_chart.png"); plt.savefig(png, dpi=160); plt.close()
S = getSampleStyleSheet(); doc = SimpleDocTemplate(os.path.join(here, "sample_report.pdf"), pagesize=A4)
t = Table([["Revenue", "Expenses", "Net profit", "Margin"], [fmt(cur["revenue"]), fmt(cur["expenses"]), fmt(cur["net"]), f"{cur['margin']*100:.1f}%"],
           [f"{rev_c:+.1f}% MoM", f"{exp_c:+.1f}% MoM", f"{net_c:+.1f}% MoM", f"{(cur['margin']-prev['margin'])*100:+.1f} pts"]])
t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey), ("GRID", (0, 0), (-1, -1), .5, colors.grey), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
doc.build([Paragraph(f"Monthly Report: {cur['month']}", S["Title"]), Paragraph("Sample Client Ltd (fictional). Demo report on synthetic data.", S["Italic"]), Spacer(1, 12), t, Spacer(1, 12),
           Paragraph("In plain English", S["Heading2"]), Paragraph(summary, S["BodyText"]), Spacer(1, 8), Image(png, width=420, height=176)])
os.remove(png); print(summary)
