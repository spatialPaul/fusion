from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fusion.associations import LeaseAssociation, SqliteLeaseAssociationStore


def test_sqlite_store_roundtrip(tmp_path: Path) -> None:
    store = SqliteLeaseAssociationStore(tmp_path / "associations.db")

    association = LeaseAssociation(
        lease_id="lease-1",
        feature_global_id="{ABC}",
        feature_object_id=42,
        building_id="BLDG-1",
        level_id="L1",
        unit_id="U101",
        geometry_type="polygon",
        last_synced=datetime(2024, 1, 1, 12, 0, 0),
    )

    store.upsert(association)
    stored = store.get("lease-1")

    assert stored is not None
    assert stored.lease_id == "lease-1"
    assert stored.feature_global_id == "{ABC}"
    assert stored.feature_object_id == 42
    assert stored.building_id == "BLDG-1"
    assert stored.level_id == "L1"
    assert stored.unit_id == "U101"
    assert stored.geometry_type == "polygon"
    assert stored.last_synced == datetime(2024, 1, 1, 12, 0, 0)

    association.feature_object_id = 99
    store.upsert(association)
    stored = store.get("lease-1")

    assert stored is not None
    assert stored.feature_object_id == 99

    store.remove("lease-1")
    assert store.get("lease-1") is None


def test_iter_all_returns_sorted(tmp_path: Path) -> None:
    store = SqliteLeaseAssociationStore(tmp_path / "associations.db")

    store.upsert(LeaseAssociation(lease_id="B", feature_global_id="{B}"))
    store.upsert(LeaseAssociation(lease_id="A", feature_global_id="{A}"))

    lease_ids = [association.lease_id for association in store.iter_all()]
    assert lease_ids == ["A", "B"]
