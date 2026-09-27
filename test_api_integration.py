import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def client():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    # Import app modules only after DATABASE_URL is set, and force this
    # test's engine/session onto the already-imported singletons so every
    # module that did `from app.db.session import engine` sees the same
    # isolated per-test database.
    from app.db import session as db_session
    test_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    db_session.engine = test_engine
    db_session.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    from app.main import app
    db_session.Base.metadata.create_all(bind=test_engine)

    with TestClient(app) as test_client:
        yield test_client

    os.remove(db_path)


def _auth_headers(client, email="amin@example.com", password="a-strong-password"):
    client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": "Amin"})
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_and_login(client):
    headers = _auth_headers(client)
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "amin@example.com"


def test_cannot_access_buildings_without_token(client):
    response = client.get("/api/v1/buildings")
    assert response.status_code == 401


def test_buildings_are_owner_scoped(client):
    headers_a = _auth_headers(client, email="a@example.com")
    headers_b = _auth_headers(client, email="b@example.com")

    building_payload = {"project_name": "Home A", "area_m2": 100, "occupants": 3}
    created = client.post("/api/v1/buildings", json=building_payload, headers=headers_a)
    assert created.status_code == 200
    building_id = created.json()["id"]

    # Owner can see it.
    assert client.get(f"/api/v1/buildings/{building_id}", headers=headers_a).status_code == 200
    # A different account cannot.
    assert client.get(f"/api/v1/buildings/{building_id}", headers=headers_b).status_code == 404
    # Listing only returns your own buildings.
    assert len(client.get("/api/v1/buildings", headers=headers_b).json()) == 0
    assert len(client.get("/api/v1/buildings", headers=headers_a).json()) == 1


def test_catalog_endpoints_are_public_reference_data(client):
    envelope = client.get("/api/v1/catalogs/envelope?category=wall")
    assert envelope.status_code == 200
    assert all(item["category"] == "wall" for item in envelope.json())

    equipment = client.get("/api/v1/catalogs/equipment?fuel=gas")
    assert equipment.status_code == 200
    assert all(item["fuel"] == "gas" for item in equipment.json())


def test_full_audit_pipeline_end_to_end(client):
    headers = _auth_headers(client)
    building_payload = {
        "project_name": "Test Home",
        "city": "جاجرم",
        "area_m2": 150,
        "floors": 1,
        "occupants": 4,
        "climate_zone": "cold",
        "wall_material_key": "wall_brick_single_wythe",
        "roof_material_key": "roof_flat_uninsulated",
        "window_material_key": "window_single_aluminum",
        "airtightness": "leaky",
        "heating_system": "old gas heater",
        "window_type": "single glazing",
    }
    building = client.post("/api/v1/buildings", json=building_payload, headers=headers).json()
    building_id = building["id"]

    bills = [
        {"year": 2025, "month": month, "electricity_kwh": 300 + (100 if month in (6, 7, 8) else 0), "gas_m3": 300 if month in (11, 12, 1, 2) else 30}
        for month in range(1, 13)
    ]
    bills_response = client.post(f"/api/v1/buildings/{building_id}/bills", json=bills, headers=headers)
    assert bills_response.status_code == 200

    weather = []
    month_temps = {1: -2, 2: 1, 3: 8, 4: 15, 5: 21, 6: 28, 7: 32, 8: 30, 9: 24, 10: 16, 11: 7, 12: 0}
    for month, temp in month_temps.items():
        weather.append({"date": f"2025-{month:02d}-15", "temp_avg": temp})
    weather_response = client.post(f"/api/v1/buildings/{building_id}/weather", json=weather, headers=headers)
    assert weather_response.status_code == 200

    audit_response = client.post(f"/api/v1/buildings/{building_id}/audit/run", headers=headers)
    assert audit_response.status_code == 200, audit_response.text
    audit = audit_response.json()

    assert audit["energy_rating"] in {"A", "B", "C", "D", "E"}
    assert audit["theoretical_heating_mj"] > 0
    assert audit["envelope_breakdown"] is not None
    assert audit["carbon_footprint"]["total_co2_kg"] > 0
    assert audit["performance_score"] is not None

    # This building has poor envelope materials by construction -- the
    # sensitivity-ranked recommendations should surface at least one
    # physics-based envelope opportunity, and it should be quantified.
    envelope_recs = [item for item in audit["recommendations"] if item["category"] == "envelope"]
    assert len(envelope_recs) > 0
    assert envelope_recs[0]["quantified"] is True
    assert envelope_recs[0]["estimated_annual_savings_toman"] > 0

    # Recommendations should be sorted by financial impact, descending.
    tomans = [item.get("estimated_annual_savings_toman") or 0 for item in audit["recommendations"]]
    assert tomans == sorted(tomans, reverse=True)

    # latest_audit should return without recomputing a new stored row.
    latest_response = client.get(f"/api/v1/buildings/{building_id}/audit/latest", headers=headers)
    assert latest_response.status_code == 200

    # Report generation must not crash with the expanded result shape.
    pdf_response = client.get(f"/api/v1/buildings/{building_id}/reports/pdf", headers=headers)
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"

    excel_response = client.get(f"/api/v1/buildings/{building_id}/reports/excel", headers=headers)
    assert excel_response.status_code == 200


def test_audit_requires_at_least_12_bills(client):
    headers = _auth_headers(client)
    building = client.post("/api/v1/buildings", json={"project_name": "Too few bills", "area_m2": 80, "occupants": 2}, headers=headers).json()
    response = client.post(f"/api/v1/buildings/{building['id']}/bills", json=[{"year": 2025, "month": 1, "electricity_kwh": 200, "gas_m3": 20}], headers=headers)
    assert response.status_code == 200
    audit_response = client.post(f"/api/v1/buildings/{building['id']}/audit/run", headers=headers)
    assert audit_response.status_code == 400
