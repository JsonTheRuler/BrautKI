from __future__ import annotations

import json

import httpx


def main() -> None:
    payload = {"email_limit": 5}
    with httpx.Client(timeout=60.0) as client:
        response = client.post("http://localhost:8010/agents/inbox/run", json=payload)
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    main()
