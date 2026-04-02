"""Compose full analysis response for dashboard."""
from __future__ import annotations

from typing import Any

from services import finance as fin


def analyze_user(expenses: list[dict[str, Any]], budget: float) -> dict[str, Any]:
    df = fin.to_df(expenses)
    month_df = fin.month_filter(df)
    month_spend = float(month_df["amount"].sum()) if not month_df.empty else 0.0
    total_spend = float(df["amount"].sum()) if not df.empty else 0.0
    score = fin.calc_health_score(df, budget)
    remaining = max(0.0, budget - month_spend) if budget > 0 else 0.0
    used_pct = min(100.0, (month_spend / budget) * 100.0) if budget > 0 else 0.0
    emoji, msg = fin.budget_message(used_pct)

    by_category = []
    if not df.empty:
        bc = df.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
        by_category = [{"category": str(r["category"]), "amount": float(r["amount"])} for _, r in bc.iterrows()]

    daily_trend = []
    if not df.empty:
        d = df.groupby("date", as_index=False)["amount"].sum().sort_values("date")
        daily_trend = [{"date": str(r["date"]), "amount": float(r["amount"])} for _, r in d.iterrows()]

    return {
        "total_spend": round(total_spend, 2),
        "month_spend": round(month_spend, 2),
        "budget": round(budget, 2),
        "budget_used_pct": round(used_pct, 2),
        "remaining_budget": round(remaining, 2),
        "health_score": score,
        "budget_emoji": emoji,
        "budget_message": msg,
        "alerts": fin.budget_alerts(month_spend, budget),
        "insights": fin.smart_insights(df),
        "investment_tips": fin.investment_tips(df, budget),
        "by_category": by_category,
        "daily_trend": daily_trend,
        "currency": "INR",
    }
