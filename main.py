

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Literal

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from templates import SYSTEM_PROMPT, build_prompt

# ── Load environment ────
load_dotenv()

LLM_PROVIDER  = os.getenv("LLM_PROVIDER", "anthropic").lower()
LLM_API_KEY   = os.getenv("LLM_API_KEY", "")

ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
OPENAI_MODEL    = os.getenv("OPENAI_MODEL",    "gpt-4o-mini")
GROQ_MODEL      = os.getenv("GROQ_MODEL",      "qwen/qwen3.8-27b")

# ── FastAPI app ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Script Bench",
    description="Turn any idea into a short-form video script using AI",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ── Request / Response models ──────────────────────────────────────────────────
class ScriptRequest(BaseModel):
    niche: str = Field(..., min_length=1, max_length=100, examples=["fitness"])
    topic: str = Field(..., min_length=5, max_length=300, examples=["3 morning habits that changed my life"])
    target_seconds: Literal[30, 45, 60] = Field(30, examples=[30])

    @field_validator("niche", "topic", mode="before")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip()


class ScriptResponse(BaseModel):
    hook: str
    body: str
    cta: str
    style_note: str
    estimated_seconds: int
    provider: str


# ── LLM caller helpers ─────────────────────────────────────────────────────────
async def call_anthropic(user_prompt: str) -> dict:
    if not LLM_API_KEY:
        raise HTTPException(502, "LLM_API_KEY not set in .env")

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": LLM_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": ANTHROPIC_MODEL,
                "max_tokens": 800,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user_prompt}],
            },
        )

    if resp.status_code != 200:
        raise HTTPException(502, f"Anthropic error {resp.status_code}: {resp.text}")

    raw = resp.json()["content"][0]["text"]
    return json.loads(raw)


async def call_openai(user_prompt: str) -> dict:
    if not LLM_API_KEY:
        raise HTTPException(502, "LLM_API_KEY not set in .env")

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENAI_MODEL,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            },
        )

    if resp.status_code != 200:
        raise HTTPException(502, f"OpenAI error {resp.status_code}: {resp.text}")

    raw = resp.json()["choices"][0]["message"]["content"]
    return json.loads(raw)


async def call_groq(user_prompt: str) -> dict:
    if not LLM_API_KEY:
        raise HTTPException(502, "LLM_API_KEY not set in .env")

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            },
        )

    if resp.status_code != 200:
        raise HTTPException(502, f"Groq error {resp.status_code}: {resp.text}")

    raw = resp.json()["choices"][0]["message"]["content"]
    return json.loads(raw)


PROVIDERS = {
    "anthropic": call_anthropic,
    "openai":    call_openai,
    "groq":      call_groq,
}


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def serve_ui():
    return FileResponse(static_dir / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok", "provider": LLM_PROVIDER, "key_set": bool(LLM_API_KEY)}


@app.post("/generate", response_model=ScriptResponse)
async def generate_script(req: ScriptRequest):
    caller = PROVIDERS.get(LLM_PROVIDER)
    if not caller:
        raise HTTPException(400, f"Unknown LLM_PROVIDER '{LLM_PROVIDER}'. Use: anthropic | openai | groq")

    user_prompt = build_prompt(req.niche, req.topic, req.target_seconds)

    try:
        result = await caller(user_prompt)
    except json.JSONDecodeError as e:
        raise HTTPException(502, f"LLM returned invalid JSON: {e}")

    return ScriptResponse(**result, provider=LLM_PROVIDER)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
