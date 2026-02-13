"""Tests for the main FastAPI application."""

from fastapi.testclient import TestClient

from life_organizer.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns API information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Life Organizer Backend API"
    assert "version" in data
    assert "api_version" in data
    assert "docs" in data


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "life-organizer-backend"
    assert "version" in data


def test_health_check_versioned():
    """Test the versioned health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_api_status():
    """Test the API status endpoint."""
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["api_version"] == "v1"
    assert "debug" in data
    assert "endpoints" in data


def test_process_rejects_reminder_category():
    """Test POST /api/v1/process returns 422 for deprecated 'reminder' category."""
    response = client.post(
        "/api/v1/process",
        json={"input": "Call the dentist", "category": "reminder"},
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
