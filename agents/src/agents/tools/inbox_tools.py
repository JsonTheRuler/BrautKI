from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import create_engine, text

from agents.config import settings
from agents.schemas import CalendarEvent, EmailRecord


def get_recent_emails(limit: int = 10) -> list[EmailRecord]:
    engine = create_engine(settings.database_url, future=True, connect_args={"connect_timeout": 3})
    query = text(
        """
        SELECT id::text, from_address, to_address, subject, body
        FROM emails
        ORDER BY created_at DESC
        LIMIT :limit
        """
    )
    try:
        with engine.connect() as conn:
            rows = conn.execute(query, {"limit": limit}).mappings().all()
    except Exception:
        rows = []

    if not rows:
        return [
            EmailRecord(
                id="stub-1",
                from_address="prospect@sample.no",
                to_address="hello@aiready.no",
                subject="Need AI roadmap proposal",
                body="Can you send a proposal and timeline for an AI readiness program?",
            )
        ]
    return [EmailRecord(**row) for row in rows]


def get_calendar_events() -> list[CalendarEvent]:
    if settings.calendar_stub_path and Path(settings.calendar_stub_path).exists():
        payload = json.loads(Path(settings.calendar_stub_path).read_text(encoding="utf-8"))
        return [CalendarEvent(**event) for event in payload]

    return [
        CalendarEvent(
            title="Leadership sync",
            start_iso="2026-04-14T09:00:00+01:00",
            end_iso="2026-04-14T09:30:00+01:00",
        ),
        CalendarEvent(
            title="Client discovery block",
            start_iso="2026-04-14T13:00:00+01:00",
            end_iso="2026-04-14T14:00:00+01:00",
        ),
    ]


def save_draft_reply(email_id: str, draft_reply: str) -> None:
    output_file = Path(settings.drafts_output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {"email_id": email_id, "draft_reply": draft_reply}
    with output_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
