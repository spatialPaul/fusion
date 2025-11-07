"""Data models shared between Nuvolo and ArcGIS workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass(slots=True)
class LeaseRecord:
    """Minimal representation of a lease shared between systems."""

    lease_id: str
    name: str
    status: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    lease_type: Optional[str] = None
    rent: Optional[float] = None
    currency: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    building_id: Optional[str] = None
    level_id: Optional[str] = None
    unit_id: Optional[str] = None
    attributes: Dict[str, str] = field(default_factory=dict)

    def to_arcgis_feature(self) -> Dict[str, object]:
        """Convert the record into an ArcGIS feature payload."""

        attributes = {
            "LEASE_ID": self.lease_id,
            "NAME": self.name,
            "STATUS": self.status,
        }
        if self.start_date:
            attributes["START_DATE"] = int(self.start_date.timestamp() * 1000)
        if self.end_date:
            attributes["END_DATE"] = int(self.end_date.timestamp() * 1000)
        if self.lease_type:
            attributes["LEASE_TYPE"] = self.lease_type
        if self.rent is not None:
            attributes["RENT"] = self.rent
        if self.currency:
            attributes["CURRENCY"] = self.currency
        if self.address:
            attributes["ADDRESS"] = self.address
        if self.building_id:
            attributes["FACILITY_ID"] = self.building_id
        if self.level_id:
            attributes["LEVEL_ID"] = self.level_id
        if self.unit_id:
            attributes["UNIT_ID"] = self.unit_id
        attributes.update(self.attributes)

        geometry = None
        if self.latitude is not None and self.longitude is not None:
            geometry = {"x": self.longitude, "y": self.latitude, "spatialReference": {"wkid": 4326}}

        return {"attributes": attributes, "geometry": geometry}


__all__ = ["LeaseRecord"]
