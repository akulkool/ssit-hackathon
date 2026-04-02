"""Core finance analytics (ported from Streamlit app.py)."""
from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

CURRENCY_PREFIX = "INR "


def money(v: float) -> str:
    return f"{CURRENCY_PREFIX}{v:,.2f}"


def to_df(expenses: list[dict[str, Any]]) -> pd.DataFrame:
    if not expenses:
        return pd.DataFrame(columns=["date", "merchant", "amount", "category", "source"])
    df = pd.DataFrame(expenses)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date.astype(str)
    return df


def month_filter(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    now = date.today()
    d = pd.to_datetime(df["date"], errors="coerce")
    return df[(d.dt.year == now.year) & (d.dt.month == now.month)].copy()


def calc_health_score(df: pd.DataFrame, budget: float) -> int:
    if df.empty:
        return 75
    mdf = month_filter(df)
    monthly_spend = float(mdf["amount"].sum()) if not mdf.empty else 0.0

    ratio_score = 25
    if budget > 0:
        ratio = monthly_spend / budget
        if ratio <= 0.5:
            ratio_score = 35
        elif ratio <= 0.8:
            ratio_score = 28
        elif ratio <= 1.0:
            ratio_score = 18
        else:
            ratio_score = 8

    daily = mdf.groupby("date", as_index=False)["amount"].sum() if not mdf.empty else pd.DataFrame()
    consistency_score = 20
    if not daily.empty and len(daily) > 2:
        avg = float(daily["amount"].mean()) or 1.0
        std = float(daily["amount"].std() or 0.0)
        cv = std / avg
        consistency_score = max(8, int(30 - cv * 18))

    anomaly_penalty = 0
    if not daily.empty and len(daily) > 3:
        threshold = float(daily["amount"].mean()) + 2 * float(daily["amount"].std() or 0.0)
        spikes = int((daily["amount"] > threshold).sum())
        anomaly_penalty = min(20, spikes * 5)

    base = ratio_score + consistency_score + 35
    return max(1, min(100, int(base - anomaly_penalty)))


def budget_alerts(spend: float, budget: float) -> list[dict[str, Any]]:
    if budget <= 0:
        return []
    used = (spend / budget) * 100.0
    checks = [
        (95, "error", "Danger: Budget nearly finished"),
        (90, "error", "Critical: Almost exhausted"),
        (75, "warning", "Warning: High spending"),
        (50, "info", "Halfway there!"),
        (25, "success", "You've used 25% of your budget"),
    ]
    return [{"threshold_pct": c[0], "level": c[1], "message": c[2]} for c in checks if used >= c[0]]


def budget_message(used_pct: float) -> tuple[str, str]:
    if used_pct >= 95:
        return ("🚨", "Danger! You may overspend — take action NOW")
    if used_pct >= 90:
        return ("🔴", "Critical: Budget almost exhausted")
    if used_pct >= 75:
        return ("🟠", "Warning: Spending is increasing fast")
    if used_pct >= 50:
        return ("🟡", "Half your budget used — stay mindful")
    if used_pct >= 25:
        return ("🟢", "Good start! You're in control")
    return ("🟢", "Great discipline so far — keep going!")


def smart_insights(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return ["Start by adding expenses to unlock insights."]
    insights: list[str] = []
    by_cat = df.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
    total = float(by_cat["amount"].sum()) or 1.0
    top = by_cat.iloc[0]
    if float(top["amount"]) / total > 0.35:
        insights.append(
            f"Overspending alert: {top['category']} is {float(top['amount'])/total:.0%} of total spend."
        )
        insights.append(f"Suggestion: Reduce {top['category']} expenses by 15-20% this month.")

    daily = df.groupby("date", as_index=False)["amount"].sum()
    if len(daily) >= 4:
        avg = float(daily["amount"].mean())
        spike_rows = daily[daily["amount"] > (avg * 1.8)]
        if not spike_rows.empty:
            insights.append("Sudden spike detected in daily spending. Review one-time large purchases.")

    sub_keywords = ["netflix", "spotify", "prime", "subscription"]
    desc = " ".join(df["merchant"].astype(str).str.lower().tolist())
    if any(k in desc for k in sub_keywords):
        insights.append("Limit subscriptions and prune unused auto-renew plans.")
    if not insights:
        insights.append("Great control! Your spending pattern looks balanced.")
    return insights[:6]


def investment_tips(df: pd.DataFrame, budget: float) -> list[str]:
    if budget <= 0:
        return ["Set a monthly budget first to get personalized investment suggestions."]
    current = float(month_filter(df)["amount"].sum()) if not df.empty else 0.0
    savings = max(0.0, budget - current)
    if savings < 1000:
        return ["Focus on building an emergency fund first (target 3-6 months expenses)."]
    if savings < 3000:
        return [f"You can put {money(savings)} into a recurring deposit for disciplined saving."]
    if savings < 8000:
        return [
            f"Consider investing {money(savings*0.7)} in SIP and keep {money(savings*0.3)} as emergency cash."
        ]
    return [
        f"Strong surplus! You can invest {money(savings*0.6)} in SIP for long-term growth.",
        f"Allocate {money(savings*0.25)} to emergency fund and {money(savings*0.15)} to fixed deposit.",
    ]


def build_financial_context(df: pd.DataFrame, budget: float) -> str:
    total = float(df["amount"].sum()) if not df.empty else 0.0
    month_df = month_filter(df)
    m_spend = float(month_df["amount"].sum()) if not month_df.empty else 0.0
    used = (m_spend / budget * 100.0) if budget > 0 else 0.0
    remain = max(0.0, budget - m_spend) if budget > 0 else 0.0
    if df.empty:
        top_line = "Top category: N/A"
    else:
        by_cat = df.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
        top_line = ", ".join(
            [f"{r['category']}={money(float(r['amount']))}" for _, r in by_cat.head(3).iterrows()]
        )
    return (
        f"Total spend all-time: {money(total)}\n"
        f"Current month spend: {money(m_spend)}\n"
        f"Monthly budget: {money(budget) if budget > 0 else 'Not set'}\n"
        f"Budget used: {used:.1f}%\n"
        f"Budget remaining: {money(remain)}\n"
        f"Top categories: {top_line}\n"
    )


def chatbot_answer(prompt: str, df: pd.DataFrame, budget: float) -> str:
    q = (prompt or "").lower().strip()
    if not q:
        return "I am here to help with spending, savings, and budget plans."
    by_cat = (
        df.groupby("category")["amount"].sum().sort_values(ascending=False) if not df.empty else pd.Series(dtype=float)
    )

    if "save" in q or "saving" in q:
        top_line = ""
        if not by_cat.empty:
            top_cat = str(by_cat.index[0])
            top_val = float(by_cat.iloc[0])
            top_line = f"Hey! I noticed something interesting: your biggest spending is {top_cat} ({money(top_val)}). "
        return (
            top_line
            + "If you cut that by 15-20%, you can redirect the savings into SIP or your emergency fund every month."
        )
    if "most" in q or "highest" in q:
        if by_cat.empty:
            return "I do not see enough data yet. Add a few expenses and ask me again."
        return (
            f"You are spending the most on {by_cat.index[0]} at {money(float(by_cat.iloc[0]))}. "
            "We can optimize this first for quick wins."
        )
    if "budget" in q:
        if budget <= 0:
            return "Set a monthly budget and I will actively track usage milestones for you."
        current = float(month_filter(df)["amount"].sum()) if not df.empty else 0.0
        ratio = (current / budget) * 100.0
        return (
            f"Your budget status right now: {ratio:.1f}% used ({money(current)} of {money(budget)}). "
            "Want me to suggest a safer weekly cap?"
        )
    if "invest" in q or "sip" in q:
        return (
            "Nice mindset! A simple rule: 50% needs, 30% wants, 20% investing. "
            "Start a small SIP now and increase it every quarter."
        )
    return "Happy to help. Ask me about savings ideas, budget usage, overspending categories, or SIP suggestions."
