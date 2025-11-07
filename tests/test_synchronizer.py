from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

from fusion.arcgis_client import ArcGISClient
from fusion.associations import LeaseAssociation, LeaseAssociationStore
from fusion.models import LeaseRecord
from fusion.nuvolo_client import NuvoloClient
from fusion.synchronizer import LeaseSynchronizer


class DummyStore(LeaseAssociationStore):
    def __init__(self) -> None:
        self.items: dict[str, LeaseAssociation] = {}

    def upsert(self, association: LeaseAssociation) -> None:
        self.items[association.lease_id] = association

    def get(self, lease_id: str):  # pragma: no cover - not used
        return self.items.get(lease_id)

    def remove(self, lease_id: str) -> None:  # pragma: no cover - not used
        self.items.pop(lease_id, None)

    def iter_all(self):  # pragma: no cover - not used
        return iter(self.items.values())


def test_sync_from_nuvolo_persists_associations() -> None:
    lease = LeaseRecord(lease_id="1", name="Lease", status="active")

    nuvolo = MagicMock(spec=NuvoloClient)
    nuvolo.iter_leases.return_value = [lease]

    arcgis = MagicMock(spec=ArcGISClient)
    arcgis.upsert_leases.return_value = {
        "updateResults": [
            {"success": True, "globalId": "{ABC}", "objectId": 10},
        ]
    }

    store = DummyStore()
    synchronizer = LeaseSynchronizer(nuvolo, arcgis, store)

    synchronizer.sync_from_nuvolo(updated_since=datetime(2024, 1, 1))

    assert "1" in store.items
    association = store.items["1"]
    assert association.feature_global_id == "{ABC}"
    assert association.feature_object_id == 10
