from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from uuid import uuid4

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException

app = FastAPI(title="AI Ready Local Model Wrapper", version="0.1.0")

MODE = os.getenv("WRAPPER_MODE", "gemma").strip().lower()
PORT = int(os.getenv("WRAPPER_PORT", "11500"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
WRAPPER_MODEL = os.getenv("WRAPPER_MODEL", "gemma3:27b")
KARPATHY_BINARY_PATH = os.getenv("KARPATHY_BINARY_PATH", "")
KARPATHY_MODEL_PATH = os.getenv("KARPATHY_MODEL_PATH", "")


def _openai_style(content: str, model: str) -> dict:
    return {
        "id": f"local-{uuid4()}",
        "object": "chat.completion",
        "created": int(datetime.now(tz=timezone.utc).timestamp()),
        "model": model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


def _join_messages(messages: list[dict]) -> str:
    return "\n".join(f"{m.get('role','user')}: {m.get('content','')}" for m in messages)


def _gemma_response(messages: list[dict], model: str) -> str:
    prompt = _join_messages(messages)
    selected_model = model or WRAPPER_MODEL
    payload = {"model": selected_model, "prompt": prompt, "stream": False}
    with httpx.Client(timeout=120.0) as client:
        response = client.post(f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate", json=payload)
        if response.status_code == 404:
            chat_payload = {
                "model": selected_model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            }
            response = client.post(f"{OLLAMA_BASE_URL.rstrip('/')}/v1/chat/completions", json=chat_payload)
            response.raise_for_status()
            body = response.json()
            return body.get("choices", [{}])[0].get("message", {}).get("content", "")

        response.raise_for_status()
        body = response.json()
        return body.get("response", "")


def _karpathy_response(messages: list[dict]) -> str:
    prompt = _join_messages(messages)

    # If llm.c runner is present, call it; otherwise deterministic fallback.
    if KARPATHY_BINARY_PATH and KARPATHY_MODEL_PATH and os.path.exists(KARPATHY_BINARY_PATH):
        cmd = [KARPATHY_BINARY_PATH, "-m", KARPATHY_MODEL_PATH, "-p", prompt, "-n", "128"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
            return result.stdout.strip()
        except Exception as exc:
            return f"Karpathy runner error: {exc}"

    return (
        "Karpathy wrapper fallback: style-normalized response.\n"
        f"Input summary: {prompt[:300]}"
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": MODE}


@app.post("/v1/chat/completions")
def chat_completions(payload: dict) -> dict:
    messages = payload.get("messages", [])
    model = payload.get("model", WRAPPER_MODEL)

    if not isinstance(messages, list):
        raise HTTPException(status_code=400, detail="'messages' must be an array.")

    if MODE == "gemma":
        content = _gemma_response(messages=messages, model=model)
        return _openai_style(content=content, model=model)

    if MODE == "karpathy":
        content = _karpathy_response(messages=messages)
        return _openai_style(content=content, model="karpathy-eval")

    raise HTTPException(status_code=500, detail=f"Unsupported WRAPPER_MODE: {MODE}")


if __name__ == "__main__":
    uvicorn.run("local_models.wrapper_api:app", host="0.0.0.0", port=PORT, reload=False)
