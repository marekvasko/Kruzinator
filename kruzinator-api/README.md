# Kruzinator API

Async FastAPI backend for user + circle-gesture datapoint collection.

## Requirements

- Postgres (required)

## Configuration

Environment variables (or `kruzinator-api/.env`):

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/kruzinator
ENVIRONMENT=development
LOG_LEVEL=info
HOST=0.0.0.0
PORT=8000
```

## Database migrations

```bash
cd kruzinator-api
uv run alembic -c alembic.ini upgrade head
```

## Run

```bash
cd kruzinator-api
uv run kruzinator-api
```

OpenAPI docs:

- `GET /docs`
- `GET /openapi.json`
