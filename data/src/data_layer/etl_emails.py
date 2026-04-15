from __future__ import annotations

from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .connectors.graph_connector import ConnectorEmail as GraphEmail
from .connectors.graph_connector import fetch_emails_graph
from .connectors.imap_connector import ConnectorEmail as ImapEmail
from .connectors.imap_connector import fetch_emails_imap
from .connectors.mock_connector import ConnectorEmail as MockEmail
from .connectors.mock_connector import fetch_emails_mock
from .db import SessionLocal
from .gateway_client import fetch_embedding_via_gateway
from .models import Document, DocumentEmbedding, Email


IncomingEmail = MockEmail | ImapEmail | GraphEmail


def fetch_inbox_emails() -> Iterable[IncomingEmail]:
    source = settings.email_source.lower().strip()
    if source == "imap":
        return fetch_emails_imap()
    if source == "graph":
        return fetch_emails_graph()
    return fetch_emails_mock()


def email_exists(db: Session, provider_id: str) -> bool:
    existing = db.execute(select(Email.id).where(Email.provider_id == provider_id)).first()
    return existing is not None


def persist_email_and_document(db: Session, email: IncomingEmail) -> None:
    if email_exists(db, email.provider_id):
        return

    email_row = Email(
        from_address=email.from_address,
        to_address=email.to_address,
        provider_id=email.provider_id,
        subject=email.subject,
        body=email.body,
        labels={"status": "new"},
        metadata={"provider_id": email.provider_id, "ingest_method": "mock"},
    )
    db.add(email_row)
    db.flush()

    document_text = f"Subject: {email.subject}\n\n{email.body}"
    vector = fetch_embedding_via_gateway(document_text)
    embedding = DocumentEmbedding(
        vector=vector,
        metadata={"model_alias": "fast-cheap", "source_email_provider_id": email.provider_id},
    )
    db.add(embedding)
    db.flush()

    document = Document(
        source="email",
        content=document_text,
        metadata={"email_id": str(email_row.id), "from": email.from_address},
        embedding_id=embedding.id,
    )
    db.add(document)


def run() -> None:
    inserted = 0
    with SessionLocal() as db:
        for incoming in fetch_inbox_emails():
            before_count = db.execute(select(Email.id).where(Email.provider_id == incoming.provider_id)).first()
            persist_email_and_document(db, incoming)
            after_count = db.execute(select(Email.id).where(Email.provider_id == incoming.provider_id)).first()
            if before_count is None and after_count is not None:
                inserted += 1
        db.commit()
    print(f"ETL complete: inserted={inserted} (dedup enabled by provider_id).")


if __name__ == "__main__":
    run()
