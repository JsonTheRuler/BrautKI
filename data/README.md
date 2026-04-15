# Data

Python package for Postgres + pgvector models and ETL.

## Phase 4 data hardening

- Main DB: Postgres
- Vector store: pgvector (in the same Postgres instance)
- ORM: SQLAlchemy 2.x
- Migration strategy: Alembic revisions in `data/alembic/versions/` (plus SQL bootstrap file).
- ETL dedup: `emails.provider_id` unique key prevents duplicate ingest.
- Connectors: source-selectable email connectors (`mock`, `imap`, `graph`).

## Schema

- `documents`: source, content, metadata, embedding reference
- `emails`: sender/recipient/subject/body + labels and metadata
- `leads`: company/contact/source + metadata
- `document_embeddings`: pgvector vector + metadata

## Setup

```bash
cd data
python -m venv .venv
. .venv/Scripts/activate
pip install -e .
```

Set environment variables:

- `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/ai_ready`
- `GATEWAY_URL=http://localhost:4000`
- `EMBEDDING_MODEL_ALIAS=fast-cheap`
- `EMBEDDING_DIMENSIONS=16`

Apply migration (quick SQL bootstrap):

```bash
psql "postgresql://postgres:postgres@localhost:5432/ai_ready" -f migrations/0001_init.sql
```

Or use Alembic (recommended):

```bash
alembic -c alembic.ini upgrade head
```

Run ETL:

```bash
python -m data_layer.etl_emails
```

## ETL notes

- Set `EMAIL_SOURCE=mock|imap|graph`.
- IMAP and Graph connectors are explicit stubs with TODOs and credential placeholders.
- Embeddings are requested through the gateway alias in `EMBEDDING_MODEL_ALIAS`.
- Re-running ETL is safe for the same `provider_id` entries.

## Connector environment variables

- `EMAIL_SOURCE=mock|imap|graph`
- IMAP:
  - `IMAP_HOST`
  - `IMAP_PORT` (default 993)
  - `IMAP_USERNAME`
  - `IMAP_PASSWORD`
- Graph:
  - `GRAPH_TENANT_ID`
  - `GRAPH_CLIENT_ID`
  - `GRAPH_CLIENT_SECRET`
  - `GRAPH_MAILBOX_USER`

## Use from agents

```python
from data_layer import SessionLocal, Email
from sqlalchemy import select

with SessionLocal() as db:
    recent_emails = db.execute(select(Email).limit(10)).scalars().all()
```
