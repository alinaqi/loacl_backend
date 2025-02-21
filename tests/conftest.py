"""
Pytest configuration file.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

@pytest.fixture
def client() -> TestClient:
    """Create a test client fixture."""
    return TestClient(app)
