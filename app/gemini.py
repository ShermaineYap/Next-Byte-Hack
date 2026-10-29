"""Thin async client for the Gemini REST API (no SDK, so model renames never break imports).

Two jobs:
* ``transcribe`` – speech-to-text for a short audio chunk (Malay/English code-switching).
* ``analyze``    – structured scam-tactic analysis of a transcript, returned as JSON
                   constrained by a response schema.
"""

from __future__ import annotations

import base64
import json
import logging
import os

import httpx

from .rules import TACTICS

log = logging.getLogger("scamshield.gemini")

API_ROOT = os.getenv("GEMINI_API_ROOT", "https://generativelanguage.googleapis.com/v1beta/models").rstrip("/")
TACTIC_IDS = [t.id for t in TACTICS]

ANALYSIS_SYSTEM_PROMPT = f"""You are ScamShield, a scam-call analyst protecting elderly people in Malaysia.
You receive a live, possibly partial and imperfect transcript of a phone call. Speakers mix Malay,
English and Manglish. Decide how likely it is that the CALLER is running a scam.

Known Malaysian phone-scam patterns (PDRM / NSRC advisories):
- Caller poses as police (often "Bukit Aman"), LHDN, Bank Negara, a court, customs or a courier.
- Claims your IC, phone number or account is linked to money laundering, drugs or a parcel.
- Threatens arrest, a warrant or frozen accounts; demands action within hours.
- Tells you to keep it secret, not tell family, stay on the line or go to a room alone.
- Asks you to move savings to a "safe account" / "akaun selamat", buy crypto or gift cards.
- Asks for OTP / TAC codes, PINs, card numbers or online-banking logins.
- Asks you to install an app (AnyDesk, APK) or click a link.
- Promises prizes or guaranteed investment returns, then asks for a fee.

Legitimate calls exist too: real banks say they will NEVER ask for a TAC or a transfer; clinics confirm
appointments; couriers ask for directions; family and friends ask for favours. Do not flag a call just
because it mentions a bank, police or money. Judge the caller's intent.

Tactic ids you may use: {", ".join(TACTIC_IDS)}.
For each tactic, quote evidence as EXACT short substrings copied from the transcript (2-8 words).
risk is your probability (0 to 1) that this is a scam. verdict: "scam" if risk >= 0.7,
"suspicious" if 0.35 <= risk < 0.7, else "safe". scam_type is a short English name (e.g.
"Police impersonation (Macau scam)") or "" if safe. Explanations are one plain sentence an elderly
person can understand, in English and in Bahasa Malaysia."""

ANALYSIS_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "risk": {"type": "NUMBER"},
        "verdict": {"type": "STRING", "enum": ["scam", "suspicious", "safe"]},
        "scam_type": {"type": "STRING"},
        "tactics": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING", "enum": TACTIC_IDS},
                    "evidence": {"type": "ARRAY", "items": {"type": "STRING"}},
                },
                "required": ["id", "evidence"],
            },
        },
        "explanation_en": {"type": "STRING"},
        "explanation_ms": {"type": "STRING"},
    },
    "required": ["risk", "verdict", "tactics", "explanation_en", "explanation_ms"],
}

TRANSCRIBE_PROMPT = (
    "Transcribe the speech in this audio verbatim. It is part of a phone call in Malaysia; speakers may mix "
    "Malay and English. Write numbers as digits. Output only the transcript text with no speaker labels, "
    "timestamps or commentary. If there is no intelligible speech, output nothing."
)


class GeminiError(RuntimeError):
    pass


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        audio_model: str | None = None,
        timeout_s: float = 12.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.audio_model = audio_model or model
        self.timeout_s = timeout_s
        self._transport = transport

    async def _generate(self, model: str, body: dict) -> str:
        url = f"{API_ROOT}/{model}:generateContent"
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_s, transport=self._transport) as client:
                resp = await client.post(url, headers=headers, json=body)
        except httpx.HTTPError as exc:
            raise GeminiError(f"network error: {exc}") from exc
        if resp.status_code != 200:
            raise GeminiError(f"HTTP {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        try:
            parts = data["candidates"][0]["content"]["parts"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GeminiError(f"unexpected response: {json.dumps(data)[:300]}") from exc
        return "".join(p.get("text", "") for p in parts if not p.get("thought"))

    async def analyze(self, transcript: str) -> dict:
        body = {
            "systemInstruction": {"parts": [{"text": ANALYSIS_SYSTEM_PROMPT}]},
            "contents": [{"role": "user", "parts": [{"text": f"Transcript so far:\n\"\"\"\n{transcript}\n\"\"\""}]}],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
                "responseSchema": ANALYSIS_SCHEMA,
            },
        }
        text = await self._generate(self.model, body)
        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            raise GeminiError(f"model did not return JSON: {text[:200]}") from exc
        return sanitize_analysis(raw, transcript)

    async def transcribe(self, audio: bytes, mime_type: str) -> str:
        body = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"inlineData": {"mimeType": mime_type, "data": base64.b64encode(audio).decode()}},
                        {"text": TRANSCRIBE_PROMPT},
                    ],
                }
            ],
            "generationConfig": {"temperature": 0.0},
        }
        return (await self._generate(self.audio_model, body)).strip()


def sanitize_analysis(raw: dict, transcript: str) -> dict:
    """Clamp numbers, drop unknown tactics and any 'evidence' the model invented."""
    lower = transcript.lower()
    try:
        risk = float(raw.get("risk", 0))
    except (TypeError, ValueError):
        risk = 0.0
    risk = max(0.0, min(1.0, risk))

    tactics = []
    for item in raw.get("tactics") or []:
        tid = item.get("id") if isinstance(item, dict) else None
        if tid not in TACTIC_IDS:
            continue
        evidence = [e.strip() for e in item.get("evidence") or [] if isinstance(e, str) and e.strip()]
        evidence = [e for e in evidence if e.lower() in lower][:6]
        tactics.append({"id": tid, "evidence": evidence})

    verdict = raw.get("verdict")
    if verdict not in ("scam", "suspicious", "safe"):
        verdict = "scam" if risk >= 0.7 else "suspicious" if risk >= 0.35 else "safe"
    return {
        "risk": risk,
        "verdict": verdict,
        "scam_type": (raw.get("scam_type") or "").strip() or None,
        "tactics": tactics,
        "explanation_en": (raw.get("explanation_en") or "").strip(),
        "explanation_ms": (raw.get("explanation_ms") or "").strip(),
    }
