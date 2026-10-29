"""Anonymous call reports in SQLite.

Privacy by design: transcripts are never stored. A report keeps only the verdict, the
tactics used and the numbers the caller tried to get money sent to, which is exactly
what an anti-scam centre would need to spot a new campaign early.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from collections import Counter
from datetime import datetime, timezone

from .config import settings

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    level TEXT NOT NULL,
    risk REAL NOT NULL,
    scam_type TEXT,
    tactics TEXT NOT NULL,
    numbers TEXT NOT NULL,
    amount_rm REAL
)
"""


def _connect(path: str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or settings.db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    return conn


def save_report(analysis: dict, path: str | None = None) -> int:
    numbers = [lk["number"] for lk in analysis.get("lookups", [])]
    amounts = analysis.get("entities", {}).get("amounts_rm") or []
    with _lock, _connect(path) as conn:
        cur = conn.execute(
            "INSERT INTO reports (created_at, level, risk, scam_type, tactics, numbers, amount_rm) VALUES (?,?,?,?,?,?,?)",
            (
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                analysis.get("level", "low"),
                float(analysis.get("risk", 0)),
                analysis.get("scam_type"),
                json.dumps([t["id"] for t in analysis.get("tactics", [])]),
                json.dumps(numbers),
                max(amounts) if amounts else None,
            ),
        )
        return int(cur.lastrowid)


def stats(path: str | None = None) -> dict:
    with _lock, _connect(path) as conn:
        rows = conn.execute("SELECT * FROM reports ORDER BY id DESC").fetchall()
    levels = Counter(r["level"] for r in rows)
    tactics = Counter(t for r in rows for t in json.loads(r["tactics"]))
    types = Counter(r["scam_type"] for r in rows if r["scam_type"])
    numbers = Counter(n for r in rows if r["level"] != "low" for n in json.loads(r["numbers"]))
    protected = sum(r["amount_rm"] or 0 for r in rows if r["level"] == "high")
    return {
        "total": len(rows),
        "levels": dict(levels),
        "tactics": tactics.most_common(),
        "scam_types": types.most_common(),
        "top_numbers": numbers.most_common(10),
        "amount_at_risk_rm": protected,
        "recent": [
            {
                "created_at": r["created_at"],
                "level": r["level"],
                "risk": r["risk"],
                "scam_type": r["scam_type"],
                "tactics": json.loads(r["tactics"]),
            }
            for r in rows[:15]
        ],
    }
