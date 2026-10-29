"""Evaluate ScamShield on the scripted test calls.

    python -m eval.run_eval            # rules engine only (offline, no key needed)
    python -m eval.run_eval --llm      # Gemini + rules (needs GEMINI_API_KEY)

For each call it reports the final verdict, and how far into the call the first
"high risk" warning fired (replaying the call line by line, as the live app does).
Writes eval/results.csv and eval/RESULTS.md.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
from pathlib import Path

from app.analyzer import analyze
from app.config import DATA_DIR, settings

OUT_DIR = Path(__file__).resolve().parent
WORDS_PER_SECOND = 2.5  # typical conversational speaking rate


async def evaluate(use_llm: bool, progressive_llm: bool = False) -> list[dict]:
    scenarios = json.loads((DATA_DIR / "scenarios.json").read_text(encoding="utf-8"))["scenarios"]
    rows = []
    for sc in scenarios:
        texts = [line["text"] for line in sc["lines"]]
        final = await analyze("\n".join(texts), use_llm=use_llm)

        first_line = first_seconds = None
        words = 0
        for i, text in enumerate(texts, start=1):
            words += len(text.split())
            # Progressive replay: LLM per line would burn free-tier quota, so it is opt-in.
            partial = await analyze("\n".join(texts[:i]), use_llm=use_llm and progressive_llm)
            if partial["level"] == "high":
                first_line, first_seconds = i, round(words / WORDS_PER_SECOND)
                break

        flagged = final["level"] == "high"
        correct = flagged if sc["expected"] == "scam" else not flagged
        rows.append(
            {
                "call": sc["title_en"],
                "id": sc["id"],
                "expected": sc["expected"],
                "level": final["level"],
                "risk": final["risk"],
                "scam_type": final["scam_type"] or "",
                "tactics": " ".join(t["id"] for t in final["tactics"]),
                "registry_hit": final["registry_hit"],
                "warning_at_line": first_line or "",
                "warning_after_s": first_seconds or "",
                "lines": len(texts),
                "correct": correct,
                "engine": final["engine"],
            }
        )
    return rows


def write_outputs(rows: list[dict], engine: str) -> str:
    with open(OUT_DIR / "results.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    scams = [r for r in rows if r["expected"] == "scam"]
    legit = [r for r in rows if r["expected"] == "legit"]
    caught = sum(r["level"] == "high" for r in scams)
    false_alarms = sum(r["level"] == "high" for r in legit)
    cautions = sum(r["level"] == "caution" for r in legit)
    times = [r["warning_after_s"] for r in scams if r["warning_after_s"] != ""]
    avg_t = round(sum(times) / len(times)) if times else None

    lines = [
        f"# Evaluation results ({engine})",
        "",
        f"- Scam calls flagged high-risk: **{caught} of {len(scams)}**",
        f"- False alarms on legitimate calls: **{false_alarms} of {len(legit)}**"
        + (f" ({cautions} shown as 'be careful')" if cautions else ""),
        f"- Average time to first warning on scam calls: **~{avg_t} s** of speech"
        + f" (at {WORDS_PER_SECOND} words/s)" if avg_t is not None else "",
        "",
        "| Call | Expected | ScamShield verdict | Risk | Scam type | Warning after | Correct |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        when = f"line {r['warning_at_line']}/{r['lines']} (~{r['warning_after_s']} s)" if r["warning_at_line"] else "—"
        lines.append(
            f"| {r['call']} | {r['expected']} | {r['level']} | {r['risk']:.2f} | {r['scam_type'] or '—'} | {when} | "
            f"{'yes' if r['correct'] else 'NO'} |"
        )
    lines += [
        "",
        "Calls are scripted by the team (see `app/data/scenarios.json`) from patterns in PDRM/NSRC advisories, so "
        "this is a functional test, not a field accuracy claim. 'Caution' on a legitimate call (e.g. a family member "
        "asking for money) is counted as correct: the app says 'be careful', not 'scam'.",
    ]
    md = "\n".join(lines) + "\n"
    (OUT_DIR / "RESULTS.md").write_text(md, encoding="utf-8")
    return md


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm", action="store_true", help="use Gemini + rules (needs GEMINI_API_KEY)")
    parser.add_argument("--progressive-llm", action="store_true", help="also call Gemini on every partial transcript")
    args = parser.parse_args()
    if args.llm and not settings.llm_enabled:
        raise SystemExit("--llm needs GEMINI_API_KEY in the environment or .env")
    results = asyncio.run(evaluate(args.llm, args.progressive_llm))
    print(write_outputs(results, "Gemini + rules" if args.llm else "rules engine only"))
