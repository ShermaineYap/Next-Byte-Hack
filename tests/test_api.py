import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app import analyzer, store
from app.gemini import GeminiClient
from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db = str(tmp_path / "test.db")
    monkeypatch.setattr(store, "_connect", lambda path=None, _orig=store._connect: _orig(db))
    analyzer.set_client(None)
    return TestClient(app)


def test_health_and_index(client):
    assert client.get("/api/health").json()["ok"] is True
    page = client.get("/")
    assert page.status_code == 200 and "ScamShield" in page.text
    assert client.get("/dashboard").status_code == 200


def test_scenarios(client):
    sc = client.get("/api/scenarios").json()
    assert len(sc) == 10 and {s["expected"] for s in sc} == {"scam", "legit"}


def test_analyze_rules_only(client):
    r = client.post("/api/analyze", json={"transcript": "Saya Sarjan Tan dari Bukit Aman. Pindahkan semua simpanan ke akaun selamat 7612 4409 8831.", "use_llm": False}).json()
    assert r["level"] == "high"
    assert r["engine"] == "rules"
    assert r["registry_hit"] is True
    assert r["lookups"][0]["status"] == "reported"
    assert "akaun selamat" in [e for t in r["tactics"] for e in t["evidence"]]


def test_transcribe_without_key_is_503(client):
    r = client.post("/api/transcribe", files={"audio": ("a.webm", b"xx", "audio/webm")})
    assert r.status_code == 503


def test_lookup_and_reports(client):
    lk = client.get("/api/lookup", params={"number": "011-2876 4410", "kind": "phone"}).json()
    assert lk["status"] == "reported" and lk["reports"] == 5
    analysis = client.post("/api/analyze", json={"transcript": "LHDN here, bank in RM12,850 now or your account will be frozen. Don't tell your family.", "use_llm": False}).json()
    assert client.post("/api/report", json={"analysis": analysis}).json()["id"] >= 1
    stats = client.get("/api/stats").json()
    assert stats["total"] == 1 and stats["levels"]["high"] == 1
    assert stats["amount_at_risk_rm"] == 12850.0


def _mock_gemini(payload: dict | None, status: int = 200) -> GeminiClient:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-goog-api-key"] == "test-key"
        body = json.loads(request.content)
        assert body["generationConfig"]["responseMimeType"] == "application/json"
        if status != 200:
            return httpx.Response(status, text="quota exceeded")
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": json.dumps(payload)}]}}]})

    return GeminiClient("test-key", "gemini-test", transport=httpx.MockTransport(handler))


async def test_llm_merges_and_drops_invented_evidence():
    llm = _mock_gemini({
        "risk": 0.93, "verdict": "scam", "scam_type": "Police impersonation (Macau scam)",
        "tactics": [{"id": "authority", "evidence": ["Bukit Aman", "a phrase that was never said"]}, {"id": "not_a_tactic", "evidence": []}],
        "explanation_en": "The caller pretends to be police.", "explanation_ms": "Pemanggil menyamar sebagai polis.",
    })
    r = await analyzer.analyze("Hello, saya dari Bukit Aman, ada kes untuk puan.", client=llm)
    assert r["engine"] == "gemini+rules"
    assert r["level"] == "high" and r["llm_risk"] == 0.93
    auth = next(t for t in r["tactics"] if t["id"] == "authority")
    assert "a phrase that was never said" not in auth["evidence"]
    assert all(t["id"] != "not_a_tactic" for t in r["tactics"])
    assert r["explanation_en"] == "The caller pretends to be police."


async def test_llm_failure_falls_back_to_rules():
    r = await analyzer.analyze("Please read me the TAC code now, it expires in 2 minutes.", client=_mock_gemini(None, status=429))
    assert r["engine"] == "rules"
    assert r["llm_error"] and "429" in r["llm_error"]
    assert r["level"] == "high"
