"""Global test fixtures."""

import pytest

from life_organizer.auth import verify_api_key
from life_organizer.main import app


@pytest.fixture(autouse=True)
def _bypass_api_key_auth():
    """Bypass API key authentication in all tests."""
    app.dependency_overrides[verify_api_key] = lambda: "test-key"
    yield
    app.dependency_overrides.pop(verify_api_key, None)
