"""
FinSight AI — FastAPI backend.
Run: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import hashlib
import os
import random
from datetime import date, timedelta
from typing import Any

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from services import analyze as analyze_svc
from services import finance as fin
from services.openai_chat import ask_openai
from services.prediction import forecast_spend
from services.store import get_user, save_user

app = FastAPI(title="FinSight AI API", version="1.0.0")

_default_cors = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
_extra = os.environ.get("ALLOWED_ORIGINS", "").strip()
if _extra:
    allow_origins = [o.strip() for o in _extra.split(",") if o.strip()]
else:
    allow_origins = list(_default_cors)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Models ---


class AnalyzeRequest(BaseModel):
    user_id: str = Field(..., description="Mobile / user id")
    budget: float | None = None  # optional override; else from store


class PredictRequest(BaseModel):
    user_id: str
    horizon_days: int = 14


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatInsightsRequest(BaseModel):
    user_id: str
    message: str
    history: list[ChatMessage] = Field(default_factory=list)


class TransactionCreate(BaseModel):
    user_id: str
    date: str
    merchant: str
    amount: float
    category: str
    source: str = "manual"


class BudgetUpdate(BaseModel):
    user_id: str
    budget: float


class ImportBankRequest(BaseModel):
    user_id: str
    count: int = 10


# --- Helpers ---


def fake_bank_transactions(mobile: str, n: int = 10) -> list[dict[str, Any]]:
    seed = int(hashlib.sha256(f"{mobile}-{date.today().isoformat()}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    merchants = [
        ("Swiggy", "Food"),
        ("Uber", "Transport"),
        ("Amazon", "Shopping"),
        ("Electricity Board", "Bills"),
        ("BigBasket", "Food"),
        ("Metro Card", "Transport"),
        ("Myntra", "Shopping"),
        ("Airtel", "Bills"),
    ]
    out: list[dict[str, Any]] = []
    for i in range(n):
        merchant, cat = rng.choice(merchants)
        amount = round(rng.uniform(120, 2200), 2)
        d = (date.today() - timedelta(days=rng.randint(0, 21))).isoformat()
        out.append(
            {
                "txn_id": f"tx_{seed % 10000}_{i+1}",
                "date": d,
                "merchant": merchant,
                "amount": amount,
                "category": cat,
                "source": "bank_api",
            }
        )
    return out


# --- Endpoints ---


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "finsight-api"}


@app.post("/analyze-expenses")
def analyze_expenses(body: AnalyzeRequest) -> dict[str, Any]:
    user = get_user(body.user_id)
    budget = float(body.budget) if body.budget is not None else float(user.get("budget", 0.0) or 0.0)
    expenses = user.get("expenses", [])
    return analyze_svc.analyze_user(expenses, budget)


@app.get("/get-transactions")
def get_transactions(user_id: str = Query(..., description="User / mobile id")) -> dict[str, Any]:
    user = get_user(user_id)
    return {"user_id": user_id, "transactions": user.get("expenses", [])}


@app.post("/predict-spending")
def predict_spending(body: PredictRequest) -> dict[str, Any]:
    user = get_user(body.user_id)
    return forecast_spend(user.get("expenses", []), horizon_days=body.horizon_days)


@app.post("/chat-insights")
def chat_insights(body: ChatInsightsRequest) -> dict[str, Any]:
    user = get_user(body.user_id)
    budget = float(user.get("budget", 0.0) or 0.0)
    expenses = user.get("expenses", [])
    df = fin.to_df(expenses)
    context = fin.build_financial_context(df, budget)

    openai_messages = [{"role": m.role, "content": m.content} for m in body.history if m.role in ("user", "assistant")]
    openai_messages.append({"role": "user", "content": body.message})

    answer = ask_openai(openai_messages[-12:], context)
    source = "openai"
    if not answer:
        answer = fin.chatbot_answer(body.message, df, budget)
        source = "rules"

    return {"reply": answer, "source": source}


@app.post("/transactions")
def add_transaction(tx: TransactionCreate) -> dict[str, Any]:
    user = get_user(tx.user_id)
    user["expenses"].append(
        {
            "date": tx.date,
            "merchant": tx.merchant,
            "amount": float(tx.amount),
            "category": tx.category,
            "source": tx.source,
        }
    )
    save_user(tx.user_id, user)
    return {"ok": True, "count": len(user["expenses"])}


@app.post("/budget")
def update_budget(body: BudgetUpdate) -> dict[str, Any]:
    user = get_user(body.user_id)
    user["budget"] = float(body.budget)
    save_user(body.user_id, user)
    return {"ok": True, "budget": user["budget"]}


@app.post("/import-bank")
def import_bank(body: ImportBankRequest) -> dict[str, Any]:
    user = get_user(body.user_id)
    bank = fake_bank_transactions(body.user_id, n=body.count)
    existing = {
        f"{e.get('date','')}-{e.get('merchant','')}-{float(e.get('amount',0.0)):.2f}"
        for e in user.get("expenses", [])
    }
    imported = 0
    for row in bank:
        key = f"{row['date']}-{row['merchant']}-{float(row['amount']):.2f}"
        if key in existing:
            continue
        user["expenses"].append(row)
        imported += 1
    save_user(body.user_id, user)
    return {"ok": True, "imported": imported, "preview": bank}
