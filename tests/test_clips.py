"""
Tests for clip management endpoints
"""

import pytest
from fastapi.testclient import TestClient
from app.models.clip import ClipType, AccessLevel


class TestClipEndpoints:
    """Test clip management endpoints"""
    
    def test_create_text_clip(self, client: TestClient, auth_headers):
        """Test creating a text clip"""
        response = client.post("/api/clips/", headers=auth_headers, json={
            "title": "Test Clip",
            "content": "This is a test clip content",
            "clip_type": "text",
            "access_level": "private"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Clip"
        assert data["content"] == "This is a test clip content"
        assert data["clip_type"] == "text"
        assert data["access_level"] == "private"
        assert data["is_pinned"] is False
        assert data["access_count"] == 0
    
    def test_create_public_clip(self, client: TestClient, auth_headers):
        """Test creating a public clip"""
        response = client.post("/api/clips/", headers=auth_headers, json={
            "title": "Public Clip",
            "content": "This is public",
            "clip_type": "text",
            "access_level": "public"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["access_level"] == "public"
        assert data["share_token"] is not None
    
    def test_create_encrypted_clip(self, client: TestClient, auth_headers):
        """Test creating an encrypted clip"""
        response = client.post("/api/clips/", headers=auth_headers, json={
            "title": "Encrypted Clip",
            "content": "This is encrypted",
            "clip_type": "text",
            "access_level": "encrypted",
            "password": "secret123"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["access_level"] == "encrypted"
        assert data["share_token"] is not None
    
    def test_get_clips(self, client: TestClient, auth_headers):
        """Test getting user's clips"""
        # Create some clips first
        for i in range(3):
            client.post("/api/clips/", headers=auth_headers, json={
                "title": f"Clip {i}",
                "content": f"Content {i}",
                "clip_type": "text"
            })
        
        response = client.get("/api/clips/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["clips"]) == 3
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["per_page"] == 20
    
    def test_get_clips_pagination(self, client: TestClient, auth_headers):
        """Test clips pagination"""
        # Create 5 clips
        for i in range(5):
            client.post("/api/clips/", headers=auth_headers, json={
                "title": f"Clip {i}",
                "content": f"Content {i}",
                "clip_type": "text"
            })
        
        # Get first page with 2 items per page
        response = client.get("/api/clips/?page=1&per_page=2", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["clips"]) == 2
        assert data["total"] == 5
        assert data["has_next"] is True
        assert data["has_prev"] is False
    
    def test_get_clip_by_id(self, client: TestClient, auth_headers):
        """Test getting a specific clip"""
        # Create a clip
        create_response = client.post("/api/clips/", headers=auth_headers, json={
            "title": "Test Clip",
            "content": "Test content",
            "clip_type": "text"
        })
        clip_id = create_response.json()["id"]
        
        # Get the clip
        response = client.get(f"/api/clips/{clip_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == clip_id
        assert data["title"] == "Test Clip"
        assert data["access_count"] == 1  # Should increment on access
    
    def test_get_nonexistent_clip(self, client: TestClient, auth_headers):
        """Test getting a nonexistent clip"""
        response = client.get("/api/clips/999", headers=auth_headers)
        
        assert response.status_code == 404
        assert "Clip not found" in response.json()["detail"]
    
    def test_update_clip(self, client: TestClient, auth_headers):
        """Test updating a clip"""
        # Create a clip
        create_response = client.post("/api/clips/", headers=auth_headers, json={
            "title": "Original Title",
            "content": "Original content",
            "clip_type": "text"
        })
        clip_id = create_response.json()["id"]
        
        # Update the clip
        response = client.put(f"/api/clips/{clip_id}", headers=auth_headers, json={
            "title": "Updated Title",
            "content": "Updated content"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["content"] == "Updated content"
    
    def test_delete_clip(self, client: TestClient, auth_headers):
        """Test deleting a clip"""
        # Create a clip
        create_response = client.post("/api/clips/", headers=auth_headers, json={
            "title": "To Delete",
            "content": "Will be deleted",
            "clip_type": "text"
        })
        clip_id = create_response.json()["id"]
        
        # Delete the clip
        response = client.delete(f"/api/clips/{clip_id}", headers=auth_headers)
        
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = client.get(f"/api/clips/{clip_id}", headers=auth_headers)
        assert get_response.status_code == 404
    
    def test_pin_clip(self, client: TestClient, auth_headers):
        """Test pinning a clip"""
        # Create a clip
        create_response = client.post("/api/clips/", headers=auth_headers, json={
            "title": "To Pin",
            "content": "Will be pinned",
            "clip_type": "text"
        })
        clip_id = create_response.json()["id"]
        
        # Pin the clip
        response = client.post(f"/api/clips/{clip_id}/pin", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_pinned"] is True
    
    def test_unpin_clip(self, client: TestClient, auth_headers):
        """Test unpinning a clip"""
        # Create and pin a clip
        create_response = client.post("/api/clips/", headers=auth_headers, json={
            "title": "To Unpin",
            "content": "Will be unpinned",
            "clip_type": "text"
        })
        clip_id = create_response.json()["id"]
        
        client.post(f"/api/clips/{clip_id}/pin", headers=auth_headers)
        
        # Unpin the clip
        response = client.delete(f"/api/clips/{clip_id}/pin", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_pinned"] is False
    
    def test_get_shared_clip(self, client: TestClient, auth_headers):
        """Test accessing a shared clip"""
        # Create a public clip
        create_response = client.post("/api/clips/", headers=auth_headers, json={
            "title": "Shared Clip",
            "content": "This is shared",
            "clip_type": "text",
            "access_level": "public"
        })
        share_token = create_response.json()["share_token"]
        
        # Access the shared clip (no auth required)
        response = client.get(f"/api/clips/shared/{share_token}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Shared Clip"
        assert data["content"] == "This is shared"
    
    def test_access_encrypted_clip(self, client: TestClient, auth_headers):
        """Test accessing an encrypted shared clip"""
        # Create an encrypted clip
        create_response = client.post("/api/clips/", headers=auth_headers, json={
            "title": "Encrypted Clip",
            "content": "This is encrypted",
            "clip_type": "text",
            "access_level": "encrypted",
            "password": "secret123"
        })
        share_token = create_response.json()["share_token"]
        
        # Access with correct password
        response = client.post(f"/api/clips/shared/{share_token}/access", json={
            "password": "secret123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Encrypted Clip"
        assert data["content"] == "This is encrypted"
        
        # Access with wrong password
        response = client.post(f"/api/clips/shared/{share_token}/access", json={
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert "Incorrect password" in response.json()["detail"]
    
    def test_search_clips(self, client: TestClient, auth_headers):
        """Test searching clips"""
        # Create clips with different content
        client.post("/api/clips/", headers=auth_headers, json={
            "title": "Python Tutorial",
            "content": "Learn Python programming",
            "clip_type": "text"
        })
        client.post("/api/clips/", headers=auth_headers, json={
            "title": "JavaScript Guide",
            "content": "Learn JavaScript basics",
            "clip_type": "text"
        })
        
        # Search for "Python"
        response = client.get("/api/clips/?search=Python", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["clips"]) == 1
        assert "Python" in data["clips"][0]["title"]
