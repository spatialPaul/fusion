"""Client for ArcGIS feature service operations."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional

from .config import ArcGISConfig


if TYPE_CHECKING:  # pragma: no cover - type checking only
    from requests import Session  # noqa: F401
else:
    Session = Any


def _default_session() -> Session:
    try:
        import requests  # type: ignore import-not-found
    except ModuleNotFoundError as exc:  # pragma: no cover - import-time guard
        raise RuntimeError(
            "The 'requests' package is required to use ArcGISClient"
        ) from exc

    session: Session = requests.Session()
    session.headers.update({"User-Agent": "fusion-arcgis-client/1.0"})
    return session


@dataclass
class ArcGISClient:
    """Encapsulates ArcGIS token management and feature service operations."""

    config: ArcGISConfig
    session: Session = field(default_factory=_default_session)
    _token: Optional[str] = None
    _token_expiry: Optional[datetime] = None

    def _generate_token(self) -> None:
        response = self.session.post(
            f"{self.config.portal_url}/sharing/rest/generateToken",
            data={
                "f": "json",
                "username": self.config.username,
                "password": self.config.password,
                "expiration": str(self.config.token_expiration_minutes),
                "client": "referer",
                "referer": self.config.portal_url,
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        token = payload.get("token")
        if not token:
            raise RuntimeError(f"Failed to generate ArcGIS token: {payload}")
        self._token = token
        self._token_expiry = datetime.utcnow() + timedelta(
            minutes=self.config.token_expiration_minutes - 5
        )

    def _ensure_token(self) -> str:
        if (
            not self._token
            or not self._token_expiry
            or datetime.utcnow() >= self._token_expiry
        ):
            self._generate_token()
        assert self._token is not None
        return self._token

    def _features_url(self, action: str) -> str:
        return f"{self.config.feature_service_url}/{action}"

    def upsert_leases(self, features: Iterable[Dict[str, object]]) -> Dict[str, object]:
        token = self._ensure_token()
        feature_list = list(features)
        serialized_features = json.dumps(feature_list)
        response = self.session.post(
            self._features_url("applyEdits"),
            data={
                "f": "json",
                "token": token,
                "adds": "[]",
                "updates": serialized_features,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def query_by_lease_ids(self, lease_ids: List[str]) -> Dict[str, object]:
        if not lease_ids:
            return {"features": []}
        where_clause = "LEASE_ID IN ({})".format(
            ",".join(f"'{lease_id}'" for lease_id in lease_ids)
        )
        return self.query(where=where_clause)

    def query(
        self,
        *,
        where: str = "1=1",
        out_fields: str = "*",
        geometry: Optional[Dict[str, object]] = None,
        spatial_rel: str = "esriSpatialRelIntersects",
        return_geometry: bool = True,
    ) -> Dict[str, object]:
        token = self._ensure_token()
        data = {
            "f": "json",
            "where": where,
            "outFields": out_fields,
            "token": token,
            "returnGeometry": "true" if return_geometry else "false",
            "spatialRel": spatial_rel,
        }
        if geometry is not None:
            data["geometry"] = json.dumps(geometry)
            data["geometryType"] = geometry.get("geometryType", "esriGeometryEnvelope")

        response = self.session.post(
            self._features_url("query"),
            data=data,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def delete_by_lease_ids(self, lease_ids: List[str]) -> Dict[str, object]:
        if not lease_ids:
            return {"deleteResults": []}
        token = self._ensure_token()
        where_clause = "LEASE_ID IN ({})".format(
            ",".join(f"'{lease_id}'" for lease_id in lease_ids)
        )
        response = self.session.post(
            self._features_url("deleteFeatures"),
            data={
                "f": "json",
                "where": where_clause,
                "token": token,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


__all__ = ["ArcGISClient"]
