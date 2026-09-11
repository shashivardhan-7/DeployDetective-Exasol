from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

from agent.investigator import Investigator  # noqa: E402
from agent.tools import ExasolTools  # noqa: E402

app = FastAPI(title="Deploy Detective", version="2.0.0")


class InvestigateRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/static/{filename}")
def static_files(filename: str):
    file = ROOT / "static" / filename
    if not file.exists() or not file.is_file():
        raise HTTPException(status_code=404, detail="static file not found")
    return FileResponse(file)


@app.get("/api/health")
def health():
    return ExasolTools().health()


@app.post("/api/investigate")
def investigate(payload: InvestigateRequest):
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    try:
        return Investigator().run(message)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Investigation could not complete. Check Exasol connectivity and run RUN_GUIDE.md. " + str(exc),
        ) from exc
