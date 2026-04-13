from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy.orm import Session

from .db import SessionLocal
from .gateway_client import fetch_embedding_via_gateway
from .models import Document, DocumentEmbedding, Email


@dataclass
class IncomingEmail:
    from_address: str
    to_address: str
    subject: str
    body: str
    provider_id: str


def fetch_inbox_emails() -> Iterable[IncomingEmail]:
    """
    TODO: replace with IMAP or Microsoft Graph integration.
    Keep output shape stable so this ETL remains unchanged.
    """
    return [
        IncomingEmail(
            from_address="ceo@client.no",
            to_address="hello@aiready.no",
            subject="Need AI readiness workshop",
            body="We want a 2-day workshop for our leadership team in May.",
            provider_id="mock-001",
        ),
        IncomingEmail(
            from_address="ops@prospect.no",
            to_address="hello@aiready.no",
            subject="Can you automate inbox triage?",
            body="Looking for help with shared mailbox processing and CRM sync.",
            provider_id="mock-002",
        ),
    ]


def persist_email_and_document(db: Session, email: IncomingEmail) -> None:
    email_row = Email(
        from_address=email.from_address,
        to_address=email.to_address,
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
    with SessionLocal() as db:
        for incoming in fetch_inbox_emails():
            persist_email_and_document(db, incoming)
        db.commit()
    print("ETL complete: emails + documents + embeddings stored.")


if __name__ == "__main__":
    run()
