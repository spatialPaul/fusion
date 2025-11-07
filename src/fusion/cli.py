"""Command line interface for synchronization tasks."""

from __future__ import annotations

import argparse
from datetime import datetime
from typing import Optional

from .arcgis_client import ArcGISClient
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
    return parser


def run(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    nuvolo_config = NuvoloConfig.from_env()
    arcgis_config = ArcGISConfig.from_env()

    nuvolo_client = NuvoloClient(nuvolo_config)
    arcgis_client = ArcGISClient(arcgis_config)
    synchronizer = LeaseSynchronizer(nuvolo_client, arcgis_client)

    if args.command == "sync-from-nuvolo":
        responses = synchronizer.sync_from_nuvolo(
            updated_since=_parse_datetime(args.updated_since),
            batch_size=args.batch_size,
        )
        print(responses)
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(run())
