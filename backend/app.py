"""
Run the FinSight API with: python app.py

Uses PORT (default 8000). Set UVICORN_RELOAD=1 for local auto-reload.
"""
from __future__ import annotations

import os

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    reload = os.environ.get("UVICORN_RELOAD", "").lower() in ("1", "true", "yes")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=reload)
