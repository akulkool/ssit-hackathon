from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional


@dataclass(frozen=True)
class DBConfig:
    db_path: Path


def default_config() -> DBConfig:
    # Stored locally for demo friendliness.
    root = Path(__file__).resolve().parents[3]  # FinSightAI/
    return DBConfig(db_path=root / "data" / "finsight.db")


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def connect(cfg: Optional[DBConfig] = None) -> Iterator[sqlite3.Connection]:
    cfg = cfg or default_config()
    ensure_parent_dir(cfg.db_path)
    conn = sqlite3.connect(str(cfg.db_path), detect_types=sqlite3.PARSE_DECLTYPES)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
    finally:
        conn.close()


def init_db(cfg: Optional[DBConfig] = None) -> None:
    with connect(cfg) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS expenses (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              amount REAL NOT NULL CHECK(amount >= 0),
              category TEXT NOT NULL,
              date TEXT NOT NULL, -- ISO: YYYY-MM-DD
              note TEXT,
              source TEXT NOT NULL DEFAULT 'manual', -- manual|bank
              created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date);
            CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);

            CREATE TABLE IF NOT EXISTS settings (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS goals (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              target_amount REAL NOT NULL CHECK(target_amount >= 0),
              saved_amount REAL NOT NULL DEFAULT 0 CHECK(saved_amount >= 0),
              created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        conn.commit()


def get_setting(conn: sqlite3.Connection, key: str, default: Any = None) -> Any:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    if not row:
        return default
    try:
        return json.loads(row["value"])
    except Exception:
        return row["value"]


def set_setting(conn: sqlite3.Connection, key: str, value: Any) -> None:
    payload = json.dumps(value)
    conn.execute(
        "INSERT INTO settings(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, payload),
    )
    conn.commit()

