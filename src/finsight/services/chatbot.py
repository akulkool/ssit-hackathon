from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import pandas as pd


@dataclass(frozen=True)
class ChatResponse:
    answer: str
    followups: List[str]


def _top_category(expenses: pd.DataFrame) -> Tuple[str, float]:
    if expenses.empty:
        return ("None", 0.0)
    by = expenses.groupby("category")["amount"].sum().sort_values(ascending=False)
    cat = str(by.index[0])
    amt = float(by.iloc[0])
    return cat, amt


def respond(user_message: str, expenses: pd.DataFrame) -> ChatResponse:
    msg = (user_message or "").strip().lower()

    if not msg:
        return ChatResponse(
            answer="Ask me something like: “Where did I spend the most?” or “How can I save money?”",
            followups=["Where did I spend the most?", "How can I save money?"],
        )

    cat, amt = _top_category(expenses)
    total = float(expenses["amount"].sum()) if not expenses.empty else 0.0

    if any(k in msg for k in ["most", "highest", "top", "maximum"]) and any(
        k in msg for k in ["spend", "spent", "expense", "expenses"]
    ):
        if total <= 0:
            return ChatResponse(
                answer="I don’t see any expenses yet—add a few and I’ll summarize where you spend the most.",
                followups=["Add an expense", "Import mock bank transactions"],
            )
        pct = (amt / total * 100.0) if total > 0 else 0.0
        return ChatResponse(
            answer=f"You spent the most on {cat}: {amt:.2f} (about {pct:.0f}% of total).",
            followups=["Show category breakdown", "How can I reduce this?"],
        )

    if any(k in msg for k in ["save", "reduce", "cut", "tips", "budget"]):
        tips = [
            "Set a monthly budget and aim for the 80% warning to stay on track.",
            "Watch your top category first—small reductions there have the biggest impact.",
            "Try a weekly cap for discretionary spending (Food/Shopping) and review every Sunday.",
        ]
        if total > 0:
            tips.insert(0, f"Your top category is {cat}—start by trimming that by 10–15%.")
        return ChatResponse(
            answer="Here are a few ways to save money:\n- " + "\n- ".join(tips),
            followups=["Set a budget", "What was my spending trend?"],
        )

    if any(k in msg for k in ["trend", "over time", "daily", "weekly", "monthly"]):
        if expenses.empty:
            return ChatResponse(
                answer="No trend yet—add expenses for a few days and I’ll show patterns.",
                followups=["Add an expense", "Import mock bank transactions"],
            )
        daily = (
            expenses.assign(date=pd.to_datetime(expenses["date"], errors="coerce").dt.date)
            .groupby("date")["amount"]
            .sum()
        )
        if len(daily) >= 2 and daily.iloc[-1] > daily.iloc[0]:
            direction = "up"
        elif len(daily) >= 2 and daily.iloc[-1] < daily.iloc[0]:
            direction = "down"
        else:
            direction = "flat"
        return ChatResponse(
            answer=f"Your recent daily spending trend looks {direction}. Check the Dashboard → Trends for details.",
            followups=["Show prediction", "Where did I spend the most?"],
        )

    return ChatResponse(
        answer="I can help with: top spend category, savings tips, and trends. Try: “Where did I spend the most?”",
        followups=["Where did I spend the most?", "How can I save money?", "Show my spending trend"],
    )

