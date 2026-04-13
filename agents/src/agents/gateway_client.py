from __future__ import annotations

import json
from typing import Any

import httpx

from .config import settings


def generate_structured_json(prompt: str, model_alias: str | None = None) -> dict[str, Any]:
    payload = {
        "model": model_alias or settings.reasoning_alias,
        "messages": [
            {"role": "system", "content": "Return valid JSON only. Do not wrap in markdown."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 1500,
    }
    with httpx.Client(timeout=45.0) as client:
        response = client.post(f"{settings.gateway_url.rstrip('/')}/v1/chat/completions", json=payload)
        response.raise_for_status()
        body = response.json()
        content = body["choices"][0]["message"]["content"]
    return json.loads(content)
