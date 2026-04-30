# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the dev server with hot reload
uvicorn main:app --reload

# Interactive API docs (once server is running)
# http://localhost:8000/docs
```

Requires a `.env` file with `DATABASE_URL`:
- **SQLite (dev):** `DATABASE_URL=sqlite+aiosqlite:///./dev.db`
- **PostgreSQL (prod):** `DATABASE_URL=postgresql+asyncpg://user:password@host/db`

For PostgreSQL, run `sql/seed.sql` first to create tables and seed test data.

There is no test suite yet. There is no linter configured.

## Stack

- Python 3.11+ / FastAPI / Uvicorn
- SQLAlchemy 2.0 async (`asyncpg`) — SQLite in dev, PostgreSQL in prod
- Pydantic v2 for validation (`pydantic-settings`)
- `python-dotenv` for env vars

## Project structure

```
main.py                  # App entry point: FastAPI instance, exception handlers, router registration
app/
  model/__init__.py      # SQLAlchemy ORM models
  schemas.py             # Pydantic request/response schemas
  routers/
    assets.py            # Asset endpoints
  database/
    connection.py        # Async engine + SessionLocal (reads DATABASE_URL from .env)
    deps.py              # get_db dependency for FastAPI
sql/
  seed.sql               # PostgreSQL DDL + seed data
  erd.md                 # Entity-relationship diagram (Mermaid)
docs/
  analisis.md            # Business rules and design decisions
  cu-01..05.md           # Use cases
```

## Architecture

`main.py` is the single entry point. On startup (`lifespan`) it runs `Base.metadata.create_all` to auto-create tables. Routers are registered at the bottom of the file.

**Error response contract** — all errors follow this shape (enforced by handlers in `main.py`):

```json
{ "success": false, "error": { "code": "SNAKE_CASE_CODE", "message": "...", "details": [] } }
```

Raise `HTTPException` with `detail={"code": ..., "message": ..., "details": [...]}` to use the structured handler; bare strings fall back to `HTTP_ERROR`.

**Success response contract** — all endpoints wrap their payload in:

```json
{ "success": true, "data": { ... } }
```

## Implemented endpoints

| Method | Route          | Description                                           |
|--------|----------------|-------------------------------------------------------|
| GET    | `/health`      | Health check                                          |
| POST   | `/assets`      | Create asset + first version (status: `pending_review`) |
| GET    | `/assets/{id}` | Get asset with all versions and approvals             |

`POST /assets` validates that the agency exists, the project exists, the user exists, and that the project belongs to the given agency before writing anything.

## Domain model

Agency → Project → Asset → AssetVersion (linear, immutable history)

**Models in `app/model/__init__.py`:**
- `Agency` — `agency_type`: `agency | freelancer`
- `Project` — belongs to one `Agency`
- `User` — `role`: `admin | designer | reviewer | client`; optionally linked to an `Agency`
- `Asset` — belongs to a `Project` + `Agency`; tracks `status` and `current_version`
- `AssetVersion` — unique constraint on `(asset_id, version_number)`
- `Approval` — immutable record of a reviewer/client decision
- `Comment` — attached to a specific `AssetVersion`, never changes asset state

**Asset states:**

```
pending_review  →[reviewer/client approves]→  approved
pending_review  ←[designer uploads version]←  rejected
approved        →[admin archives]→            archived
```

**Key rules:**
- `version_number` starts at 1, increments as `MAX + 1` per asset. Past versions are immutable.
- Only the current version (`assets.current_version`) can receive an approval/rejection.
- Only `client` or `reviewer` roles create approval records.
- Comments attach to a specific `asset_version`; they never change asset state.
- Approvals are never modified or deleted (full auditability).

## Pending use cases (not yet implemented)

From `docs/`:
- **CU-02** — Upload new version to an existing asset (designer, asset in `rejected` state)
- **CU-03** — Approve or reject a version (reviewer/client)
- **CU-04** — Comment on a version (any user with project access)
- **CU-05** — Already covered by `GET /assets/{id}`

## Assumptions baked into the design

1. **No authentication** — `user_id` is passed in the request body. In production it would come from a JWT.
2. **File storage is simulated** — `file_url` is stored as a plain string; no S3/GCS integration.
3. **Single approver is enough** — first approval decision wins; multi-sig is out of scope.
4. **No notifications** — no email or in-app events are triggered.
5. **Project belongs to one agency** — `projects.agency_id` is immutable.
6. **Linear versioning** — no branches or merges; versions are strictly sequential (1 → 2 → 3 → …).
