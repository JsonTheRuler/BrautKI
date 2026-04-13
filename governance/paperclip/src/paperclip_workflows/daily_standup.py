from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx
import yaml


def load_org_config() -> dict[str, Any]:
    config_path = Path(__file__).resolve().parents[2] / "paperclip-org.yaml"
    return yaml.safe_load(config_path.read_text(encoding="utf-8"))


def call_role_endpoint(endpoint: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    with httpx.Client(timeout=45.0) as client:
        response = client.post(endpoint, json=(payload or {}))
        response.raise_for_status()
        return response.json()


def build_summary(role_outputs: list[dict[str, Any]]) -> str:
    lines = ["# AI Ready Daily Standup", ""]
    for item in role_outputs:
        lines.append(f"## {item['display_name']}")
        lines.append(f"- Role ID: {item['role_id']}")
        lines.append(f"- Endpoint: {item['endpoint']}")
        lines.append("- Output:")
        lines.append(f"```json\n{json.dumps(item['output'], ensure_ascii=True, indent=2)}\n```")
        lines.append("")
    return "\n".join(lines)


def send_notifications(summary_markdown: str) -> None:
    slack_webhook = os.getenv("STANDUP_SLACK_WEBHOOK_URL", "").strip()
    email_webhook = os.getenv("STANDUP_EMAIL_WEBHOOK_URL", "").strip()

    if slack_webhook:
        with httpx.Client(timeout=20.0) as client:
            client.post(slack_webhook, json={"text": summary_markdown}).raise_for_status()

    if email_webhook:
        payload = {
            "subject": "AI Ready Daily Standup",
            "body_markdown": summary_markdown,
            "recipients": os.getenv("STANDUP_EMAIL_RECIPIENTS", "hello@aiready.no").split(","),
        }
        with httpx.Client(timeout=20.0) as client:
            client.post(email_webhook, json=payload).raise_for_status()


def main() -> None:
    config = load_org_config()
    roles = config.get("roles", [])
    outputs: list[dict[str, Any]] = []

    for role in roles:
        endpoint = role["endpoint"]
        payload = role.get("payload_template")
        try:
            output = call_role_endpoint(endpoint, payload=payload)
        except Exception as exc:
            output = {"error": str(exc)}
        outputs.append(
            {
                "role_id": role["role_id"],
                "display_name": role["display_name"],
                "endpoint": endpoint,
                "output": output,
            }
        )

    summary = build_summary(outputs)
    print(summary)
    send_notifications(summary)


if __name__ == "__main__":
    main()
