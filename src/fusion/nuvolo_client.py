"""Client for interacting with the Nuvolo API."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional

from .config import NuvoloConfig
from .models import LeaseRecord


if TYPE_CHECKING:  # pragma: no cover - type checking only
    from requests import Session  # noqa: F401
else:
    Session = Any


def _default_session() -> Session:
    try:
        import requests  # type: ignore import-not-found
    except ModuleNotFoundError as exc:  # pragma: no cover - import-time guard
        raise RuntimeError(
            "The 'requests' package is required to use NuvoloClient"
        ) from exc

    session: Session = requests.Session()
    session.headers.update({"User-Agent": "fusion-nuvolo-client/1.0"})
    return session


@dataclass
class NuvoloClient:
    """Lightweight client that wraps Nuvolo REST API calls."""

    config: NuvoloConfig
    session: Session = field(default_factory=_default_session)

    def _token_url(self) -> str:
        return f"{self.config.instance_url}/oauth_token.do"

    def _api_url(self) -> str:
        return f"{self.config.instance_url}{self.config.api_path}"

    def _authenticate(self) -> str:
        response = self.session.post(
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
        token = payload.get("access_token")
        if not token:
            raise RuntimeError(f"Nuvolo authentication failed: {payload}")
        return token

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
            response = self.session.get(url, headers=headers, params=params, timeout=30)
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
                "geometry",
            }
            and value not in (None, "")
        }

        geometry: Optional[Dict[str, object]] = None
        geometry_payload = payload.get("geometry")
        if isinstance(geometry_payload, dict):
            geometry = geometry_payload
        elif isinstance(geometry_payload, str):
            try:
                geometry = json.loads(geometry_payload)
            except json.JSONDecodeError:
                geometry = None

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
            geometry=geometry,
            attributes=attributes,
        )

    def update_lease(self, lease_id: str, payload: Dict[str, object]) -> Dict[str, object]:
        """Update a lease in Nuvolo with new data."""

        token = self._authenticate()
        headers = {"Authorization": f"Bearer {token}"}
        response = self.session.patch(
            f"{self._api_url()}/{lease_id}",
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


__all__ = ["NuvoloClient"]
