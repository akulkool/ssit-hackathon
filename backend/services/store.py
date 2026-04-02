"""JSON-backed user store (same schema as legacy Streamlit app)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# FinSightAI/data/users_data.json (project root parent of backend/)
ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = ROOT / "data" / "users_data.json"


def ensure_store() -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text(json.dumps({"users": {}}, indent=2), encoding="utf-8")


def load_store() -> dict[str, Any]:
    ensure_store()
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def save_store(store: dict[str, Any]) -> None:
    DATA_FILE.write_text(json.dumps(store, indent=2), encoding="utf-8")


def get_user(user_id: str) -> dict[str, Any]:
    store = load_store()
    if user_id not in store["users"]:
        store["users"][user_id] = {"mobile": user_id, "budget": 0.0, "expenses": []}
        save_store(store)
    return store["users"][user_id]


def save_user(user_id: str, user: dict[str, Any]) -> None:
    store = load_store()
    store["users"][user_id] = user
    save_store(store)
