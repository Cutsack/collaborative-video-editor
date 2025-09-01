"""
Basic tests for the FastAPI application
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Collaborative Video Editor API" in response.json()["message"]


def test_api_docs():
    """Test API documentation endpoints"""
    response = client.get("/docs")
    assert response.status_code == 200
    
    response = client.get("/redoc")
    assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__])
