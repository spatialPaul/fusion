# Custom Run Route Planner (PostGIS + Python + MapLibre)

This project is a runnable starter for a **loop-running route planner**.
Given a start point and target distance, the API returns 2–3 route options and renders them on a simple MapLibre UI.

## What you can see right now

- A local web UI at `http://localhost:8000/`.
- A form to submit start point + target distance.
- A map that draws returned routes in 3 colors.

> Current route results are still scaffold-level placeholders from network edges. The plumbing is ready for real pgRouting loop assembly.

## Stack

- PostgreSQL + PostGIS
- pgRouting
- Python (FastAPI + psycopg)
- MapLibre GL JS
- OSM ingestion with GDAL/osm2pgsql (workflow documented below)

## Run it locally

### 1) Start database

```bash
docker compose up -d db
```

### 2) Initialize schema

```bash
docker exec -i fusion-db psql -U postgres -d routes < sql/schema.sql
```

### 3) Install Python deps and run API/UI

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 4) Open the app

Visit:

- `http://localhost:8000/` (visual app)
- `http://localhost:8000/docs` (Swagger API docs)
- `http://localhost:8000/health`

## API example

```bash
curl -X POST http://localhost:8000/run-routes \
  -H 'content-type: application/json' \
  -d '{"start_lat": 40.734, "start_lon": -73.994, "target_distance_km": 8, "options": 3}'
```

## OSM ingest notes

Example import with `osm2pgsql`:

```bash
osm2pgsql \
  --create \
  --database routes \
  --host localhost \
  --port 5432 \
  --username postgres \
  --hstore \
  --slim \
  your-city.osm.pbf
```

Then convert imported lines to `run_edges` and generate `run_vertices` + topology for pgRouting.

## Next step to make routes real

Replace the placeholder SQL with:

1. Snap start to nearest vertex.
2. Select waypoint candidates around target radius.
3. Build 3-leg loops via `pgr_dijkstra`.
4. Score by distance error + overlap penalty.
5. Return top 2–3 unique loops as GeoJSON.
