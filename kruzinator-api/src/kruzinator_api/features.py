from __future__ import annotations

import math


def _dist(a: dict, b: dict) -> float:
    dx = float(b["x"]) - float(a["x"])
    dy = float(b["y"]) - float(a["y"])
    return math.hypot(dx, dy)


def compute_features(points: list[dict]) -> dict:
    if not points:
        return {
            "pointsCount": 0,
            "durationMs": 0,
            "pathLength": 0.0,
            "closureDistance": 0.0,
            "avgSpeed": 0.0,
            "peakSpeed": 0.0,
        }

    points_count = len(points)
    t0 = int(points[0].get("tMs", 0))
    t1 = int(points[-1].get("tMs", 0))
    duration_ms = max(0, t1 - t0)

    path_length = 0.0
    peak_speed = 0.0

    for prev, cur in zip(points, points[1:], strict=False):
        segment = _dist(prev, cur)
        path_length += segment
        dt = int(cur.get("tMs", 0)) - int(prev.get("tMs", 0))
        if dt > 0:
            peak_speed = max(peak_speed, segment / (dt / 1000.0))

    closure_distance = _dist(points[0], points[-1])
    avg_speed = (path_length / (duration_ms / 1000.0)) if duration_ms > 0 else 0.0

    return {
        "pointsCount": points_count,
        "durationMs": duration_ms,
        "pathLength": path_length,
        "closureDistance": closure_distance,
        "avgSpeed": avg_speed,
        "peakSpeed": peak_speed,
    }
