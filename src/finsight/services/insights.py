from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional

import pandas as pd


@dataclass(frozen=True)
class Insight:
    level: str  # info|warn
    text: str


def _pct_change(new: float, old: float) -> Optional[float]:
    if old <= 0 and new <= 0:
        return 0.0
    if old <= 0:
        return None
    return (new - old) / old * 100.0


def week_over_week_insights(expenses: pd.DataFrame, today: Optional[date] = None) -> List[Insight]:
    today = today or date.today()
    if expenses.empty:
        return [Insight(level="info", text="Add a few expenses to unlock smart insights.")]

    df = expenses.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date

    this_week_start = today - timedelta(days=today.weekday())
    last_week_start = this_week_start - timedelta(days=7)
    last_week_end = this_week_start - timedelta(days=1)

    this_w = df[(df["date"] >= this_week_start) & (df["date"] <= today)]
    last_w = df[(df["date"] >= last_week_start) & (df["date"] <= last_week_end)]

    insights: List[Insight] = []

    this_by = this_w.groupby("category")["amount"].sum().to_dict()
    last_by = last_w.groupby("category")["amount"].sum().to_dict()

    for cat in sorted(set(this_by) | set(last_by)):
        new = float(this_by.get(cat, 0.0))
        old = float(last_by.get(cat, 0.0))
        ch = _pct_change(new, old)
        if ch is None:
            if new > 0:
                insights.append(Insight(level="info", text=f"You started spending on {cat} this week."))
            continue
        if abs(ch) >= 25 and (new + old) > 0:
            direction = "more" if ch > 0 else "less"
            insights.append(
                Insight(level="info", text=f"You spent {abs(ch):.0f}% {direction} on {cat} this week.")
            )

    if not insights:
        insights.append(Insight(level="info", text="Your spending looks stable week-over-week."))
    return insights[:6]


def month_over_month_insights(expenses: pd.DataFrame, today: Optional[date] = None) -> List[Insight]:
    today = today or date.today()
    if expenses.empty:
        return []

    df = expenses.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date

    this_month_start = today.replace(day=1)
    last_month_end = this_month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    this_m = df[(df["date"] >= this_month_start) & (df["date"] <= today)]
    last_m = df[(df["date"] >= last_month_start) & (df["date"] <= last_month_end)]

    insights: List[Insight] = []
    this_by = this_m.groupby("category")["amount"].sum().to_dict()
    last_by = last_m.groupby("category")["amount"].sum().to_dict()

    for cat in sorted(set(this_by) | set(last_by)):
        new = float(this_by.get(cat, 0.0))
        old = float(last_by.get(cat, 0.0))
        ch = _pct_change(new, old)
        if ch is None:
            if new > 0:
                insights.append(Insight(level="info", text=f"{cat} spending appeared this month."))
            continue
        if abs(ch) >= 25 and (new + old) > 0:
            direction = "increased" if ch > 0 else "decreased"
            insights.append(
                Insight(level="info", text=f"Your {cat} expenses {direction} compared to last month.")
            )

    return insights[:6]

