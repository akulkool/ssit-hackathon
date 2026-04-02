from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Literal, Optional, Tuple

import pandas as pd

from finsight.services.storage import list_expenses


Period = Literal["D", "W", "M"]


@dataclass(frozen=True)
class SpendSummary:
    total: float
    by_category: pd.DataFrame  # columns: category, amount
    trend: pd.DataFrame  # columns: period, amount


def _to_datetime_series(df: pd.DataFrame) -> pd.Series:
    return pd.to_datetime(df["date"], errors="coerce")


def spend_summary(conn: sqlite3.Connection, period: Period = "D") -> SpendSummary:
    df = list_expenses(conn)
    if df.empty:
        return SpendSummary(
            total=0.0,
            by_category=pd.DataFrame(columns=["category", "amount"]),
            trend=pd.DataFrame(columns=["period", "amount"]),
        )

    df["_dt"] = _to_datetime_series(df)
    total = float(df["amount"].sum())

    by_cat = (
        df.groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
    )

    if period == "D":
        df["period"] = df["_dt"].dt.to_period("D").dt.to_timestamp()
    elif period == "W":
        df["period"] = df["_dt"].dt.to_period("W").dt.start_time
    else:
        df["period"] = df["_dt"].dt.to_period("M").dt.to_timestamp()

    trend = df.groupby("period", as_index=False)["amount"].sum().sort_values("period")
    trend.rename(columns={"period": "period", "amount": "amount"}, inplace=True)

    return SpendSummary(total=total, by_category=by_cat, trend=trend)


def filter_expenses(
    conn: sqlite3.Connection,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> pd.DataFrame:
    df = list_expenses(conn)
    if df.empty:
        return df
    dts = pd.to_datetime(df["date"], errors="coerce").dt.date
    if start_date is not None:
        df = df[dts >= start_date]
    if end_date is not None:
        df = df[dts <= end_date]
    return df


def current_month_range(today: Optional[date] = None) -> Tuple[date, date]:
    today = today or date.today()
    start = today.replace(day=1)
    if start.month == 12:
        end = date(start.year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(start.year, start.month + 1, 1) - timedelta(days=1)
    return start, end


def month_spend(conn: sqlite3.Connection, today: Optional[date] = None) -> float:
    s, e = current_month_range(today)
    df = filter_expenses(conn, s, e)
    if df.empty:
        return 0.0
    return float(df["amount"].sum())

