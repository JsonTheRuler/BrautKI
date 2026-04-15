"""Baseline schema for data layer.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-04-15 00:00:00
"""
from __future__ import annotations

from alembic import op

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE EXTENSION IF NOT EXISTS pgcrypto;

        CREATE TABLE IF NOT EXISTS document_embeddings (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          vector vector(16) NOT NULL,
          metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS documents (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          source VARCHAR(100) NOT NULL,
          content TEXT NOT NULL,
          metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
          embedding_id UUID REFERENCES document_embeddings(id) ON DELETE SET NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS emails (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          from_address VARCHAR(255) NOT NULL,
          to_address VARCHAR(255) NOT NULL,
          subject VARCHAR(500) NOT NULL,
          body TEXT NOT NULL,
          labels JSONB NOT NULL DEFAULT '{}'::jsonb,
          metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS leads (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          company_name VARCHAR(255) NOT NULL,
          contact_name VARCHAR(255) NOT NULL,
          contact_email VARCHAR(255) NOT NULL,
          source VARCHAR(100) NOT NULL,
          metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_leads_contact_email ON leads(contact_email);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS leads;
        DROP TABLE IF EXISTS emails;
        DROP TABLE IF EXISTS documents;
        DROP TABLE IF EXISTS document_embeddings;
        """
    )
