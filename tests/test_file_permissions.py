"""
Tests for file download permissions and access control
"""

import io
from fastapi.testclient import TestClient


class TestFilePermissions:
    """Test file download permissions"""
    
    def test_owner_can_download_private_file(self, client: TestClient, auth_headers):
        """Test that file owner can download their private files"""
        # Upload a file
        file_content = b"Private file content"
        file_data = io.BytesIO(file_content)
        
        response = client.post(
            "/api/files/upload",
            headers=auth_headers,
            files={"file": ("private.txt", file_data, "text/plain")}
        )
        
        assert response.status_code == 201
        file_id = response.json()["file"]["id"]
        
        # Owner should be able to download
        download_response = client.get(f"/api/files/{file_id}/download", headers=auth_headers)
        
        assert download_response.status_code == 200
        assert download_response.content == file_content
    
    def test_anonymous_cannot_download_private_file(self, client: TestClient, auth_headers):
        """Test that anonymous users cannot download private files"""
        # Upload a file as authenticated user
        file_content = b"Private file content"
        file_data = io.BytesIO(file_content)
        
        response = client.post(
            "/api/files/upload",
            headers=auth_headers,
            files={"file": ("private.txt", file_data, "text/plain")}
        )
        
        assert response.status_code == 201
        file_id = response.json()["file"]["id"]
        
        # Anonymous user should not be able to download
        download_response = client.get(f"/api/files/{file_id}/download")
        
        assert download_response.status_code == 404
    
    def test_other_user_cannot_download_private_file(self, client: TestClient):
        """Test that other users cannot download private files"""
        # Create two users
        user1_response = client.post("/api/auth/register", json={
            "username": "fileowner",
            "email": "owner@test.com",
            "password": "password123"
        })
        assert user1_response.status_code == 201
        
        user2_response = client.post("/api/auth/register", json={
            "username": "otheruser",
            "email": "other@test.com", 
            "password": "password123"
        })
        assert user2_response.status_code == 201
        
        # User1 uploads a file
        login1_response = client.post("/api/auth/login", json={
            "username": "fileowner",
            "password": "password123"
        })
        user1_token = login1_response.json()["access_token"]
        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        
        file_content = b"User1's private file"
        file_data = io.BytesIO(file_content)
        
        upload_response = client.post(
            "/api/files/upload",
            headers=user1_headers,
            files={"file": ("private.txt", file_data, "text/plain")}
        )
        assert upload_response.status_code == 201
        file_id = upload_response.json()["file"]["id"]
        
        # User2 tries to download User1's file
        login2_response = client.post("/api/auth/login", json={
            "username": "otheruser",
            "password": "password123"
        })
        user2_token = login2_response.json()["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}
        
        download_response = client.get(f"/api/files/{file_id}/download", headers=user2_headers)
        
        assert download_response.status_code == 404
    
    def test_anonymous_can_download_public_clip_file(self, client: TestClient, auth_headers):
        """Test that anonymous users can download files from public clips"""
        # Upload a file
        file_content = b"Public clip file content"
        file_data = io.BytesIO(file_content)
        
        upload_response = client.post(
            "/api/files/upload",
            headers=auth_headers,
            files={"file": ("public.txt", file_data, "text/plain")}
        )
        assert upload_response.status_code == 201
        file_id = upload_response.json()["file"]["id"]
        
        # Create public clip with file
        clip_data = {
            "title": "Public File Clip",
            "content": "This is public",
            "clip_type": "file",
            "access_level": "public",
            "file_ids": [file_id]
        }
        
        clip_response = client.post("/api/clips/", headers=auth_headers, json=clip_data)
        assert clip_response.status_code == 201
        
        # Anonymous user should be able to download file from public clip
        download_response = client.get(f"/api/files/{file_id}/download")
        
        assert download_response.status_code == 200
        assert download_response.content == file_content
    
    def test_anonymous_can_download_encrypted_clip_file(self, client: TestClient, auth_headers):
        """Test that anonymous users can download files from encrypted clips"""
        # Upload a file
        file_content = b"Encrypted clip file content"
        file_data = io.BytesIO(file_content)
        
        upload_response = client.post(
            "/api/files/upload",
            headers=auth_headers,
            files={"file": ("encrypted.txt", file_data, "text/plain")}
        )
        assert upload_response.status_code == 201
        file_id = upload_response.json()["file"]["id"]
        
        # Create encrypted clip with file
        clip_data = {
            "title": "Encrypted File Clip",
            "content": "This is encrypted",
            "clip_type": "file",
            "access_level": "encrypted",
            "password": "secret123",
            "file_ids": [file_id]
        }
        
        clip_response = client.post("/api/clips/", headers=auth_headers, json=clip_data)
        assert clip_response.status_code == 201
        
        # Anonymous user should be able to download file from encrypted clip
        # (file download doesn't require password, only clip access does)
        download_response = client.get(f"/api/files/{file_id}/download")
        
        assert download_response.status_code == 200
        assert download_response.content == file_content
    
    def test_cannot_download_private_clip_file(self, client: TestClient, auth_headers):
        """Test that files from private clips cannot be downloaded by others"""
        # Upload a file
        file_content = b"Private clip file content"
        file_data = io.BytesIO(file_content)
        
        upload_response = client.post(
            "/api/files/upload",
            headers=auth_headers,
            files={"file": ("private.txt", file_data, "text/plain")}
        )
        assert upload_response.status_code == 201
        file_id = upload_response.json()["file"]["id"]
        
        # Create private clip with file
        clip_data = {
            "title": "Private File Clip",
            "content": "This is private",
            "clip_type": "file",
            "access_level": "private",
            "file_ids": [file_id]
        }
        
        clip_response = client.post("/api/clips/", headers=auth_headers, json=clip_data)
        assert clip_response.status_code == 201
        
        # Anonymous user should not be able to download file from private clip
        download_response = client.get(f"/api/files/{file_id}/download")
        
        assert download_response.status_code == 404
    
    def test_file_without_clip_requires_ownership(self, client: TestClient, auth_headers):
        """Test that files not associated with clips require ownership"""
        # Upload a file without associating it with a clip
        file_content = b"Standalone file content"
        file_data = io.BytesIO(file_content)
        
        upload_response = client.post(
            "/api/files/upload",
            headers=auth_headers,
            files={"file": ("standalone.txt", file_data, "text/plain")}
        )
        assert upload_response.status_code == 201
        file_id = upload_response.json()["file"]["id"]
        
        # Owner should be able to download
        download_response = client.get(f"/api/files/{file_id}/download", headers=auth_headers)
        assert download_response.status_code == 200
        assert download_response.content == file_content
        
        # Anonymous user should not be able to download
        anon_download_response = client.get(f"/api/files/{file_id}/download")
        assert anon_download_response.status_code == 404
    
    def test_download_nonexistent_file(self, client: TestClient, auth_headers):
        """Test downloading a file that doesn't exist"""
        response = client.get("/api/files/99999/download", headers=auth_headers)
        
        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]
    
    def test_file_download_updates_counter(self, client: TestClient, auth_headers):
        """Test that file downloads update the download counter"""
        # Upload a file
        file_content = b"Download counter test"
        file_data = io.BytesIO(file_content)
        
        upload_response = client.post(
            "/api/files/upload",
            headers=auth_headers,
            files={"file": ("counter.txt", file_data, "text/plain")}
        )
        assert upload_response.status_code == 201
        file_id = upload_response.json()["file"]["id"]
        
        # Check initial download count
        info_response = client.get(f"/api/files/{file_id}", headers=auth_headers)
        assert info_response.status_code == 200
        initial_count = info_response.json()["download_count"]
        
        # Download the file
        download_response = client.get(f"/api/files/{file_id}/download", headers=auth_headers)
        assert download_response.status_code == 200
        
        # Check updated download count
        info_response = client.get(f"/api/files/{file_id}", headers=auth_headers)
        assert info_response.status_code == 200
        updated_count = info_response.json()["download_count"]
        
        assert updated_count == initial_count + 1 + 1
