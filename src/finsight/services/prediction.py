from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


@dataclass(frozen=True)
class ForecastResult:
    history_daily: pd.DataFrame  # date, amount
    forecast_daily: pd.DataFrame  # date, predicted
    method: str


def _daily_series(expenses: pd.DataFrame) -> pd.DataFrame:
    if expenses.empty:
        return pd.DataFrame(columns=["date", "amount"])
    df = expenses.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    daily = df.groupby("date", as_index=False)["amount"].sum().sort_values("date")
    return daily


def forecast_spend(
    expenses: pd.DataFrame, horizon_days: int = 14, min_points: int = 7
) -> ForecastResult:
    history = _daily_series(expenses)
    if history.empty:
        future_dates = [date.today() + timedelta(days=i) for i in range(1, horizon_days + 1)]
        return ForecastResult(
            history_daily=history,
            forecast_daily=pd.DataFrame({"date": future_dates, "predicted": [0.0] * horizon_days}),
            method="empty",
        )

    # Fill missing days (so regression isn't biased by sparse logging)
    d0 = history["date"].min()
    d1 = history["date"].max()
    idx = pd.date_range(d0, d1, freq="D").date
    filled = (
        history.set_index("date")
        .reindex(idx, fill_value=0.0)
        .rename_axis("date")
        .reset_index()
    )

    if len(filled) < min_points:
        # Moving average fallback for early demos
        window = min(7, max(1, len(filled)))
        ma = float(pd.Series(filled["amount"]).tail(window).mean())
        future_dates = [d1 + timedelta(days=i) for i in range(1, horizon_days + 1)]
        forecast = pd.DataFrame({"date": future_dates, "predicted": [ma] * horizon_days})
        return ForecastResult(history_daily=filled, forecast_daily=forecast, method="moving_average")

    X = np.arange(len(filled)).reshape(-1, 1)
    y = filled["amount"].to_numpy(dtype=float)
    model = LinearRegression()
    model.fit(X, y)

    future_X = np.arange(len(filled), len(filled) + horizon_days).reshape(-1, 1)
    yhat = model.predict(future_X)
    yhat = np.clip(yhat, 0.0, None)

    future_dates = [d1 + timedelta(days=i) for i in range(1, horizon_days + 1)]
    forecast = pd.DataFrame({"date": future_dates, "predicted": yhat})
    return ForecastResult(history_daily=filled, forecast_daily=forecast, method="linear_regression")

