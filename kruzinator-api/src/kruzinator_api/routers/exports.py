from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db import get_db_session
from ..models import Datapoint
from ..schemas import ExportRequest


router = APIRouter(prefix="/api/v1/exports", tags=["exports"])


@router.post("")
async def export_dataset(payload: ExportRequest, db: AsyncSession = Depends(get_db_session)) -> StreamingResponse:
    settings = get_settings()

    stmt = select(Datapoint).order_by(Datapoint.created_at.asc())
    if payload.user_ids:
        stmt = stmt.where(Datapoint.user_id.in_(payload.user_ids))
    if payload.protocol_version:
        stmt = stmt.where(Datapoint.protocol_version == payload.protocol_version)
    if payload.created_from:
        stmt = stmt.where(Datapoint.created_at >= payload.created_from)
    if payload.created_to:
        stmt = stmt.where(Datapoint.created_at <= payload.created_to)

    rows = (await db.execute(stmt.limit(settings.exports_max_rows))).scalars().all()
    if len(rows) >= settings.exports_max_rows:
        raise HTTPException(status_code=413, detail="Export too large")

    async def gen():
        for r in rows:
            record = {
                "datapointId": str(r.id),
                "userId": str(r.user_id),
                "sessionId": str(r.session_id) if r.session_id else None,
                "createdAt": r.created_at.isoformat(),
                "captureLabel": r.capture_label,
                "protocolVersion": r.protocol_version,
                "metadata": r.context,
                "features": r.features,
                "raw": r.raw,
            }
            yield (json.dumps(record, separators=(",", ":")) + "\n").encode("utf-8")

    return StreamingResponse(
        gen(),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": "attachment; filename=export.jsonl"},
    )
