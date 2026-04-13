from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    gateway_url: str = os.getenv("GATEWAY_URL", "http://localhost:4000")
    reasoning_alias: str = os.getenv("REASONING_MODEL_ALIAS", "reasoning-primary")
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/ai_ready"
    )
    calendar_stub_path: str = os.getenv("CALENDAR_STUB_PATH", "")
    drafts_output_path: str = os.getenv("DRAFTS_OUTPUT_PATH", "runtime/draft_replies.jsonl")
    council_alias: str = os.getenv("COUNCIL_MODEL_ALIAS", "council-meta")
    enable_council_review: bool = os.getenv("ENABLE_COUNCIL_REVIEW", "false").lower() == "true"
    internal_secure_alias: str = os.getenv("INTERNAL_SECURE_MODEL_ALIAS", "internal-secure")


settings = Settings()
