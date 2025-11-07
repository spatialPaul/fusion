"""Client for interacting with the Nuvolo API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterator, Optional

import requests

from .config import NuvoloConfig
from .models import LeaseRecord


@dataclass
class NuvoloClient:
    """Lightweight client that wraps Nuvolo REST API calls."""

    config: NuvoloConfig

    def _token_url(self) -> str:
        return f"{self.config.instance_url}/oauth_token.do"

    def _api_url(self) -> str:
        return f"{self.config.instance_url}{self.config.api_path}"

    def _authenticate(self) -> str:
        response = requests.post(
            self._token_url(),
            data={
                "grant_type": "password",
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "username": self.config.username,
                "password": self.config.password,
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["access_token"]

    def iter_leases(
        self,
        *,
        updated_since: Optional[datetime] = None,
        extra_filters: Optional[Dict[str, str]] = None,
        page_size: int = 100,
    ) -> Iterator[LeaseRecord]:
        """Yield leases matching the provided filters."""

        token = self._authenticate()
        headers = {"Authorization": f"Bearer {token}"}
        params: Dict[str, str] = {"sysparm_limit": str(page_size)}
        if updated_since:
            params["sysparm_query"] = f"sys_updated_on>={updated_since.isoformat()}"
        if extra_filters:
            filters = params.setdefault("sysparm_query", "")
            for key, value in extra_filters.items():
                filters = f"{filters}^" if filters else ""
                filters = f"{filters}{key}={value}"
            params["sysparm_query"] = filters

        url = self._api_url()
        while url:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            for item in data.get("result", []):
                yield self._parse_lease(item)
            link = data.get("link") or {}
            url = link.get("next")
            params = None  # After first page rely on `next` link

    def _parse_lease(self, payload: Dict[str, object]) -> LeaseRecord:
        def _float(value: Optional[str]) -> Optional[float]:
            if value in (None, ""):
                return None
            return float(value)

        def _datetime(value: Optional[str]) -> Optional[datetime]:
            if value in (None, ""):
                return None
            return datetime.fromisoformat(value)

        attributes = {
            key: str(value)
            for key, value in payload.items()
            if key not in {
                "sys_id",
                "name",
                "status",
                "start_date",
                "end_date",
                "lease_type",
                "rent",
                "currency",
                "address",
                "latitude",
                "longitude",
                "building_id",
                "level_id",
                "unit_id",
            }
            and value not in (None, "")
        }

        return LeaseRecord(
            lease_id=str(payload["sys_id"]),
            name=str(payload.get("name", "")),
            status=str(payload.get("status", "")),
            start_date=_datetime(payload.get("start_date")),
            end_date=_datetime(payload.get("end_date")),
            lease_type=payload.get("lease_type"),
            rent=_float(payload.get("rent")),
            currency=payload.get("currency"),
            address=payload.get("address"),
            latitude=_float(payload.get("latitude")),
            longitude=_float(payload.get("longitude")),
            building_id=payload.get("building_id"),
            level_id=payload.get("level_id"),
            unit_id=payload.get("unit_id"),
            attributes=attributes,
        )

    def update_lease(self, lease_id: str, payload: Dict[str, object]) -> Dict[str, object]:
        """Update a lease in Nuvolo with new data."""

        token = self._authenticate()
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.patch(
            f"{self._api_url()}/{lease_id}",
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


__all__ = ["NuvoloClient"]
