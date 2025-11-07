"""Command line interface for synchronization tasks."""

from __future__ import annotations

import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from .arcgis_client import ArcGISClient
from .associations import SqliteLeaseAssociationStore
from .config import ArcGISConfig, NuvoloConfig
from .nuvolo_client import NuvoloClient
from .synchronizer import LeaseSynchronizer


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    return datetime.fromisoformat(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Nuvolo ↔ ArcGIS integration toolkit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser(
        "sync-from-nuvolo",
        help="Pull leases from Nuvolo and upsert into ArcGIS",
    )
    sync_parser.add_argument(
        "--since",
        dest="updated_since",
        help="ISO timestamp to filter leases by update time",
    )
    sync_parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of leases to upload in each batch",
    )
    sync_parser.add_argument(
        "--association-store",
        type=Path,
        default=None,
        help="Path to the SQLite database used to persist lease associations",
    )

    list_parser = subparsers.add_parser(
        "list-associations",
        help="Inspect persisted lease associations",
    )
    list_parser.add_argument(
        "--association-store",
        type=Path,
        default=None,
        help="Path to the SQLite database used to persist lease associations",
    )
    return parser


def run(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    nuvolo_config = NuvoloConfig.from_env()
    arcgis_config = ArcGISConfig.from_env()

    store_path = _resolve_store_path(getattr(args, "association_store", None))
    association_store = SqliteLeaseAssociationStore(store_path)

    nuvolo_client = NuvoloClient(nuvolo_config)
    arcgis_client = ArcGISClient(arcgis_config)
    synchronizer = LeaseSynchronizer(nuvolo_client, arcgis_client, association_store)

    if args.command == "sync-from-nuvolo":
        responses = synchronizer.sync_from_nuvolo(
            updated_since=_parse_datetime(args.updated_since),
            batch_size=args.batch_size,
        )
        print(responses)
        return 0

    if args.command == "list-associations":
        for association in association_store.iter_all():
            print(
                f"Lease {association.lease_id} → Global ID {association.feature_global_id}"
            )
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 1


def _resolve_store_path(path: Optional[Path]) -> Path:
    if path:
        return path
    env = os.getenv("FUSION_ASSOCIATION_DB")
    if env:
        return Path(env)
    return Path("lease_associations.db")


if __name__ == "__main__":
    raise SystemExit(run())
