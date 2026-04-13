from __future__ import annotations

import json

import httpx


def main() -> None:
    payload = {
        "model": "council-meta",
        "messages": [
            {
                "role": "user",
                "content": (
                    "Review this delivery draft and improve it. "
                    "Context: Mid-sized logistics company, low automation, high compliance pressure."
                ),
            }
        ],
        "temperature": 0.2,
        "max_tokens": 700,
    }

    with httpx.Client(timeout=90.0) as client:
        response = client.post("http://localhost:4000/v1/chat/completions", json=payload)
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    main()
