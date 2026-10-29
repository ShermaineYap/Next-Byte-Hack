"""Mule-account / scam-number lookup.

PDRM's Semak Mule portal (https://semakmule.rmp.gov.my) has no public API and is
protected against automated queries, so this prototype never scrapes it. Two modes:

* ``demo`` – checks a small bundled sample registry (``data/demo_registry.json``)
  containing the fictitious numbers used in the demo calls. Every result is
  labelled ``source: "demo"`` and the UI says so.
* ``link`` – returns no verdict, only a deep link so the user can check the
  number on the official portal themselves.

A production version would plug an official data-sharing feed (e.g. from NSRC)
in behind the same ``lookup`` function.
"""

from __future__ import annotations

import json
from functools import lru_cache

from .config import DATA_DIR, settings
from .entities import normalise_phone

SEMAK_MULE_URL = "https://semakmule.rmp.gov.my/"


@lru_cache(maxsize=1)
def _demo_registry() -> dict[str, dict]:
    raw = json.loads((DATA_DIR / "demo_registry.json").read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for entry in raw["entries"]:
        key = entry["number"]
        key = normalise_phone(key) if entry["kind"] == "phone" else "".join(c for c in key if c.isdigit())
        out[key] = entry
    return out


def lookup(number: str, kind: str) -> dict:
    key = normalise_phone(number) if kind == "phone" else "".join(c for c in number if c.isdigit())
    result = {
        "number": key,
        "kind": kind,
        "status": "unchecked",
        "reports": 0,
        "source": settings.registry_mode,
        "check_url": SEMAK_MULE_URL,
        "note": "Check this number yourself on PDRM Semak Mule.",
    }
    if settings.registry_mode != "demo":
        return result

    entry = _demo_registry().get(key)
    if entry:
        result.update(
            status="reported",
            reports=entry["reports"],
            note=f"DEMO DATA: {entry['reports']} reports ({entry['category']}). Verify on Semak Mule.",
        )
    else:
        result.update(status="not_found", note="DEMO DATA: not in the sample registry. Verify on Semak Mule.")
    return result


def lookup_entities(entities: dict) -> list[dict]:
    results = [lookup(p, "phone") for p in entities.get("phones", [])]
    results += [lookup(a, "account") for a in entities.get("accounts", [])]
    return results
