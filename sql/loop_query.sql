-- Skeleton SQL for constructing loop candidates.
-- Inputs:
--   :start_lon, :start_lat, :target_m, :options

WITH start_point AS (
  SELECT ST_SetSRID(ST_Point(:start_lon, :start_lat), 4326) AS geom
),
start_vertex AS (
  SELECT v.id, v.geom
  FROM run_vertices v, start_point s
  ORDER BY v.geom <-> s.geom
  LIMIT 1
),
candidate_waypoints AS (
  SELECT v.id, v.geom
  FROM run_vertices v, start_point s
  WHERE ST_DWithin(v.geom::geography, s.geom::geography, (:target_m / 3.14) * 1.2)
  ORDER BY random()
  LIMIT 50
),
loop_pairs AS (
  SELECT a.id AS a_id, b.id AS b_id
  FROM candidate_waypoints a
  JOIN candidate_waypoints b ON a.id <> b.id
  LIMIT 200
)
SELECT *
FROM loop_pairs
LIMIT :options;

-- In production, expand with pgr_dijkstra calls and scoring by total distance error.
