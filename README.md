# Circle Data Collection App (Monorepo)

A monorepo for a mobile-first web app that collects **circle-drawing gestures** on a touchscreen.  
Each drawing produces a **single datapoint** consisting of:

- A **time-series** captured while the user draws (pointer trajectory: `x, y, t` + optional pressure/tilt)
- Optional **preview** (PNG) for QA/admin review
- Derived **client-side metrics** (duration, path length, closure distance, quick circle-fit hint)

Backend processes and validates submissions, stores raw payloads + normalized features, and powers **rewards** and **leaderboards**.

---

## Repo Structure
- `/`
  - `kruzinator-vue/` # Vue 3 + TypeScript client (PWA-ready)
  - `kruzinator-api/` # FastAPI (Python 3.12) backend


## Tech Stack

### Frontend (`apps/web`)
- **Vue 3** + **Vite** + **TypeScript**
- **Pinia** (state), **Vue Router**
- UI: **Quasar** (recommended) or other component framework
- Pointer input capture on canvas (`pointerdown/move/up/cancel`)
- Sampling + optional smoothing + client-side validation
- Offline queue (optional): IndexedDB + background sync (PWA)

### Backend (`apps/api`)
- **Python 3.12**
- **FastAPI** + **Pydantic v2** (typed request/response models)
- **PostgreSQL** (primary storage)
- **Redis** (leaderboards cache / rate limits)
- **S3-compatible storage** (MinIO in dev) for raw compressed payloads + previews
- Background tasks: Celery/RQ/ARQ (optional; e.g., PNG preview rendering, aggregations)
- Tests: `pytest` (+ async helpers)

---

## Core Concepts

### Datapoint
A datapoint is a single circle-drawing attempt. It includes:

- **Metadata**: app version, device/platform info, canvas size, DPR, session/task ids
- **Payload**:
  - Inline time-series (MVP): JSON list of points
  - Packed and compressed (production): packed deltas → MessagePack → gzip → base64
- **Quality** (server-side): accepted/rejected + quality score (0..1)
- **Rewards**: points and badges issued for accepted datapoints

### Time-Series
Captured as a sequence of points:

- `x`, `y` in canvas coordinates (DPR-aware)
- `tMs` relative to stroke start
- optional pointer channels: pressure, tilt, azimuth

Sampling modes supported by the canvas component:
- `raw` (every event)
- `time` (e.g., 60 Hz)
- `distance` (only store if moved by ≥ N px)
- `hybrid` (recommended)

---

## Frontend: `CircleCanvas.vue` Interface

`CircleCanvas.vue` is a reusable “headless” drawing component that:
- Captures pointer time-series
- Applies sampling and optional smoothing
- Computes basic metrics (client-side hint)
- Validates the stroke (min points, duration, closure threshold)
- Exposes an imperative API for export/clear/replay

### Props (high-level)
- Size: `width`, `height`, optional `dpr`
- Interaction: `disabled`, `readOnly`, `capturePointer`
- Data capture: `sampling`, `smoothing`
- Validation: `validation`
- UX: `showGuide`, `showLivePath`, `showDebug`
- Replay: `initialStroke`

### Emits
- `stroke:start`, `stroke:end`, `stroke:validated`
- `state` changes: `idle | drawing | completed | invalid | disabled`
- `cleared`, `error`

### Exposed API
Access via `ref` from the parent page:
- `clear()`, `cancelStroke()`
- `validate()`
- `exportPayload({ format, includePreview, normalize })`
- `getStroke()`, `getMetrics()`
- `setStroke(points)` (replay)

> The backend is the source-of-truth for validation and scoring; client validation is mainly for UX.

---

## Backend: API Overview

### Auth (minimal)
- Anonymous-first auth (device-based token), with optional upgrade to email later.

### Ingest
- `POST /v1/datapoints`
  - Accepts `metadata` + `payload`
  - Returns: `datapoint_id`, `accepted`, `quality_score`, `earned_points`, `new_badges[]`

### Rewards
- `GET /v1/rewards/me` for user stats and badges

### Leaderboards
- `GET /v1/leaderboards/daily`
- `GET /v1/leaderboards/weekly`
- `GET /v1/leaderboards/all-time`

---

## Data Storage

- **Postgres**: users, sessions, datapoint records (accepted/score), features, reward events
- **Object Storage (S3/MinIO)**:
  - raw payload blobs (gz+base64 decoded to bytes)
  - optional PNG previews
- **Redis**:
  - rate-limits / antifraud throttling
  - leaderboard cached rankings (sorted sets)

---

## Getting Started (Dev)

### Prerequisites
- Node.js (LTS)
- Python 3.12
- Docker + Docker Compose

### 1) Start infrastructure
From repo root:

```bash
docker compose -f docker-compose.yml up -d
```

This should start:
- Postgres
- Redis
- MinIO (S3-compatible)


### 2) Backend
1. `cd kruzinator-api`
2. `python -m venv .venv`
3. `source .venv/bin/activate`
4. `pip install -r requirements.txt`
5. `uvicorn app.main:app --reload`

### 3) Frontend
1. `cd kruzinator-vue`
2. `npm install`
3. `npm run dev`


### Environment Variables (Example)

#### Backend (`kruzinator-api/.env`)

- `DATABASE_URL=postgresql+asyncpg://...`
- `REDIS_URL=redis://...`
- `S3_ENDPOINT_URL=http://localhost:9000`
- `S3_ACCESS_KEY=...`
- `S3_SECRET_KEY=...`
- `S3_BUCKET=circles`
- `JWT_SECRET=...`

#### Frontend (`kruzinator-vue/.env`)
- `VITE_API_BASE_URL=http://localhost:8000`

### Conventions & Quality

#### Python:
- typed models via Pydantic v2
- strict linting/formatting (recommended): ruff + black
- type checks: pyright

#### Frontend:
- TypeScript types for all payloads
- keep canvas hot-path fast (avoid heavy emits per point)
- sampling defaults: hybrid (≈60Hz + min distance)

#### Notes on Privacy & Safety
- Prefer anonymous identifiers.
- Avoid collecting personally identifying information unless required.
- Treat raw gesture data as sensitive (behavioral biometric–like); secure storage and access.
- Provide clear user consent and data retention policy in the UI.

#### Next Steps

Implement packed delta encoding + gzip base64 ingestion for production scale.

Add antifraud heuristics (rate limits, duplicate trajectory hashing).

Add admin review tooling (sample accepted/rejected + preview rendering).

Export pipeline for ML training (Parquet/JSONL).
