"""
API endpoint tests
"""
import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "CSPM" in response.json()["message"]


def test_health_endpoint():
    """Test health check"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_cloud_accounts():
    """Test getting cloud accounts"""
    response = client.get("/api/cloud-accounts/")
    assert response.status_code == 200
    # Should return a list (might be empty)
    assert isinstance(response.json(), list)


def test_login_endpoint():
    """Test login endpoint"""
    login_data = {
        "username": "admin",
        "password": "testpass123"
    }
    
    response = client.post(
        "/api/auth/login",
        data=login_data,  # OAuth2 uses form data
    )
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_prowler_checks():
    """Test getting Prowler checks catalog"""
    response = client.get("/api/scans/prowler-checks")
    assert response.status_code == 200
    assert "count" in response.json()
    assert "checks" in response.json()