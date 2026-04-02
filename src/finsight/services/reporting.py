from __future__ import annotations

from datetime import date
from typing import Optional

import pandas as pd
from fpdf import FPDF


def _latin1_safe(text: str) -> str:
    # fpdf core fonts are latin-1; keep report generation robust for demos.
    return (text or "").encode("latin-1", errors="replace").decode("latin-1")


def build_pdf_report(
    *,
    app_name: str,
    currency: str,
    generated_on: Optional[date],
    total_spend: float,
    month_spend: float,
    month_budget: Optional[float],
    by_category: pd.DataFrame,  # category, amount
) -> bytes:
    generated_on = generated_on or date.today()
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    title = f"{app_name} - Spending Report"
    pdf.cell(0, 10, _latin1_safe(title), ln=True)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, _latin1_safe(f"Generated on: {generated_on.isoformat()}"), ln=True)
    pdf.ln(2)

    cur = currency if currency.isascii() else "INR "

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Summary", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, _latin1_safe(f"Total spending (all time): {cur}{total_spend:,.2f}"), ln=True)
    pdf.cell(0, 7, _latin1_safe(f"Spending this month: {cur}{month_spend:,.2f}"), ln=True)

    if month_budget is not None and month_budget > 0:
        remaining = max(0.0, month_budget - month_spend)
        pdf.cell(0, 7, _latin1_safe(f"Monthly budget: {cur}{month_budget:,.2f}"), ln=True)
        pdf.cell(0, 7, _latin1_safe(f"Remaining (month): {cur}{remaining:,.2f}"), ln=True)
    else:
        pdf.cell(0, 7, "Monthly budget: Not set", ln=True)

    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Category breakdown", ln=True)

    if by_category is None or by_category.empty:
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 7, "No category data available yet.", ln=True)
    else:
        tmp = by_category.copy()
        tmp["amount"] = pd.to_numeric(tmp["amount"], errors="coerce").fillna(0.0)
        tmp = tmp.sort_values("amount", ascending=False).head(10)
        pdf.set_font("Helvetica", "", 11)
        for _, r in tmp.iterrows():
            pdf.cell(
                0,
                7,
                _latin1_safe(f"- {r['category']}: {cur}{float(r['amount']):,.2f}"),
                ln=True,
            )

    return bytes(pdf.output(dest="S"))

