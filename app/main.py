"""ScamShield MY — FastAPI entry point.

Run:  uvicorn app.main:app --reload    then open http://localhost:8000
"""

from __future__ import annotations

import json
import logging

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import store
from .analyzer import analyze, get_client
from .config import DATA_DIR, STATIC_DIR, settings
from .gemini import GeminiError
from .registry import lookup

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app = FastAPI(title="ScamShield MY", version="1.0.0", description="Real-time phone-scam co-pilot for seniors.")

MAX_AUDIO_BYTES = 4 * 1024 * 1024


class AnalyzeRequest(BaseModel):
    transcript: str = Field(..., max_length=20000)
    use_llm: bool = True


class ReportRequest(BaseModel):
    analysis: dict


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "llm_enabled": settings.llm_enabled,
        "model": settings.gemini_model if settings.llm_enabled else None,
        "registry_mode": settings.registry_mode,
    }


@app.get("/api/scenarios")
def scenarios() -> list[dict]:
    return json.loads((DATA_DIR / "scenarios.json").read_text(encoding="utf-8"))["scenarios"]


@app.post("/api/analyze")
async def analyze_endpoint(req: AnalyzeRequest) -> dict:
    return await analyze(req.transcript, use_llm=req.use_llm)


@app.post("/api/transcribe")
async def transcribe(audio: UploadFile = File(...)) -> dict:
    client = get_client()
    if client is None:
        raise HTTPException(503, "Gemini transcription needs GEMINI_API_KEY. Use browser speech or demo mode instead.")
    data = await audio.read()
    if not data:
        return {"text": ""}
    if len(data) > MAX_AUDIO_BYTES:
        raise HTTPException(413, "Audio chunk too large; send chunks of a few seconds.")
    mime = (audio.content_type or "audio/webm").split(";")[0]
    try:
        text = await client.transcribe(data, mime)
    except GeminiError as exc:
        raise HTTPException(502, f"Transcription failed: {exc}") from exc
    return {"text": text}


@app.get("/api/lookup")
def lookup_endpoint(number: str = Query(..., min_length=6, max_length=32), kind: str = Query("account", pattern="^(phone|account)$")) -> dict:
    return lookup(number, kind)


@app.post("/api/report")
def report(req: ReportRequest) -> dict:
    return {"id": store.save_report(req.analysis)}


@app.get("/api/stats")
def stats() -> dict:
    return store.stats()


@app.get("/dashboard")
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "dashboard.html")


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
