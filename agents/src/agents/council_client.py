from __future__ import annotations

import json
from typing import Any

import httpx

from .config import settings


def review_with_council(report: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "model": settings.council_alias,
        "messages": [
            {
                "role": "system",
                "content": "You are a council reviewer. Return JSON with improved_report, rationale.",
            },
            {
                "role": "user",
                "content": (
                    "Review and improve this delivery report draft. "
                    f"Return JSON only.\nDraft:\n{json.dumps(report, ensure_ascii=True)}"
                ),
            },
        ],
        "temperature": 0.1,
        "max_tokens": 1200,
    }

    with httpx.Client(timeout=90.0) as client:
        response = client.post(f"{settings.gateway_url.rstrip('/')}/v1/chat/completions", json=payload)
        response.raise_for_status()
        body = response.json()
    content = body["choices"][0]["message"]["content"]

    try:
        parsed = json.loads(content)
    except Exception:
        return {
            "improved_report": report,
            "rationale": "Council output could not be parsed; returning original report.",
        }

    return parsed
