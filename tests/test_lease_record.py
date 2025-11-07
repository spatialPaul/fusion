from __future__ import annotations

from datetime import datetime

from fusion.associations import LeaseAssociation
from fusion.models import LeaseRecord


def test_to_arcgis_feature_builds_attributes_and_geometry() -> None:
    lease = LeaseRecord(
        lease_id="lease-1",
        name="HQ",
        status="active",
        start_date=datetime(2024, 1, 1, 8, 0, 0),
        end_date=datetime(2025, 1, 1, 8, 0, 0),
        lease_type="office",
        rent=1200.5,
        currency="USD",
        address="123 Main St",
        latitude=35.7796,
        longitude=-78.6382,
        building_id="BLDG-1",
        level_id="L1",
        unit_id="U101",
        attributes={"CUSTOM": "VALUE"},
    )

    feature = lease.to_arcgis_feature()

    attrs = feature["attributes"]
    assert attrs["LEASE_ID"] == "lease-1"
    assert attrs["NAME"] == "HQ"
    assert attrs["STATUS"] == "active"
    assert attrs["LEASE_TYPE"] == "office"
    assert attrs["RENT"] == 1200.5
    assert attrs["CURRENCY"] == "USD"
    assert attrs["ADDRESS"] == "123 Main St"
    assert attrs["FACILITY_ID"] == "BLDG-1"
    assert attrs["LEVEL_ID"] == "L1"
    assert attrs["UNIT_ID"] == "U101"
    assert attrs["CUSTOM"] == "VALUE"

    geometry = feature["geometry"]
    assert geometry["x"] == -78.6382
    assert geometry["y"] == 35.7796
    assert geometry["spatialReference"] == {"wkid": 4326}


def test_geometry_precedence_over_lat_lon() -> None:
    lease = LeaseRecord(
        lease_id="lease-1",
        name="Indoor Suite",
        status="active",
        geometry={
            "rings": [
                [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]],
            ],
            "spatialReference": {"wkid": 3857},
        },
    )

    feature = lease.to_arcgis_feature()
    assert feature["geometry"]["spatialReference"] == {"wkid": 3857}
    assert "x" not in feature["geometry"]


def test_to_arcgis_feature_respects_existing_association() -> None:
    lease = LeaseRecord(lease_id="lease-1", name="HQ", status="active")
    association = LeaseAssociation(
        lease_id="lease-1",
        feature_global_id="{ABCDEF}",
        feature_object_id=77,
    )

    feature = lease.to_arcgis_feature(association)
    attrs = feature["attributes"]
    assert attrs["OBJECTID"] == 77
    assert attrs["GlobalID"] == "{ABCDEF}"
