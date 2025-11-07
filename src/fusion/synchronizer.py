"""Synchronization utilities for Nuvolo and ArcGIS."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional

from .arcgis_client import ArcGISClient
from .models import LeaseRecord
from .nuvolo_client import NuvoloClient


@dataclass
class LeaseSynchronizer:
    """Coordinates synchronization of lease records between Nuvolo and ArcGIS."""

    nuvolo: NuvoloClient
    arcgis: ArcGISClient

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
                responses.append(self._push_to_arcgis(batch))
                batch.clear()
        if batch:
            responses.append(self._push_to_arcgis(batch))
        return responses

    def _push_to_arcgis(self, leases: Iterable[LeaseRecord]) -> dict:
        features = [lease.to_arcgis_feature() for lease in leases]
        return self.arcgis.upsert_leases(features)


__all__ = ["LeaseSynchronizer"]
