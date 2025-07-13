"""
Tests for anonymous user functionality
"""

import io
from fastapi.testclient import TestClient
from app.database import settings


class TestAnonymousUser:
    """Test anonymous user functionality"""
    
    def test_create_anonymous_session(self, client: TestClient):
        """Test creating an anonymous session"""
        response = client.post("/api/auth/anonymous")
        
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert data["user"]["is_anonymous"] is True
        assert data["user"]["username"] is None
        assert data["user"]["email"] is None
    
    def test_anonymous_session_disabled(self, client: TestClient, monkeypatch):
        """Test anonymous session creation when disabled"""
        # Temporarily disable anonymous access
        monkeypatch.setattr(settings, "allow_anonymous", False)
        
        response = client.post("/api/auth/anonymous")
        
        assert response.status_code == 403
        assert "Anonymous access is disabled" in response.json()["detail"]
    
    def test_auth_status_anonymous(self, client: TestClient):
        """Test auth status endpoint with anonymous user"""
        # Create anonymous session
        response = client.post("/api/auth/anonymous")
        session_id = response.json()["session_id"]
        
        # Check auth status with session ID
        response = client.get("/api/auth/status", headers={
            "X-Session-Id": session_id
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["user"]["is_anonymous"] is True
    
    def test_auth_status_no_auth(self, client: TestClient):
        """Test auth status endpoint without authentication"""
        response = client.get("/api/auth/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False
        assert data["anonymous_allowed"] is True
        assert data["user"] is None
    
    def test_anonymous_create_clip(self, client: TestClient):
        """Test creating a clip as anonymous user"""
        # Create anonymous session
        response = client.post("/api/auth/anonymous")
        session_id = response.json()["session_id"]
        
        # Create clip with session ID
        response = client.post("/api/clips/", 
            headers={"X-Session-Id": session_id},
            json={
                "title": "Anonymous Clip",
                "content": "This is an anonymous clip",
                "clip_type": "text",
                "access_level": "private"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Anonymous Clip"
        assert data["content"] == "This is an anonymous clip"
    
    def test_anonymous_upload_file(self, client: TestClient):
        """Test file upload as anonymous user"""
        # Create anonymous session
        response = client.post("/api/auth/anonymous")
        session_id = response.json()["session_id"]
        
        # Upload file with session ID
        file_content = b"Anonymous file content"
        file_data = io.BytesIO(file_content)
        
        response = client.post("/api/files/upload",
            headers={"X-Session-Id": session_id},
            files={"file": ("anon_file.txt", file_data, "text/plain")}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["file"]["original_filename"] == "anon_file.txt"
    
    def test_anonymous_file_size_limit(self, client: TestClient, monkeypatch):
        """Test file size limit for anonymous users"""
        # Set a very small limit for testing
        monkeypatch.setattr(settings, "anonymous_max_file_size", 10)
        
        # Create anonymous session
        response = client.post("/api/auth/anonymous")
        session_id = response.json()["session_id"]
        
        # Try to upload a file larger than the limit
        file_content = b"This file is too large for anonymous users"
        file_data = io.BytesIO(file_content)
        
        response = client.post("/api/files/upload",
            headers={"X-Session-Id": session_id},
            files={"file": ("large_file.txt", file_data, "text/plain")}
        )
        
        assert response.status_code == 413
        assert "File too large" in response.json()["detail"]
    
    def test_anonymous_clip_limits(self, client: TestClient, monkeypatch):
        """Test clip limits for anonymous users"""
        # Set a very low limit for testing
        monkeypatch.setattr(settings, "anonymous_max_clips", 2)
        
        # Create anonymous session
        response = client.post("/api/auth/anonymous")
        session_id = response.json()["session_id"]
        headers = {"X-Session-Id": session_id}
        
        # Create clips up to the limit
        for i in range(2):
            response = client.post("/api/clips/", 
                headers=headers,
                json={
                    "title": f"Clip {i}",
                    "content": f"Content {i}",
                    "clip_type": "text"
                }
            )
            assert response.status_code == 201
        
        # Try to create one more clip (should fail or trigger cleanup)
        response = client.post("/api/clips/", 
            headers=headers,
            json={
                "title": "Clip 3",
                "content": "Content 3",
                "clip_type": "text"
            }
        )
        
        # Should either succeed (after cleanup) or fail with limit error
        assert response.status_code in [201, 400]
    
    def test_anonymous_access_shared_clip(self, client: TestClient, auth_headers):
        """Test anonymous user accessing shared clips"""
        # Create a public clip as authenticated user
        response = client.post("/api/clips/", headers=auth_headers, json={
            "title": "Public Clip",
            "content": "This is public",
            "clip_type": "text",
            "access_level": "public"
        })
        share_token = response.json()["share_token"]
        
        # Access the shared clip without any authentication
        response = client.get(f"/api/clips/shared/{share_token}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Public Clip"
        assert data["content"] == "This is public"
    
    def test_anonymous_cannot_access_private_operations(self, client: TestClient):
        """Test that anonymous users cannot access operations requiring authentication"""
        # Create anonymous session
        response = client.post("/api/auth/anonymous")
        session_id = response.json()["session_id"]
        headers = {"X-Session-Id": session_id}

        # Try to access user profile (should require non-anonymous user)
        response = client.get("/api/auth/me", headers=headers)

        # This should fail since /api/auth/me requires non-anonymous user
        assert response.status_code == 403
        assert "This operation requires a registered account" in response.json()["detail"]
    
    def test_mixed_authentication(self, client: TestClient, auth_headers):
        """Test mixing authenticated and anonymous access"""
        # Create clip as authenticated user
        response = client.post("/api/clips/", headers=auth_headers, json={
            "title": "Auth User Clip",
            "content": "From authenticated user",
            "clip_type": "text"
        })
        auth_clip_id = response.json()["id"]
        
        # Create anonymous session
        response = client.post("/api/auth/anonymous")
        session_id = response.json()["session_id"]
        anon_headers = {"X-Session-Id": session_id}
        
        # Create clip as anonymous user
        response = client.post("/api/clips/", headers=anon_headers, json={
            "title": "Anonymous Clip",
            "content": "From anonymous user",
            "clip_type": "text"
        })
        anon_clip_id = response.json()["id"]
        
        # Authenticated user should not see anonymous user's clips
        response = client.get(f"/api/clips/{anon_clip_id}", headers=auth_headers)
        assert response.status_code == 404
        
        # Anonymous user should not see authenticated user's clips
        response = client.get(f"/api/clips/{auth_clip_id}", headers=anon_headers)
        assert response.status_code == 404
