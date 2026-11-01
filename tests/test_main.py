"""Tests for the main FastAPI application."""

from importlib.metadata import version

from fastapi.testclient import TestClient

import life_organizer
from life_organizer.main import app

client = TestClient(app)

PACKAGE_VERSION = version("life-organizer")


def test_root_endpoint():
    """Test the root endpoint returns API information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Life Organizer Backend API"
    assert data["version"] == PACKAGE_VERSION
    assert "api_version" in data


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "life-organizer-backend"
    assert data["version"] == PACKAGE_VERSION


def test_health_check_versioned():
    """Test the versioned health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_health_check_versioned_reports_package_version():
    """The versioned health endpoint reports the installed package version."""
    assert client.get("/api/v1/health").json()["version"] == PACKAGE_VERSION


def test_app_version_is_package_version():
    """The FastAPI app carries the installed package version."""
    assert app.version == PACKAGE_VERSION


def test_package_dunder_version_is_package_version():
    """life_organizer.__version__ comes from package metadata."""
    assert life_organizer.__version__ == PACKAGE_VERSION


def test_api_status():
    """Test the API status endpoint."""
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["api_version"] == "v1"
    assert "debug" in data
    assert "debug" in data


def test_process_endpoint_removed():
    """Test POST /api/v1/process returns 404 (endpoint no longer exists)."""
    response = client.post(
        "/api/v1/process",
        json={"input": "Call the dentist", "category": "reminder"},
    )
    assert response.status_code == 404


def test_no_meals_routes_registered():
    """No route is registered under /api/v1/meals."""
    paths = [getattr(route, "path", "") for route in app.routes]
    assert [p for p in paths if p.startswith("/api/v1/meals")] == []


def test_openapi_has_no_meals_paths():
    """The generated OpenAPI schema lists no meals path."""
    assert [p for p in app.openapi()["paths"] if "/meals" in p] == []


def test_meals_endpoints_removed():
    """The former meals endpoints return 404."""
    assert client.post("/api/v1/meals/suggest", json={}).status_code == 404
    response = client.post("/api/v1/meals/feedback", json={"recipe_name": "x", "liked": True})
    assert response.status_code == 404


def test_app_description_describes_budget_api():
    """The app description names the budget API, not a voice assistant."""
    description = app.description.lower()
    assert "budget" in description
    assert "voice" not in description
