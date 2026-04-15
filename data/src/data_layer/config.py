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
    email_source: str = os.getenv("EMAIL_SOURCE", "mock")
    imap_host: str = os.getenv("IMAP_HOST", "")
    imap_port: int = int(os.getenv("IMAP_PORT", "993"))
    imap_username: str = os.getenv("IMAP_USERNAME", "")
    imap_password: str = os.getenv("IMAP_PASSWORD", "")
    graph_tenant_id: str = os.getenv("GRAPH_TENANT_ID", "")
    graph_client_id: str = os.getenv("GRAPH_CLIENT_ID", "")
    graph_client_secret: str = os.getenv("GRAPH_CLIENT_SECRET", "")
    graph_mailbox_user: str = os.getenv("GRAPH_MAILBOX_USER", "")


settings = Settings()
