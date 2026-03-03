from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI

from .schemas.ingest import IngestDatapointRequest, IngestDatapointResponse

app = FastAPI(title='Kruzinator API', version='0.1.0')


@app.get('/health')
async def health_check() -> dict[str, str]:
    return {'status': 'ok'}


@app.post('/v1/datapoints', response_model=IngestDatapointResponse)
async def ingest_datapoint(payload: IngestDatapointRequest) -> IngestDatapointResponse:
    return IngestDatapointResponse(
        datapoint_id=uuid4(),
        received_at=datetime.now(timezone.utc),
        accepted=False,
        quality_score=0.0,
        earned_points=0,
        new_badges=[],
        server_metrics={'points_received': len(payload.payload.timeseries.points)}
        if payload.payload.kind == 'inline' and payload.payload.timeseries.format == 'raw_points'
        else None,
    )
