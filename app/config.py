"""Runtime configuration, read once from environment variables (or a .env file)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader so the project needs no extra dependency."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv(BASE_DIR.parent / ".env")


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
    # A "latest" alias keeps working as Google renames versioned models.
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-flash-latest").strip()
    gemini_audio_model: str = os.getenv("GEMINI_AUDIO_MODEL", "").strip() or os.getenv(
        "GEMINI_MODEL", "gemini-flash-latest"
    ).strip()
    gemini_timeout_s: float = float(os.getenv("GEMINI_TIMEOUT_S", "12"))
    db_path: str = os.getenv("SCAMSHIELD_DB", str(BASE_DIR.parent / "scamshield.db"))
    # "demo" = bundled sample registry (clearly labelled in the UI);
    # "link" = never claim a result, only deep-link to the official Semak Mule portal.
    registry_mode: str = os.getenv("REGISTRY_MODE", "demo").strip().lower()

    @property
    def llm_enabled(self) -> bool:
        return bool(self.gemini_api_key)


settings = Settings()
