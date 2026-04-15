"""Add provider_id for email idempotency.

Revision ID: 0002_email_provider_id
Revises: 0001_baseline
Create Date: 2026-04-15 00:10:00
"""
from __future__ import annotations

from alembic import op

revision = "0002_email_provider_id"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE emails
        ADD COLUMN IF NOT EXISTS provider_id VARCHAR(255);

        UPDATE emails
        SET provider_id = COALESCE(metadata->>'provider_id', id::text)
        WHERE provider_id IS NULL;

        ALTER TABLE emails
        ALTER COLUMN provider_id SET NOT NULL;

        CREATE UNIQUE INDEX IF NOT EXISTS uq_emails_provider_id ON emails(provider_id);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS uq_emails_provider_id;
        ALTER TABLE emails DROP COLUMN IF EXISTS provider_id;
        """
    )
