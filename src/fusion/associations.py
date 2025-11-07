"""Persistence helpers for mapping Nuvolo leases to ArcGIS features."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import sqlite3
from pathlib import Path
from typing import Iterator, Optional


@dataclass(slots=True)
class LeaseAssociation:
    """Record linking a Nuvolo lease to an ArcGIS feature."""

    lease_id: str
    feature_global_id: str
    feature_object_id: Optional[int] = None
    building_id: Optional[str] = None
    level_id: Optional[str] = None
    unit_id: Optional[str] = None
    geometry_type: Optional[str] = None
    last_synced: datetime = field(default_factory=datetime.utcnow)


class LeaseAssociationStore:
    """Protocol for persisting :class:`LeaseAssociation` records."""

    def upsert(self, association: LeaseAssociation) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def get(self, lease_id: str) -> Optional[LeaseAssociation]:  # pragma: no cover - interface
        raise NotImplementedError

    def remove(self, lease_id: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def iter_all(self) -> Iterator[LeaseAssociation]:  # pragma: no cover - interface
        raise NotImplementedError


class SqliteLeaseAssociationStore(LeaseAssociationStore):
    """Simple SQLite-backed implementation of :class:`LeaseAssociationStore`."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS lease_associations (
                    lease_id TEXT PRIMARY KEY,
                    feature_global_id TEXT NOT NULL,
                    feature_object_id INTEGER,
                    building_id TEXT,
                    level_id TEXT,
                    unit_id TEXT,
                    geometry_type TEXT,
                    last_synced TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def upsert(self, association: LeaseAssociation) -> None:
        payload = {
            "lease_id": association.lease_id,
            "feature_global_id": association.feature_global_id,
            "feature_object_id": association.feature_object_id,
            "building_id": association.building_id,
            "level_id": association.level_id,
            "unit_id": association.unit_id,
            "geometry_type": association.geometry_type,
            "last_synced": association.last_synced.isoformat(),
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO lease_associations (
                    lease_id,
                    feature_global_id,
                    feature_object_id,
                    building_id,
                    level_id,
                    unit_id,
                    geometry_type,
                    last_synced
                ) VALUES (
                    :lease_id,
                    :feature_global_id,
                    :feature_object_id,
                    :building_id,
                    :level_id,
                    :unit_id,
                    :geometry_type,
                    :last_synced
                )
                ON CONFLICT(lease_id) DO UPDATE SET
                    feature_global_id = excluded.feature_global_id,
                    feature_object_id = excluded.feature_object_id,
                    building_id = excluded.building_id,
                    level_id = excluded.level_id,
                    unit_id = excluded.unit_id,
                    geometry_type = excluded.geometry_type,
                    last_synced = excluded.last_synced
                """,
                payload,
            )
            conn.commit()

    def get(self, lease_id: str) -> Optional[LeaseAssociation]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM lease_associations WHERE lease_id = ?",
                (lease_id,),
            ).fetchone()
        return self._row_to_association(row) if row else None

    def remove(self, lease_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM lease_associations WHERE lease_id = ?", (lease_id,))
            conn.commit()

    def iter_all(self) -> Iterator[LeaseAssociation]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM lease_associations ORDER BY lease_id").fetchall()
        for row in rows:
            association = self._row_to_association(row)
            if association:
                yield association

    @staticmethod
    def _row_to_association(row: sqlite3.Row) -> Optional[LeaseAssociation]:
        if not row:
            return None
        return LeaseAssociation(
            lease_id=row["lease_id"],
            feature_global_id=row["feature_global_id"],
            feature_object_id=row["feature_object_id"],
            building_id=row["building_id"],
            level_id=row["level_id"],
            unit_id=row["unit_id"],
            geometry_type=row["geometry_type"],
            last_synced=datetime.fromisoformat(row["last_synced"]),
        )


__all__ = [
    "LeaseAssociation",
    "LeaseAssociationStore",
    "SqliteLeaseAssociationStore",
]
