from __future__ import annotations

import hashlib
import json
from typing import Any

import httpx

from .config import settings


def _deterministic_fallback_embedding(text: str, dimensions: int) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    repeated = (digest * ((dimensions // len(digest)) + 1))[:dimensions]
    return [round((b / 255.0) * 2 - 1, 6) for b in repeated]


def fetch_embedding_via_gateway(text: str) -> list[float]:
    """
    Fetch embedding via gateway alias. Current gateway only exposes chat completions,
    so we request a strict JSON float array. If parsing fails, fall back deterministically.
    """
    payload: dict[str, Any] = {
        "model": settings.embedding_alias,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an embedding bridge. Return ONLY a JSON array of "
                    f"{settings.embedding_dimensions} floats in range [-1,1]."
                ),
            },
            {"role": "user", "content": text},
        ],
        "temperature": 0.0,
        "max_tokens": 300,
    }

    url = f"{settings.gateway_url.rstrip('/')}/v1/chat/completions"
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            if (
                isinstance(parsed, list)
                and len(parsed) == settings.embedding_dimensions
                and all(isinstance(x, (int, float)) for x in parsed)
            ):
                return [float(x) for x in parsed]
    except Exception:
        pass

    return _deterministic_fallback_embedding(text, settings.embedding_dimensions)
