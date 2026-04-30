# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the dev server with hot reload
uvicorn main:app --reload

# Install dependencies
pip install -r requirements.txt

# Interactive API docs (once server is running)
# http://localhost:8000/docs
```

There is no test suite yet. There is no linter configured.

## Stack

- Python 3.11+ / FastAPI / Uvicorn
- SQLAlchemy 2.0 (async with `asyncpg`) — SQLite in dev, PostgreSQL in prod
- Pydantic v2 for validation and settings (`pydantic-settings`)
- `python-dotenv` for env vars

## Architecture

The app is in early development. `main.py` is the single entry point; it declares the `FastAPI` app, registers exception handlers, and exposes `/health`.

**Error response contract** — all errors follow this shape (enforced by handlers in `main.py`):

```json
{ "success": false, "error": { "code": "SNAKE_CASE_CODE", "message": "...", "details": [] } }
```

Raise `HTTPException` with `detail={"code": ..., "message": ..., "details": [...]}` to use the structured handler; otherwise it falls back to `HTTP_ERROR`.

## Domain model

Agency → Project → Asset → AssetVersion (linear, immutable history)

**Asset states:**

```
pending_review  →[reviewer/client approves]→  approved
pending_review  ←[designer uploads version]←  rejected
approved        →[admin archives]→            archived
```

**Key rules (from `docs/analisis.md`):**
- `version_number` starts at 1, increments as `MAX + 1` per asset. Past versions are immutable.
- Only the current version (`assets.current_version`) can receive an approval/rejection.
- Only `client` or `reviewer` roles create approval records.
- Comments attach to a specific `asset_version`, not the asset; they never change asset state.
- Approvals are never modified or deleted (full auditability).

**Roles:** `admin`, `designer`, `reviewer`, `client`

## Assumptions baked into the design

1. **No authentication** — `user_id` is passed in the request body. In production it would come from a JWT.
2. **File storage is simulated** — `file_url` is stored as a plain string; no S3/GCS integration.
3. **Single approver is enough** — first approval decision wins; multi-sig is out of scope.
4. **No notifications** — no email or in-app events are triggered.
5. **Project belongs to one agency** — `projects.agency_id` is immutable.
