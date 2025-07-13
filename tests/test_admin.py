"""
Tests for admin endpoints
"""

import pytest
from fastapi.testclient import TestClient


class TestAdminEndpoints:
    """Test admin endpoints"""
    
    def test_admin_lru_cleanup(self, client: TestClient, admin_auth_headers, test_user):
        """Test admin LRU cleanup endpoint"""
        # Create some clips for cleanup
        auth_response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        user_headers = {"Authorization": f"Bearer {auth_response.json()['access_token']}"}
        
        # Create clips
        for i in range(5):
            client.post("/api/clips/", headers=user_headers, json={
                "title": f"Clip {i}",
                "content": f"Content {i}",
                "clip_type": "text"
            })
        
        # Run cleanup as admin
        response = client.post("/api/admin/cleanup/lru", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "result" in data
        assert "users_processed" in data["result"]
    
    def test_admin_lru_cleanup_unauthorized(self, client: TestClient, auth_headers):
        """Test admin LRU cleanup with non-admin user"""
        response = client.post("/api/admin/cleanup/lru", headers=auth_headers)
        
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]
    
    def test_admin_storage_stats(self, client: TestClient, admin_auth_headers, test_user):
        """Test admin storage statistics endpoint"""
        # Create some test data
        auth_response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        user_headers = {"Authorization": f"Bearer {auth_response.json()['access_token']}"}
        
        # Create clips and files
        client.post("/api/clips/", headers=user_headers, json={
            "title": "Test Clip",
            "content": "Test content",
            "clip_type": "text"
        })
        
        # Get storage stats as admin
        response = client.get("/api/admin/stats/storage", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "clips" in data
        assert "files" in data
        assert data["users"]["total"] >= 2  # test_user + admin_user
        assert data["clips"]["total"] >= 1
    
    def test_admin_storage_stats_unauthorized(self, client: TestClient, auth_headers):
        """Test admin storage stats with non-admin user"""
        response = client.get("/api/admin/stats/storage", headers=auth_headers)
        
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]
    
    def test_admin_endpoints_no_auth(self, client: TestClient):
        """Test admin endpoints without authentication"""
        response = client.post("/api/admin/cleanup/lru")
        assert response.status_code == 401
        
        response = client.get("/api/admin/stats/storage")
        assert response.status_code == 401
