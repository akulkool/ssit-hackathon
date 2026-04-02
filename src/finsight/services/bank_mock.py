from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


@dataclass(frozen=True)
class MockBankConfig:
    json_path: Path


def default_bank_config() -> MockBankConfig:
    root = Path(__file__).resolve().parents[4]  # FinSightAI/
    return MockBankConfig(json_path=root / "data" / "mock_bank_transactions.json")


def load_mock_transactions(cfg: Optional[MockBankConfig] = None) -> pd.DataFrame:
    cfg = cfg or default_bank_config()
    if not cfg.json_path.exists():
        return pd.DataFrame(columns=["txn_id", "posted_date", "description", "merchant", "amount", "category"])

    payload = json.loads(cfg.json_path.read_text(encoding="utf-8"))
    txns: List[Dict] = payload.get("transactions", [])
    df = pd.DataFrame(txns)
    if df.empty:
        return pd.DataFrame(columns=["txn_id", "posted_date", "description", "merchant", "amount", "category"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["posted_date"] = pd.to_datetime(df["posted_date"], errors="coerce").dt.date.astype(str)
    return df


def map_bank_category(bank_category: str) -> str:
    c = (bank_category or "").lower()
    if "food" in c or "restaurant" in c or "dining" in c:
        return "Food"
    if "transport" in c or "fuel" in c or "cab" in c or "uber" in c:
        return "Transport"
    if "shopping" in c or "ecom" in c or "retail" in c:
        return "Shopping"
    if "bill" in c or "utility" in c or "electric" in c or "phone" in c or "internet" in c:
        return "Bills"
    return "Others"

