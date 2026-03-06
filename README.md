# Kruzinator: Circle Gesture Identity (Data Collection)

Kruzinator is a mobile-first web app that collects **circle-drawing gestures** and stores them as a **behavioral signature dataset** tied to a user.

The core idea: **how** a person draws a circle (timing, curvature, micro-corrections, pressure patterns, etc.) can be distinctive enough to support later identity modeling. For now, the focus is on **managing users and their circle samples** (capture, storage, review, export).

This repository’s README is written as a product/spec description that can be used later to implement the app.

---

## Goal

Collect and manage high-quality circle gesture samples in a way that supports future identity modeling.

- Create and manage **users** (pseudonymous IDs).
- Capture and store **multiple circle samples per user**.
- Compute and store **derived features** (optional, reproducible) alongside raw samples.
- Provide basic **review/admin tooling** (spot-check, search/filter by metadata/tags, export).
- Support **data governance** (retention, deletion by user).

This app is primarily a **data collection + user/sample management** pipeline.

---

## What the user does (UX flow)

### 1) Consent and explanation
Before any capture, the app explains:

- What is being collected (gesture telemetry)
- What it’s used for (creating a dataset of circle-drawing signatures)
- Retention rules and deletion options

### 2) Create/select a user
The user creates a new profile (or selects an existing one).

- The app generates a **pseudonymous user identifier** (or links to an auth account, depending on product decisions).

### 3) Capture circle samples
The user completes a guided set of circle drawings.

- The user draws **N circles** across prompts (speed changes, size changes, clockwise/counterclockwise).
- Each attempt is stored as a separate datapoint linked to the current user.

### 4) Review (optional)
The user (or an admin) can review recent samples:

- Inspect samples and metadata (e.g., device/prompt context)
- Add notes/tags for QA or research (manual)
- Re-collect samples if the drawing is unusable for the intended dataset

---

## What is captured (single datapoint)

Each drawing attempt produces one **datapoint** with:

### A) Metadata (context)
- App version
- Device and platform info (coarse)
- Canvas size, device pixel ratio (DPR)
- Input type (finger/stylus/mouse) when available
- Session/task identifiers (capture prompt type; collection protocol version)

### B) Raw time-series (gesture telemetry)
A sequence of points sampled while the user draws:

- `x`, `y`: canvas coordinates (DPR-aware)
- `tMs`: milliseconds since stroke start
- Optional pointer channels when supported: pressure, tilt, azimuth

Sampling may be:

- `raw`: every input event
- `time`: target Hz (e.g., 60 Hz)
- `distance`: minimum movement threshold
- `hybrid`: time + minimum distance (typical default)

### C) Derived features (computed from raw)
Derived values computed from raw samples (for analysis and future modeling), for example:

- Duration, path length, average/peak speed
- Closure distance (distance between start/end)
- Curvature / turning-angle statistics
- Resampling to a fixed number of points
- Normalized geometry (translate/scale/rotate)
- Simple circle-fit residual error (as a hint)

---

## Data labeling

Labeling strategy is intentionally simple:

- Each datapoint is labeled with the **user ID** (ground truth) and a **capture label** (e.g., prompt type, protocol step).
- Additional labels can be added later (e.g., handedness, stylus usage) but are not required for MVP.

---

## No quality gates

The app does not automatically accept/reject strokes or compute quality scores. Any filtering is a downstream, analysis-time decision.

---

## Privacy and safety (important)

Circle gesture telemetry is potentially **sensitive** (behavioral biometric-like). The product should:

- Avoid collecting direct PII unless explicitly needed.
- Make consent explicit and revocable.
- Provide a clear retention policy and deletion path.
- Treat raw telemetry and previews as sensitive (access controls, encryption, audit logs).
- Separate “identity model” from “identity account” where possible (pseudonymous user IDs).

---

## System responsibilities (implementation-agnostic)

Even if the implementation changes, the system should support:

- **Capture**: reliable pointer/stylus capture on mobile browsers
- **Normalize**: consistent coordinate system and time base
- **Store**: users + raw time-series + derived features + labels
- **Review**: basic admin/user review of samples and metadata
- **Export**: dataset export for ML training (e.g., JSONL/Parquet)
- **Govern**: retention policies and deletion by user

---

## API shape (conceptual)

This is a conceptual API outline (exact routes can change). The emphasis is on **user and sample management**:

- `POST /v1/users` → create a pseudonymous user
- `GET /v1/users/{user_id}` → fetch user summary
- `DELETE /v1/users/{user_id}` → delete user and associated data (subject to retention policy)
- `POST /v1/sessions` → start a capture session (protocol version, prompt plan)
- `POST /v1/datapoints` → upload a single stroke datapoint (linked to `user_id`)
- `GET /v1/users/{user_id}/datapoints` → list samples and metadata
- `GET /v1/datapoints/{datapoint_id}` → fetch sample metadata/features
- `GET /v1/datapoints/{datapoint_id}/raw` → fetch raw payload (access-controlled)
- `POST /v1/datapoints/{datapoint_id}/tags` → add manual tags/notes (optional)
- `POST /v1/exports` → request a dataset export (scoped by protocol/date/user cohort)

In all cases, the backend remains the source-of-truth for storage and data governance.

---

## Notes for future implementation

- Prefer a packed/compressed payload format for production scale (delta encoding → MessagePack → gzip → base64).
- Add antifraud heuristics (rate limits, duplicate trajectory detection).
- Maintain a clear separation between:
  - raw data (for reproducibility)
  - normalized features (for model speed)
  - optional tags/notes (for manual review)
