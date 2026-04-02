"""Simple spend forecast (linear regression + moving average fallback)."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from services.finance import to_df


def forecast_spend(
    expenses: list[dict[str, Any]], horizon_days: int = 14, min_points: int = 7
) -> dict[str, Any]:
    df = to_df(expenses)
    if df.empty:
        future = [(date.today() + timedelta(days=i)).isoformat() for i in range(1, horizon_days + 1)]
        return {
            "method": "empty",
            "history": [],
            "forecast": [{"date": d, "predicted": 0.0} for d in future],
        }

    hist = (
        df.assign(_d=pd.to_datetime(df["date"], errors="coerce").dt.date)
        .groupby("_d", as_index=False)["amount"]
        .sum()
        .sort_values("_d")
    )
    hist.rename(columns={"_d": "date"}, inplace=True)
    d0 = hist["date"].min()
    d1 = hist["date"].max()
    idx = pd.date_range(d0, d1, freq="D").date
    filled = (
        hist.set_index("date")
        .reindex(idx, fill_value=0.0)
        .rename_axis("date")
        .reset_index()
    )

    if len(filled) < min_points:
        window = min(7, max(1, len(filled)))
        ma = float(pd.Series(filled["amount"]).tail(window).mean())
        future_dates = [d1 + timedelta(days=i) for i in range(1, horizon_days + 1)]
        return {
            "method": "moving_average",
            "history": [{"date": str(r["date"]), "amount": float(r["amount"])} for _, r in filled.iterrows()],
            "forecast": [{"date": d.isoformat(), "predicted": round(ma, 2)} for d in future_dates],
        }

    X = np.arange(len(filled)).reshape(-1, 1)
    y = filled["amount"].to_numpy(dtype=float)
    model = LinearRegression()
    model.fit(X, y)
    future_X = np.arange(len(filled), len(filled) + horizon_days).reshape(-1, 1)
    yhat = np.clip(model.predict(future_X), 0.0, None)
    future_dates = [d1 + timedelta(days=i) for i in range(1, horizon_days + 1)]

    return {
        "method": "linear_regression",
        "history": [{"date": str(r["date"]), "amount": float(r["amount"])} for _, r in filled.iterrows()],
        "forecast": [
            {"date": d.isoformat(), "predicted": round(float(p), 2)} for d, p in zip(future_dates, yhat)
        ],
    }
