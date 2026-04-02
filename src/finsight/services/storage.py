from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Optional

import pandas as pd

from finsight.constants import CATEGORIES


@dataclass(frozen=True)
class ExpenseInput:
    amount: float
    category: str
    date: str  # YYYY-MM-DD
    note: str = ""
    source: str = "manual"  # manual|bank


def add_expense(conn: sqlite3.Connection, exp: ExpenseInput) -> int:
    if exp.category not in CATEGORIES:
        raise ValueError(f"Unknown category: {exp.category}")
    cur = conn.execute(
        """
        INSERT INTO expenses(amount, category, date, note, source)
        VALUES (?, ?, ?, ?, ?)
        """,
        (float(exp.amount), exp.category, exp.date, exp.note.strip() or None, exp.source),
    )
    conn.commit()
    return int(cur.lastrowid)


def delete_expense(conn: sqlite3.Connection, expense_id: int) -> None:
    conn.execute("DELETE FROM expenses WHERE id = ?", (int(expense_id),))
    conn.commit()


def list_expenses(conn: sqlite3.Connection, limit: Optional[int] = None) -> pd.DataFrame:
    q = "SELECT id, amount, category, date, note, source, created_at FROM expenses ORDER BY date DESC, id DESC"
    params = ()
    if limit is not None:
        q += " LIMIT ?"
        params = (int(limit),)
    rows = conn.execute(q, params).fetchall()
    df = pd.DataFrame([dict(r) for r in rows])
    if df.empty:
        return pd.DataFrame(
            columns=["id", "amount", "category", "date", "note", "source", "created_at"]
        )
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date.astype(str)
    return df

