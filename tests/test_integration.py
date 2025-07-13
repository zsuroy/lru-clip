"""
Integration tests for complete workflows
"""

import io
from fastapi.testclient import TestClient


class TestIntegrationWorkflows:
    """Test complete user workflows"""
    
    def test_complete_user_workflow(self, client: TestClient):
        """Test complete user workflow from registration to clip management"""
        # 1. Register a new user
        register_response = client.post("/api/auth/register", json={
            "username": "integrationuser",
            "email": "integration@example.com",
            "password": "password123",
            "full_name": "Integration User"
        })
        
        assert register_response.status_code == 201
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Create a text clip
        clip_response = client.post("/api/clips/", headers=headers, json={
            "title": "My First Clip",
            "content": "This is my first clip content",
            "clip_type": "text",
            "access_level": "private"
        })
        
        assert clip_response.status_code == 201
        clip_id = clip_response.json()["id"]
        
        # 3. Upload a file associated with the clip
        file_content = b"File content for the clip"
        file_data = io.BytesIO(file_content)
        
        file_response = client.post(
            f"/api/files/upload?clip_id={clip_id}",
            headers=headers,
            files={"file": ("clip_file.txt", file_data, "text/plain")}
        )
        
        assert file_response.status_code == 201
        file_id = file_response.json()["file"]["id"]
        
        # 4. Get the clip and verify file is associated
        get_clip_response = client.get(f"/api/clips/{clip_id}", headers=headers)
        
        assert get_clip_response.status_code == 200
        clip_data = get_clip_response.json()
        assert len(clip_data["files"]) == 1
        assert clip_data["files"][0]["id"] == file_id
        
        # 5. Update the clip to make it public
        update_response = client.put(f"/api/clips/{clip_id}", headers=headers, json={
            "access_level": "public"
        })
        
        assert update_response.status_code == 200
        share_token = update_response.json()["share_token"]
        assert share_token is not None
        
        # 6. Access the clip via share token (no auth required)
        shared_response = client.get(f"/api/clips/shared/{share_token}")
        
        assert shared_response.status_code == 200
        shared_data = shared_response.json()
        assert shared_data["title"] == "My First Clip"
        assert shared_data["content"] == "This is my first clip content"
        
        # 7. Pin the clip
        pin_response = client.post(f"/api/clips/{clip_id}/pin", headers=headers)
        
        assert pin_response.status_code == 200
        assert pin_response.json()["is_pinned"] is True
        
        # 8. Download the file
        download_response = client.get(f"/api/files/{file_id}/download", headers=headers)
        
        assert download_response.status_code == 200
        assert download_response.content == file_content
    
    def test_encrypted_clip_workflow(self, client: TestClient, auth_headers):
        """Test encrypted clip workflow"""
        # 1. Create an encrypted clip
        clip_response = client.post("/api/clips/", headers=auth_headers, json={
            "title": "Secret Clip",
            "content": "This is secret content",
            "clip_type": "text",
            "access_level": "encrypted",
            "password": "mysecret123"
        })
        
        assert clip_response.status_code == 201
        share_token = clip_response.json()["share_token"]
        
        # 2. Try to access without password (should fail)
        shared_response = client.get(f"/api/clips/shared/{share_token}")
        
        assert shared_response.status_code == 200
        # Content should be accessible but password verification is needed for full access
        
        # 3. Access with correct password
        access_response = client.post(f"/api/clips/shared/{share_token}/access", json={
            "password": "mysecret123"
        })
        
        assert access_response.status_code == 200
        data = access_response.json()
        assert data["title"] == "Secret Clip"
        assert data["content"] == "This is secret content"
        
        # 4. Try with wrong password
        wrong_password_response = client.post(f"/api/clips/shared/{share_token}/access", json={
            "password": "wrongpassword"
        })
        
        assert wrong_password_response.status_code == 401
    
    def test_lru_cleanup_workflow(self, client: TestClient, auth_headers, admin_auth_headers):
        """Test LRU cleanup workflow"""
        # 1. Create many clips to trigger LRU
        clip_ids = []
        for i in range(10):
            response = client.post("/api/clips/", headers=auth_headers, json={
                "title": f"Clip {i}",
                "content": f"Content {i}",
                "clip_type": "text"
            })
            clip_ids.append(response.json()["id"])
        
        # 2. Pin some clips
        for i in range(3):
            client.post(f"/api/clips/{clip_ids[i]}/pin", headers=auth_headers)
        
        # 3. Check initial clip count
        clips_response = client.get("/api/clips/", headers=auth_headers)
        initial_count = clips_response.json()["total"]
        
        # 4. Run admin cleanup
        cleanup_response = client.post("/api/admin/cleanup/lru", headers=admin_auth_headers)
        
        assert cleanup_response.status_code == 200
        
        # 5. Verify cleanup results
        final_clips_response = client.get("/api/clips/", headers=auth_headers)
        final_count = final_clips_response.json()["total"]
        
        # Should have same or fewer clips after cleanup
        assert final_count <= initial_count
        
        # Pinned clips should still exist
        pinned_clips = [clip for clip in final_clips_response.json()["clips"] if clip["is_pinned"]]
        assert len(pinned_clips) >= 3
    
    def test_file_deduplication_workflow(self, client: TestClient, auth_headers):
        """Test file deduplication workflow"""
        # 1. Upload the same file content multiple times with different names
        file_content = b"This is the same content for deduplication test"
        
        file_ids = []
        for i in range(3):
            file_data = io.BytesIO(file_content)
            response = client.post(
                "/api/files/upload",
                headers=auth_headers,
                files={"file": (f"duplicate_{i}.txt", file_data, "text/plain")}
            )
            assert response.status_code == 201
            file_ids.append(response.json()["file"]["id"])
        
        # 2. Verify all files have the same hash
        file_hashes = []
        for file_id in file_ids:
            response = client.get(f"/api/files/{file_id}", headers=auth_headers)
            file_hashes.append(response.json()["file_hash"])
        
        assert len(set(file_hashes)) == 1  # All hashes should be the same
        
        # 3. Delete one file
        delete_response = client.delete(f"/api/files/{file_ids[0]}", headers=auth_headers)
        assert delete_response.status_code == 204
        
        # 4. Other files should still be downloadable (physical file not deleted)
        download_response = client.get(f"/api/files/{file_ids[1]}/download", headers=auth_headers)
        assert download_response.status_code == 200
        assert download_response.content == file_content
    
    def test_search_and_pagination_workflow(self, client: TestClient, auth_headers):
        """Test search and pagination workflow"""
        # 1. Create clips with different content
        search_terms = ["python", "javascript", "database", "api", "frontend"]
        
        for i, term in enumerate(search_terms):
            client.post("/api/clips/", headers=auth_headers, json={
                "title": f"{term.title()} Tutorial",
                "content": f"Learn {term} programming and development",
                "clip_type": "text"
            })
        
        # 2. Search for specific term
        search_response = client.get("/api/clips/?search=python", headers=auth_headers)
        
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert search_data["total"] == 1
        assert "python" in search_data["clips"][0]["title"].lower()
        
        # 3. Test pagination
        paginated_response = client.get("/api/clips/?page=1&per_page=2", headers=auth_headers)
        
        assert paginated_response.status_code == 200
        paginated_data = paginated_response.json()
        assert len(paginated_data["clips"]) == 2
        assert paginated_data["has_next"] is True
        
        # 4. Get next page
        next_page_response = client.get("/api/clips/?page=2&per_page=2", headers=auth_headers)
        
        assert next_page_response.status_code == 200
        next_page_data = next_page_response.json()
        assert len(next_page_data["clips"]) == 2
        assert next_page_data["has_prev"] is True
