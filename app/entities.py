"""Pull phone numbers, bank account numbers and ringgit amounts out of a transcript."""

from __future__ import annotations

import re

# Malaysian mobiles: 01X-XXX XXXX / 01X-XXXX XXXX, optional +6 / 6 prefix.
_MOBILE = re.compile(r"(?<!\d)(?:\+?6)?01[0-9][\s-]?\d{3,4}[\s-]?\d{4}(?!\d)")
# Landlines: 03-XXXX XXXX (KL/Selangor) and 0[4-9]-XXX XXXX elsewhere.
_LANDLINE = re.compile(r"(?<!\d)(?:\+?6)?0[3-9][\s-]?\d{3,4}[\s-]?\d{4}(?!\d)")
# Account numbers: 10–16 digits, possibly grouped with spaces or dashes.
_ACCOUNT = re.compile(r"(?<!\d)\d(?:[\s-]?\d){9,15}(?!\d)")
_AMOUNT = re.compile(
    r"\b(?:rm|myr)\s?(\d{1,3}(?:[,\s]\d{3})+|\d+)(?:\.(\d{1,2}))?\s?(k|ribu|thousand|juta|million|mil)?\b",
    re.IGNORECASE,
)
_MULTIPLIER = {"k": 1_000, "ribu": 1_000, "thousand": 1_000, "juta": 1_000_000, "million": 1_000_000, "mil": 1_000_000}


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s)


def normalise_phone(raw: str) -> str:
    d = _digits(raw)
    if d.startswith("60"):
        d = d[1:]
    return d


def extract_entities(text: str) -> dict:
    text = text or ""
    phones: list[str] = []
    taken: list[tuple[int, int]] = []

    for pattern in (_MOBILE, _LANDLINE):
        for m in pattern.finditer(text):
            num = normalise_phone(m.group(0))
            if num not in phones:
                phones.append(num)
            taken.append(m.span())

    accounts: list[str] = []
    for m in _ACCOUNT.finditer(text):
        if any(s <= m.start() < e or s < m.end() <= e for s, e in taken):
            continue
        num = _digits(m.group(0))
        if num not in accounts and num not in phones:
            accounts.append(num)

    amounts: list[float] = []
    for m in _AMOUNT.finditer(text):
        whole = float(re.sub(r"[,\s]", "", m.group(1)))
        cents = float("0." + m.group(2)) if m.group(2) else 0.0
        mult = _MULTIPLIER.get((m.group(3) or "").lower(), 1)
        value = (whole + cents) * mult
        if value not in amounts:
            amounts.append(value)

    return {"phones": phones, "accounts": accounts, "amounts_rm": amounts}
