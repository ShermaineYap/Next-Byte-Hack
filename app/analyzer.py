"""Combine the rule floor, the LLM analyst and the registry lookup into one verdict."""

from __future__ import annotations

import logging

from .config import settings
from .entities import extract_entities
from .gemini import GeminiClient, GeminiError
from .registry import lookup_entities
from .rules import ADVICE, TACTIC_BY_ID, analyze_rules, level_for

log = logging.getLogger("scamshield.analyzer")

MAX_CHARS = 6000  # analyse the most recent part of very long calls
REGISTRY_HIT_FLOOR = 0.8  # a number already reported as a mule account is a strong signal

_client: GeminiClient | None = None


def get_client() -> GeminiClient | None:
    global _client
    if not settings.llm_enabled:
        return None
    if _client is None:
        _client = GeminiClient(
            settings.gemini_api_key, settings.gemini_model, settings.gemini_audio_model, settings.gemini_timeout_s
        )
    return _client


def set_client(client: GeminiClient | None) -> None:
    """Used by tests to inject a client with a mocked transport."""
    global _client
    _client = client


async def analyze(transcript: str, use_llm: bool = True, client: GeminiClient | None = None) -> dict:
    transcript = (transcript or "")[-MAX_CHARS:]
    rules = analyze_rules(transcript)
    entities = extract_entities(transcript)
    lookups = lookup_entities(entities)

    llm: dict | None = None
    llm_error: str | None = None
    client = client or (get_client() if use_llm else None)
    if use_llm and client and len(transcript.strip()) >= 20:
        try:
            llm = await client.analyze(transcript)
        except GeminiError as exc:
            llm_error = str(exc)
            log.warning("Gemini analysis failed, using rules only: %s", exc)

    # Merge tactics from both engines, keeping evidence from each.
    merged: dict[str, dict] = {}
    for hit in rules.tactics:
        merged[hit.id] = {"id": hit.id, "label_en": hit.label_en, "label_ms": hit.label_ms, "evidence": list(hit.evidence), "by": ["rules"]}
    for item in (llm or {}).get("tactics", []):
        t = TACTIC_BY_ID[item["id"]]
        entry = merged.setdefault(item["id"], {"id": t.id, "label_en": t.label_en, "label_ms": t.label_ms, "evidence": [], "by": []})
        entry["by"].append("gemini")
        for ev in item["evidence"]:
            if ev.lower() not in (e.lower() for e in entry["evidence"]):
                entry["evidence"].append(ev)

    registry_hit = any(r["status"] == "reported" for r in lookups)
    llm_risk = llm["risk"] if llm else None
    risk = max(rules.risk, llm_risk or 0.0)
    if registry_hit:
        risk = max(risk, REGISTRY_HIT_FLOOR)
    level = level_for(risk)

    scam_type = scam_type_ms = None
    if level != "low":
        scam_type = (llm or {}).get("scam_type") or rules.scam_type
        scam_type_ms = rules.scam_type_ms if (rules.scam_type and scam_type == rules.scam_type) else scam_type
        if not scam_type and registry_hit:
            scam_type, scam_type_ms = "Reported mule account", "Akaun keldai yang dilaporkan"

    if llm and llm.get("explanation_en"):
        explanation_en, explanation_ms = llm["explanation_en"], llm["explanation_ms"]
    elif merged:
        explanation_en = "Signs found: " + "; ".join(t["label_en"].lower() for t in merged.values()) + "."
        explanation_ms = "Tanda dikesan: " + "; ".join(t["label_ms"].lower() for t in merged.values()) + "."
    else:
        explanation_en, explanation_ms = "No scam signs found yet.", "Belum ada tanda penipuan."

    return {
        "risk": round(risk, 3),
        "level": level,
        "scam_type": scam_type,
        "scam_type_ms": scam_type_ms,
        "tactics": list(merged.values()),
        "entities": entities,
        "lookups": lookups,
        "registry_hit": registry_hit,
        "explanation_en": explanation_en,
        "explanation_ms": explanation_ms,
        "advice_en": ADVICE[level]["en"],
        "advice_ms": ADVICE[level]["ms"],
        "engine": "gemini+rules" if llm else "rules",
        "rule_risk": round(rules.risk, 3),
        "llm_risk": None if llm_risk is None else round(llm_risk, 3),
        "llm_error": llm_error,
        "negated": rules.negated,
    }
