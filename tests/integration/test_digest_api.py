"""Integration tests for Digest API endpoint."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from apps.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_digest_mvp_endpoint_success(client):
    """Test successful digest generation."""
    # Mock the DigestAgent
    with patch("apps.api.routers.digest.DigestAgentMVP") as mock_agent_class:
        mock_agent = AsyncMock()
        mock_agent_class.return_value = mock_agent
        
        # Mock successful response
        mock_agent.process.return_value = AsyncMock(
            status="success",
            result={
                "status": "success",
                "digest": "Test digest content",
                "summary_count": 3,
                "timestamp": "2025-05-17T15:00:00Z"
            }
        )
        
        # Make request
        response = client.post(
            "/api/v1/digest/mvp/",
            json={"user_id": "test_user", "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["digest"] == "Test digest content"
        assert data["summary_count"] == 3
        assert data["timestamp"] == "2025-05-17T15:00:00Z"


def test_digest_mvp_endpoint_error(client):
    """Test error handling in digest generation."""
    # Mock the DigestAgent
    with patch("apps.api.routers.digest.DigestAgentMVP") as mock_agent_class:
        mock_agent = AsyncMock()
        mock_agent_class.return_value = mock_agent
        
        # Mock error response
        mock_agent.process.return_value = AsyncMock(
            status="error",
            result={
                "status": "error",
                "error": "Database connection failed"
            }
        )
        
        # Make request
        response = client.post(
            "/api/v1/digest/mvp/",
            json={"user_id": "test_user", "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert data["error"] == "Database connection failed"


def test_digest_mvp_endpoint_default_params(client):
    """Test digest endpoint with default parameters."""
    # Mock the DigestAgent
    with patch("apps.api.routers.digest.DigestAgentMVP") as mock_agent_class:
        mock_agent = AsyncMock()
        mock_agent_class.return_value = mock_agent
        
        # Mock successful response
        mock_agent.process.return_value = AsyncMock(
            status="success",
            result={
                "status": "success",
                "digest": "Default digest content",
                "summary_count": 5,
                "timestamp": "2025-05-17T15:00:00Z"
            }
        )
        
        # Make request with no parameters
        response = client.post(
            "/api/v1/digest/mvp/",
            json={}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["digest"] == "Default digest content"