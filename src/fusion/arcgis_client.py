"""Client for ArcGIS feature service operations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional

import requests

from .config import ArcGISConfig


@dataclass
class ArcGISClient:
    """Encapsulates ArcGIS token management and feature service operations."""

    config: ArcGISConfig
    _token: Optional[str] = None
    _token_expiry: Optional[datetime] = None

    def _generate_token(self) -> None:
        response = requests.post(
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
        if "token" not in payload:
            raise RuntimeError(f"Failed to generate ArcGIS token: {payload}")
        self._token = payload["token"]
        self._token_expiry = datetime.utcnow() + timedelta(
            minutes=self.config.token_expiration_minutes - 5
        )

    def _ensure_token(self) -> str:
        if not self._token or not self._token_expiry or datetime.utcnow() >= self._token_expiry:
            self._generate_token()
        assert self._token is not None
        return self._token

    def _features_url(self, action: str) -> str:
        return f"{self.config.feature_service_url}/{action}"

    def upsert_leases(self, features: Iterable[Dict[str, object]]) -> Dict[str, object]:
        token = self._ensure_token()
        serialized_features = json.dumps(list(features))
        response = requests.post(
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
        token = self._ensure_token()
        where_clause = "LEASE_ID IN ({})".format(
            ",".join(f"'{lease_id}'" for lease_id in lease_ids)
        )
        response = requests.post(
            self._features_url("query"),
            data={
                "f": "json",
                "where": where_clause,
                "outFields": "*",
                "token": token,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def delete_by_lease_ids(self, lease_ids: List[str]) -> Dict[str, object]:
        token = self._ensure_token()
        where_clause = "LEASE_ID IN ({})".format(
            ",".join(f"'{lease_id}'" for lease_id in lease_ids)
        )
        response = requests.post(
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
