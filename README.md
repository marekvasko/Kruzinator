# Kruzinator: Circle Gesture Collection (Datapoints)

Kruzinator is a mobile-first web app that collects **circle-drawing gestures** and stores them as a dataset of raw gesture telemetry plus optional derived features.

The core idea stays the same: **how** a person draws a circle (timing, curvature, micro-corrections, pressure patterns, etc.) is distinctive enough to support future modeling. The product focus is on collecting many **datapoints** over time, with flexible metadata on each datapoint (hand, direction, device context, etc.).

This README is a product/spec description meant to guide implementation.

---

## Product idea (current)

The app supports **unbounded datapoint collection**:

- A person can collect **as many circle datapoints as they want**.
- Each datapoint carries enough metadata to describe the capture context (e.g., right/left hand, index finger vs stylus, clockwise/counterclockwise, prompt type).
- Datapoints are associated with the **logged-in account** and are manageable anywhere after signing in.

---

## Goals

- Make it easy to collect circle gesture samples across **many datapoints over time**.
- Keep identity simple: **access is based on login**.
- Keep the backend the source-of-truth for stored telemetry and governance.

Non-goals for MVP:

- Automatic quality scoring or acceptance/rejection of strokes.
- Identity modeling or authentication based on gestures.

---

## Key concepts

### Identity mode

There is a single identity mode:

- **Logged-in**: a signed-in user creates datapoints that are **accessible across devices**.
- Server-side authorization controls access.

### Datapoint

- **Datapoint**: a single circle drawing attempt (one stroke) linked to the logged-in user.

---

## UX flow (updated)

### 1) Consent and explanation
Before any capture, the app explains:

- What is collected (gesture telemetry)
- What it’s used for (building a dataset of circle-drawing signatures)
- That capture is tied to the logged-in account
- Retention rules and deletion options

### 2) Log in
The user signs in to access their dataset.

### 3) Capture circles (repeat anytime)
The user draws circles. Each attempt is stored as a datapoint linked to:

- the logged-in account
- capture metadata (device/canvas/input context + user-provided capture labels)

There is no fixed number of circles; the user can add more at any time.

### 4) Review and management
The user can:

- Inspect datapoints and metadata
- Add notes/tags (optional)
- Delete datapoints (and request account-scoped deletion, subject to retention policy)

---

## What is captured (datapoint)

Each circle attempt produces one **datapoint** with:

### A) Metadata (context)
- App version
- Device/platform info (coarse)
- Canvas size and device pixel ratio (DPR)
- Input type (finger/stylus/mouse) when available
- Identifiers:
  - protocol/prompt label (optional)

User-provided capture labels (examples):

- Hand: left/right/unknown
- Finger/tool: index finger/thumb/stylus/mouse/unknown
- Direction: clockwise/counterclockwise/unknown
- Any other freeform tags needed for the collection protocol

### B) Raw time-series (gesture telemetry)
A sequence of sampled points while the user draws:

- `x`, `y`: canvas coordinates (DPR-aware)
- `tMs`: milliseconds since stroke start
- Optional pointer channels: pressure, tilt, azimuth (when supported)

Sampling may be:

- `raw`: every input event
- `time`: target Hz (e.g., 60 Hz)
- `distance`: minimum movement threshold
- `hybrid`: time + minimum distance

### C) Derived features (optional, computed from raw)
Derived values computed from raw samples (reproducible), for example:

- Duration, path length, average/peak speed
- Closure distance (distance between start/end)
- Curvature / turning-angle statistics
- Resampling to a fixed number of points
- Normalized geometry (translate/scale/rotate)
- Simple circle-fit residual error (hint only)

---

## Data labeling

- Primary linkage is **user → datapoint**.
- Labeling should be metadata-driven: each datapoint may include labels such as hand/finger/tool and clockwise/counterclockwise, but the system should not require a rigid schema.
- Additional labels can be added later; not required for MVP.

---

## No quality gates

The app does not automatically accept/reject strokes or compute quality scores. Any filtering is a downstream analysis-time decision.

---

## Privacy and safety

Circle gesture telemetry is potentially **sensitive** (behavioral biometric-like). The product should:

- Avoid collecting direct PII unless explicitly needed.
- Make consent explicit and revocable.
- Treat raw telemetry and previews as sensitive (access controls, encryption in transit/at rest where applicable, audit logs).

Access expectations:

- Data is access-controlled via account auth and available across devices.

---

## System responsibilities (implementation-agnostic)

Even if implementation details change, the system should support:

- **Capture**: reliable pointer/stylus capture on mobile browsers
- **Normalize**: consistent coordinate system and time base
- **Store**: user-linked datapoints (raw + derived)
- **Manage**: list, tag, and delete
- **Review**: basic inspection of samples/metadata and optional tagging
- **Export**: dataset export for ML training (e.g., JSONL/Parquet)
- **Govern**: retention policies and deletion

---

## API shape (conceptual)

Exact routes can change. The emphasis is now **account-scoped datapoints**.

### Auth / identity

- `POST /api/v1/auth/login` → log in (establish authenticated access)
- `POST /api/v1/auth/logout` → log out (revoke authenticated access)

### Datapoints

- `POST /api/v1/datapoints` → upload a single circle datapoint (linked to the logged-in user)
- `GET /api/v1/datapoints` → list datapoints and metadata (optionally filter by labels)
- `GET /api/v1/datapoints/{datapoint_id}` → fetch datapoint metadata/features
- `GET /api/v1/datapoints/{datapoint_id}/raw` → fetch raw payload (access-controlled)
- `POST /api/v1/datapoints/{datapoint_id}/tags` → add manual tags/notes (optional)
- `DELETE /api/v1/datapoints/{datapoint_id}` → delete a datapoint (subject to retention policy)

### Exports

- `POST /api/v1/exports` → request an export scoped by date/labels

---

## Notes for future implementation

- Prefer a packed/compressed payload format for production scale (delta encoding → MessagePack → gzip → base64).
- Add abuse controls (rate limits, duplicate trajectory heuristics).
- Keep a clear separation between:
  - raw data (for reproducibility)
  - derived/normalized features (for speed)
  - optional tags/notes (manual review)
