"""Synchronization utilities for Nuvolo and ArcGIS."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional

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
        features = [lease.to_arcgis_feature() for lease in lease_list]
        response = self.arcgis.upsert_leases(features)
        update_results = response.get("updateResults") or response.get("addResults") or []
        for lease, result in zip(lease_list, update_results):
            global_id = result.get("globalId") if isinstance(result, dict) else None
            object_id = result.get("objectId") if isinstance(result, dict) else None
            if not global_id:
                continue
            geometry_type = None
            if lease.geometry and isinstance(lease.geometry, dict):
                geometry_type = lease.geometry.get("geometryType")
            if geometry_type is None and lease.latitude is not None:
                geometry_type = "point"

            association = LeaseAssociation(
                lease_id=lease.lease_id,
                feature_global_id=global_id,
                feature_object_id=object_id,
                building_id=lease.building_id,
                level_id=lease.level_id,
                unit_id=lease.unit_id,
                geometry_type=geometry_type,
            )
            self.associations.upsert(association)
        return response


__all__ = ["LeaseSynchronizer"]
