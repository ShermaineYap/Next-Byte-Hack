"""Fill the community dashboard with one anonymous report per demo call (rules engine, offline).

    python -m scripts.seed_demo_reports
"""

import asyncio
import json

from app import store
from app.analyzer import analyze
from app.config import DATA_DIR


async def main() -> None:
    scenarios = json.loads((DATA_DIR / "scenarios.json").read_text(encoding="utf-8"))["scenarios"]
    saved = 0
    for sc in scenarios:
        result = await analyze("\n".join(line["text"] for line in sc["lines"]), use_llm=False)
        if result["level"] != "low":
            store.save_report(result)
            saved += 1
    print(f"Saved {saved} demo reports to {store.settings.db_path}")


if __name__ == "__main__":
    asyncio.run(main())
