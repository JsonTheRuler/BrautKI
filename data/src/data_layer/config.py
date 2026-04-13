from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/ai_ready"
    )
    gateway_url: str = os.getenv("GATEWAY_URL", "http://localhost:4000")
    embedding_alias: str = os.getenv("EMBEDDING_MODEL_ALIAS", "fast-cheap")
    embedding_dimensions: int = int(os.getenv("EMBEDDING_DIMENSIONS", "16"))


settings = Settings()
