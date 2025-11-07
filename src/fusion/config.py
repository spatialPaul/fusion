"""Configuration helpers for Nuvolo and ArcGIS integrations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import os


@dataclass(slots=True)
class NuvoloConfig:
    """Configuration values required to call the Nuvolo API."""

    instance_url: str
    client_id: str
    client_secret: str
    username: str
    password: str
    api_path: str = "/api/x_nuvo_cmdb/leases"

    @classmethod
    def from_env(cls, prefix: str = "NUVOLO") -> "NuvoloConfig":
        """Create a :class:`NuvoloConfig` from environment variables."""

        def _env(name: str, *, optional: bool = False) -> Optional[str]:
            value = os.getenv(f"{prefix}_{name}")
            if value is None and not optional:
                raise RuntimeError(f"Missing environment variable: {prefix}_{name}")
            return value

        return cls(
            instance_url=_env("INSTANCE_URL"),
            client_id=_env("CLIENT_ID"),
            client_secret=_env("CLIENT_SECRET"),
            username=_env("USERNAME"),
            password=_env("PASSWORD"),
            api_path=_env("API_PATH", optional=True) or "/api/x_nuvo_cmdb/leases",
        )


@dataclass(slots=True)
class ArcGISConfig:
    """Configuration for interacting with an ArcGIS feature service."""

    portal_url: str
    username: str
    password: str
    feature_service_url: str
    token_expiration_minutes: int = 120

    @classmethod
    def from_env(cls, prefix: str = "ARCGIS") -> "ArcGISConfig":
        """Create a :class:`ArcGISConfig` from environment variables."""

        def _env(name: str) -> str:
            value = os.getenv(f"{prefix}_{name}")
            if value is None:
                raise RuntimeError(f"Missing environment variable: {prefix}_{name}")
            return value

        return cls(
            portal_url=_env("PORTAL_URL"),
            username=_env("USERNAME"),
            password=_env("PASSWORD"),
            feature_service_url=_env("FEATURE_SERVICE_URL"),
            token_expiration_minutes=int(
                os.getenv(f"{prefix}_TOKEN_EXPIRATION_MINUTES", "120")
            ),
        )


__all__ = ["ArcGISConfig", "NuvoloConfig"]
