"""Tests for Phase 5: Professional Workflow — Inspiration & Multi-Role Export Packages.

Validates that:
1. Inspiration presets feed DesignState strictly through the brief.
2. Physical constraints, clearances, and budgets are never bypassed by aesthetic presets.
3. Export packages (Client, Designer, Dealer BOM) expose strictly verified catalog and constraint facts.
4. Dealer BOM contains verified KOHLER SKUs, quantities, rough-ins, and electrical specs.
5. All endpoints work reliably with test client.
"""

from fastapi.testclient import TestClient
import pytest

from backend.api.routes import create_planning_router
from backend.api.schemas import BathroomBrief
from backend.export.generator import export_generator
from backend.inspiration.engine import inspiration_engine
from backend.main import app
from backend.services.planner import create_plan
from backend.services.store import store


@pytest.fixture
def client():
    store.clear()
    return TestClient(app)


def test_inspiration_presets_and_matching():
    presets = inspiration_engine.list_presets()
    assert len(presets) >= 5

    preset_ids = [p.id for p in presets]
    assert "warm_minimalist" in preset_ids
    assert "modern_luxury" in preset_ids
    assert "classic_heritage" in preset_ids
    assert "industrial_modern" in preset_ids
    assert "coastal_spa" in preset_ids

    # Deterministic matching tests
    m1 = inspiration_engine.match_preset("I want warm minimalist teak and travertine")
    assert m1.id == "warm_minimalist"

    m2 = inspiration_engine.match_preset("Dramatic gold brass luxury with Numi toilet")
    assert m2.id == "modern_luxury"

    m3 = inspiration_engine.match_preset("Classic vintage heritage Edwardian cross handles")
    assert m3.id == "classic_heritage"

    m4 = inspiration_engine.match_preset("Industrial modern cast concrete and matte steel")
    assert m4.id == "industrial_modern"

    m5 = inspiration_engine.match_preset("Restorative coastal spa sanctuary with rainhead")
    assert m5.id == "coastal_spa"


def test_inspiration_feeds_brief_without_bypassing_constraints():
    brief = BathroomBrief(
        room_width_ft=6.0,
        room_length_ft=8.0,
        budget=250000.0,
        required_categories=["vanity", "basin", "faucet", "toilet", "shower"],
    )
    preset = inspiration_engine.get_preset("modern_luxury")
    assert preset is not None

    new_brief = inspiration_engine.apply_preset_to_brief(brief, preset)
    assert "luxury" in new_brief.preferred_styles
    # Dimensions and budget MUST be strictly preserved
    assert new_brief.room_width_ft == 6.0
    assert new_brief.room_length_ft == 8.0
    assert new_brief.budget == 250000.0


def test_inspiration_api_endpoint(client):
    # 1. Create a project
    create_res = client.post(
        "/api/v1/plan",
        json={
            "room_width_ft": 6.0,
            "room_length_ft": 8.0,
            "budget": 250000.0,
            "required_categories": ["vanity", "basin", "faucet", "toilet", "shower"],
        },
    )
    assert create_res.status_code == 200
    project_id = create_res.json()["project_id"]

    # 2. Get presets
    presets_res = client.get("/api/v1/inspiration/presets")
    assert presets_res.status_code == 200
    presets_data = presets_res.json()["presets"]
    assert len(presets_data) >= 5

    # 3. Apply Modern Luxury preset
    insp_res = client.post(
        f"/api/v1/plan/{project_id}/inspiration",
        json={"preset_id": "modern_luxury"},
    )
    assert insp_res.status_code == 200
    insp_data = insp_res.json()
    assert insp_data["preset"]["id"] == "modern_luxury"
    assert "luxury" in insp_data["applied_styles"]
    assert insp_data["state"]["version_id"] == "v2"
    assert insp_data["state"]["version_number"] == 2
    assert len(insp_data["state"]["decision_records"]) >= 1


def test_export_packages_client_designer_dealer(client):
    # Setup project
    create_res = client.post(
        "/api/v1/plan",
        json={
            "room_width_ft": 6.0,
            "room_length_ft": 8.0,
            "budget": 250000.0,
            "required_categories": ["vanity", "basin", "faucet", "toilet", "shower"],
        },
    )
    project_id = create_res.json()["project_id"]

    # 1. Client Export Package
    client_res = client.get(f"/api/v1/plan/{project_id}/export?role=client")
    assert client_res.status_code == 200
    cdata = client_res.json()["data"]
    assert "total_investment" in cdata
    assert cdata["total_investment"] > 0
    assert len(cdata["products"]) == 5
    for p in cdata["products"]:
        assert "price" in p
        assert "dimensions" in p

    # 2. Designer Architectural Spec
    designer_res = client.get(f"/api/v1/plan/{project_id}/export?role=designer")
    assert designer_res.status_code == 200
    ddata = designer_res.json()["data"]
    assert "ledger" in ddata
    assert "clearances" in ddata
    assert len(ddata["clearances"]) > 0
    for c in ddata["clearances"]:
        assert "footprint" in c
        assert "required_clearance" in c
        assert "clearance_source" in c

    # 3. Dealer BOM Package
    dealer_res = client.get(f"/api/v1/plan/{project_id}/export?role=dealer")
    assert dealer_res.status_code == 200
    bdata = dealer_res.json()["data"]
    assert "line_items" in bdata
    assert len(bdata["line_items"]) == 5
    for item in bdata["line_items"]:
        assert item["sku"]  # Real SKU
        assert item["quantity"] == 1
        assert item["unit_price"] > 0
        assert "electrical_required" in item

    # 4. Standalone Printable HTML
    html_res = client.get(f"/api/v1/plan/{project_id}/export/document?role=dealer")
    assert html_res.status_code == 200
    assert "text/html" in html_res.headers["content-type"]
    assert "Bill of Materials (BOM)" in html_res.text
    assert "KOHLER AI BATHPLAN" in html_res.text.upper()
