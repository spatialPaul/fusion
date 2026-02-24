from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import psycopg


app = FastAPI(title="Run Loop Planner", version="0.1.0")


class RunRouteRequest(BaseModel):
    start_lat: float = Field(ge=-90, le=90)
    start_lon: float = Field(ge=-180, le=180)
    target_distance_km: float = Field(gt=0.5, le=100)
    options: int = Field(default=3, ge=2, le=3)


class RouteOption(BaseModel):
    route_id: int
    distance_m: float
    geojson: dict[str, Any]


class RunRouteResponse(BaseModel):
    routes: list[RouteOption]


@dataclass
class Settings:
    db_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/routes")


def fetch_loop_candidates(req: RunRouteRequest, settings: Settings) -> list[RouteOption]:
    query = """
    WITH start_point AS (
      SELECT ST_SetSRID(ST_Point(%(lon)s, %(lat)s), 4326) AS geom
    ),
    nearest_start AS (
      SELECT id
      FROM run_vertices v, start_point s
      ORDER BY v.geom <-> s.geom
      LIMIT 1
    ),
    random_edges AS (
      SELECT id, geom, ST_Length(geom::geography) AS distance_m
      FROM run_edges
      ORDER BY random()
      LIMIT %(options)s
    )
    SELECT
      row_number() over() AS route_id,
      distance_m,
      ST_AsGeoJSON(geom)::jsonb AS geojson
    FROM random_edges;
    """

    try:
      with psycopg.connect(settings.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    {
                        "lat": req.start_lat,
                        "lon": req.start_lon,
                        "target_m": req.target_distance_km * 1000,
                        "options": req.options,
                    },
                )
                rows = cur.fetchall()
    except psycopg.Error as exc:
        raise HTTPException(status_code=500, detail=f"Database query failed: {exc}") from exc

    return [
        RouteOption(route_id=row[0], distance_m=float(row[1]), geojson=row[2])
        for row in rows
    ]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/run-routes", response_model=RunRouteResponse)
def run_routes(req: RunRouteRequest) -> RunRouteResponse:
    routes = fetch_loop_candidates(req, Settings())
    if len(routes) < 2:
        raise HTTPException(status_code=404, detail="Not enough route options generated")
    return RunRouteResponse(routes=routes)
