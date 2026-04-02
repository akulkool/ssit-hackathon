"""Optional OpenAI chat completion."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


def ai_system_prompt() -> str:
    return (
        "You are FinSight AI, a premium fintech assistant. "
        "Be concise, friendly, practical, and data-driven. "
        "Give safe financial suggestions, not legal/tax guarantees. "
        "Use INR style naturally, and reference the user's budget utilization when available."
    )


def ask_openai(messages: list[dict[str, str]], financial_context: str) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": ai_system_prompt()},
            {"role": "system", "content": f"User financial context:\n{financial_context}"},
            *messages,
        ],
        "temperature": 0.6,
        "max_tokens": 260,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            body = json.loads(res.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"].strip()
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, IndexError, json.JSONDecodeError):
        return None
