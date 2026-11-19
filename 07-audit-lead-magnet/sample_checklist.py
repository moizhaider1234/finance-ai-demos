"""Renders a sample AUDIT checklist PDF (same content structure the workflow emails). Run: python sample_checklist.py"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
S = getSampleStyleSheet(); here = os.path.dirname(__file__)
items = [("Invoice entry", "Automate invoice capture: extract vendor, date, tax and total from PDFs and auto-suggest categories, with a human review queue."),
         ("Receivables chasing", "Set tiered reminders that stop when an invoice is marked paid, plus a weekly summary to the owner."),
         ("Bank reconciliation", "Auto-match bank lines to ledger entries; review only the exceptions.")]
SimpleDocTemplate(os.path.join(here, "sample_checklist.pdf"), pagesize=A4).build(
    [Paragraph("Your Automation AUDIT", S["Title"]), Paragraph("Hi Sample Firm,", S["BodyText"]), Paragraph("<b>Automation opportunity score: 36/100 (Medium opportunity)</b>", S["BodyText"]),
     Spacer(1, 8), Paragraph("Your priority checklist", S["Heading2"])] + [Paragraph(f"{i+1}. <b>{a}</b>: {b}", S["BodyText"]) for i, (a, b) in enumerate(items)] +
    [Spacer(1, 10), Paragraph("General guidance from a demo system, not financial or tax advice.", S["Italic"])])
