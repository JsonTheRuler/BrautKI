# Data

Python package for Postgres + pgvector models and ETL.

## Phase 2 decisions

- Main DB: Postgres
- Vector store: pgvector (in the same Postgres instance)
- ORM: SQLAlchemy 2.x
- Migration strategy: SQL migration files in `data/migrations/` (starting with `0001_init.sql`)

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

Apply migration:

```bash
psql "postgresql://postgres:postgres@localhost:5432/ai_ready" -f migrations/0001_init.sql
```

Run ETL:

```bash
python -m data_layer.etl_emails
```

## ETL notes

- `etl_emails.py` currently uses mocked inbox data.
- TODO marker included where IMAP / Microsoft Graph credentials should be wired.
- Embeddings are requested through the gateway alias in `EMBEDDING_MODEL_ALIAS`.

## Use from agents

```python
from data_layer import SessionLocal, Email
from sqlalchemy import select

with SessionLocal() as db:
    recent_emails = db.execute(select(Email).limit(10)).scalars().all()
```
