import json

import pytest

from app.config import DATA_DIR
from app.entities import extract_entities
from app.rules import analyze_rules, level_for

SCENARIOS = json.loads((DATA_DIR / "scenarios.json").read_text(encoding="utf-8"))["scenarios"]


def _text(sc):
    return "\n".join(line["text"] for line in sc["lines"])


@pytest.mark.parametrize("sc", [s for s in SCENARIOS if s["expected"] == "scam"], ids=lambda s: s["id"])
def test_scam_calls_reach_high(sc):
    assert analyze_rules(_text(sc)).level == "high"


@pytest.mark.parametrize("sc", [s for s in SCENARIOS if s["expected"] == "legit"], ids=lambda s: s["id"])
def test_legit_calls_never_high(sc):
    assert analyze_rules(_text(sc)).level != "high"


def test_negated_requests_are_ignored():
    r = analyze_rules("Maybank will never ask you for your OTP, PIN or password, and will never ask you to transfer money.")
    assert r.level == "low"
    assert "OTP" in r.negated and "PIN" in r.negated


def test_reassurance_is_not_negation():
    # "Jangan risau" (don't worry) must not cancel the transfer request that follows.
    r = analyze_rules("Jangan risau, pindahkan semua wang ke akaun selamat sekarang.")
    assert any(t.id == "money_transfer" for t in r.tactics)


def test_manglish_tac_request():
    r = analyze_rules("Aunty just read the TAC to me quickly, the code expire in 2 minutes")
    ids = {t.id for t in r.tactics}
    assert {"credentials", "threat_urgency"} <= ids
    assert r.level == "high"


def test_empty_transcript():
    r = analyze_rules("")
    assert r.risk == 0 and r.level == "low" and r.tactics == []


def test_levels():
    assert level_for(0.1) == "low"
    assert level_for(0.5) == "caution"
    assert level_for(0.7) == "high"


def test_entities():
    e = extract_entities("Call 011-2876 4410 or +6012 345 6789, bank in RM12,850 to 5140 2267 9031. Also RM5k.")
    assert e["phones"] == ["01128764410", "0123456789"]
    assert e["accounts"] == ["514022679031"]
    assert 12850.0 in e["amounts_rm"] and 5000.0 in e["amounts_rm"]
