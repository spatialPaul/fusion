# Custom Run Route Planner (PostGIS + Python + MapLibre)

This repository contains a starter architecture for a **loop-running route planner**.
Given a start point and target distance, the API returns 2–3 loop options by searching a street/trail network in PostGIS.

## Stack

- **PostgreSQL + PostGIS**: stores road/trail graph and runs spatial queries.
- **pgRouting**: shortest-path and cost matrix functions over network edges.
- **GDAL/ogr2ogr + osm2pgsql**: import OpenStreetMap data.
- **Python (FastAPI + psycopg)**: API orchestration + loop candidate selection.
- **MapLibre GL JS**: client-side rendering of route options.

## Project Layout

- `app/main.py` – FastAPI service exposing `POST /run-routes`.
- `sql/schema.sql` – network schema and indexes.
- `sql/loop_query.sql` – SQL approach for loop candidate assembly.
- `docker-compose.yml` – local PostGIS + pgRouting setup.

## Quick Start

1. Start PostGIS locally:

```bash
docker compose up -d db
```

2. Apply schema:

```bash
docker exec -i fusion-db psql -U postgres -d routes < sql/schema.sql
```

3. Import OSM network data (example with `osm2pgsql`):

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

4. Transform imported roads into routing edges (sample SQL in `sql/schema.sql`).

5. Start API:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

6. Request route options:

```bash
curl -X POST http://localhost:8000/run-routes \
  -H 'content-type: application/json' \
  -d '{"start_lat": 40.734, "start_lon": -73.994, "target_distance_km": 8, "options": 3}'
```

## How loop generation works

1. **Snap start point** to nearest graph node.
2. Compute a **search radius** from target distance (roughly target / π).
3. Pick candidate waypoints at varied bearings and distance ratios.
4. Build loops as:
   - start → waypoint A
   - waypoint A → waypoint B
   - waypoint B → start
5. Score each loop by:
   - distance error from target
   - overlap penalty (prefer variety)
   - optional elevation/surface preferences
6. Return best 2–3 options.

## MapLibre integration sketch

Use API response `LineString` GeoJSON features and render each candidate route with a different style layer:

```js
map.addSource('run-routes', { type: 'geojson', data: featureCollection });
map.addLayer({
  id: 'route-1',
  type: 'line',
  source: 'run-routes',
  paint: { 'line-color': '#ff4d4d', 'line-width': 5 },
  filter: ['==', ['get', 'route_id'], 1]
});
```

## Next enhancements

- Add slope-aware costs using DEM rasters via GDAL.
- Add safety filters (lit roads, parks, trails).
- Add user preferences (avoid traffic, maximize park coverage).
- Cache route computations with Redis.
