from __future__ import annotations

import platform
import subprocess


def speak(text: str) -> bool:
    """
    Best-effort voice alert for demos.
    - On macOS: uses built-in `say`
    - Else: no-op (returns False)
    """
    msg = (text or "").strip()
    if not msg:
        return False

    if platform.system() == "Darwin":
        try:
            subprocess.run(["say", msg], check=False)
            return True
        except Exception:
            return False
    return False

