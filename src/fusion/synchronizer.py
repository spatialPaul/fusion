"""Synchronization utilities for Nuvolo and ArcGIS."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional, Sequence, Tuple

from .arcgis_client import ArcGISClient
from .associations import LeaseAssociation, LeaseAssociationStore
from .models import LeaseRecord
from .nuvolo_client import NuvoloClient


@dataclass
class LeaseSynchronizer:
    """Coordinates synchronization of lease records between Nuvolo and ArcGIS."""

    nuvolo: NuvoloClient
    arcgis: ArcGISClient
    associations: LeaseAssociationStore

    def sync_from_nuvolo(
        self,
        *,
        updated_since: Optional[datetime] = None,
        batch_size: int = 50,
    ) -> List[dict]:
        """Fetch leases from Nuvolo and upsert them into ArcGIS."""

        batch: List[LeaseRecord] = []
        responses: List[dict] = []
        for lease in self.nuvolo.iter_leases(updated_since=updated_since):
            batch.append(lease)
            if len(batch) >= batch_size:
                responses.append(self._push_to_arcgis(list(batch)))
                batch.clear()
        if batch:
            responses.append(self._push_to_arcgis(list(batch)))
        return responses

    def _push_to_arcgis(self, leases: Iterable[LeaseRecord]) -> dict:
        lease_list = list(leases)
        additions: List[LeaseRecord] = []
        add_features: List[dict] = []
        updates: List[Tuple[LeaseRecord, LeaseAssociation]] = []
        update_features: List[dict] = []

        for lease in lease_list:
            association = self.associations.get(lease.lease_id)
            feature = lease.to_arcgis_feature(association)
            if association is None:
                additions.append(lease)
                add_features.append(feature)
            else:
                updates.append((lease, association))
                update_features.append(feature)

        response = self.arcgis.upsert_leases(adds=add_features, updates=update_features)
        self._persist_results(additions, updates, response)
        return response

    def _persist_results(
        self,
        additions: Sequence[LeaseRecord],
        updates: Sequence[Tuple[LeaseRecord, LeaseAssociation]],
        response: dict,
    ) -> None:
        timestamp = datetime.utcnow()

        add_results = response.get("addResults") or []
        for lease, result in zip(additions, add_results):
            association = self._build_association(lease, result, timestamp)
            if association:
                self.associations.upsert(association)

        update_results = response.get("updateResults") or []
        for (lease, existing), result in zip(updates, update_results):
            association = self._build_association(
                lease,
                result,
                timestamp,
                fallback=existing,
            )
            if association:
                self.associations.upsert(association)

    def _build_association(
        self,
        lease: LeaseRecord,
        result: object,
        timestamp: datetime,
        *,
        fallback: Optional[LeaseAssociation] = None,
    ) -> Optional[LeaseAssociation]:
        if not isinstance(result, dict) or not result.get("success", True):
            return None

        global_id = result.get("globalId") or result.get("globalID")
        object_id = result.get("objectId")

        if fallback is not None:
            global_id = global_id or fallback.feature_global_id
            if object_id is None:
                object_id = fallback.feature_object_id

        if not global_id:
            return None

        geometry_type = None
        if lease.geometry and isinstance(lease.geometry, dict):
            geometry_type = lease.geometry.get("geometryType")
        if geometry_type is None and lease.latitude is not None:
            geometry_type = "point"

        return LeaseAssociation(
            lease_id=lease.lease_id,
            feature_global_id=str(global_id),
            feature_object_id=object_id if object_id is None else int(object_id),
            building_id=lease.building_id,
            level_id=lease.level_id,
            unit_id=lease.unit_id,
            geometry_type=geometry_type,
            last_synced=timestamp,
        )


__all__ = ["LeaseSynchronizer"]
