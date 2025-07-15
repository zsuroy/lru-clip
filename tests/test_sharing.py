"""
Tests for clip sharing functionality
"""

import io
from fastapi.testclient import TestClient


class TestClipSharing:
    """Test clip sharing functionality"""
    
    def create_public_clip_with_files(self, client: TestClient, auth_headers):
        """Test creating a public clip with multiple files"""
        # Upload multiple files
        file_ids = []
        for i in range(3):
            file_content = f"Test file {i+1} content".encode()
            file_data = io.BytesIO(file_content)
            
            response = client.post(
                "/api/files/upload",
                headers=auth_headers,
                files={"file": (f"test_file_{i+1}.txt", file_data, "text/plain")}
            )
            
            assert response.status_code == 201
            file_ids.append(response.json()["file"]["id"])
        
        # Create public clip with files
        clip_data = {
            "title": "Public Multi-File Clip",
            "content": "This clip contains multiple files",
            "clip_type": "file",
            "access_level": "public",
            "file_ids": file_ids
        }
        
        response = client.post("/api/clips/", headers=auth_headers, json=clip_data)
        
        assert response.status_code == 201
        clip = response.json()
        assert clip["access_level"] == "public"
        assert clip["share_token"] is not None
        assert len(clip["files"]) == 3
        
        return clip["share_token"], file_ids
    
    def create_encrypted_clip_with_file (self, client: TestClient, auth_headers):
        """Test creating an encrypted clip with file"""
        # Upload a file
        file_content = b"Secret file content"
        file_data = io.BytesIO(file_content)
        
        upload_response = client.post(
            "/api/files/upload",
            headers=auth_headers,
            files={"file": ("secret.txt", file_data, "text/plain")}
        )
        
        assert upload_response.status_code == 201
        file_id = upload_response.json()["file"]["id"]
        
        # Create encrypted clip
        clip_data = {
            "title": "Encrypted File Clip",
            "content": "This is a secret clip",
            "clip_type": "file",
            "access_level": "encrypted",
            "password": "secret123",
            "file_ids": [file_id]
        }
        
        response = client.post("/api/clips/", headers=auth_headers, json=clip_data)
        
        assert response.status_code == 201
        clip = response.json()
        assert clip["access_level"] == "encrypted"
        assert clip["share_token"] is not None
        assert len(clip["files"]) == 1
        
        return clip["share_token"], file_id
    
    def test_access_public_shared_clip(self, client: TestClient, auth_headers):
        """Test accessing a public shared clip"""
        share_token, file_ids = self.create_public_clip_with_files(client, auth_headers)
        
        # Access shared clip without authentication
        response = client.get(f"/api/clips/shared/{share_token}")
        
        assert response.status_code == 200
        clip = response.json()
        assert clip["title"] == "Public Multi-File Clip"
        assert len(clip["files"]) == 3
        
        # Verify file IDs match
        clip_file_ids = [f["id"] for f in clip["files"]]
        assert set(clip_file_ids) == set(file_ids)
    
    def test_access_encrypted_shared_clip_without_password(self, client: TestClient, auth_headers):
        """Test accessing encrypted clip without password should fail"""
        share_token, file_id = self.create_encrypted_clip_with_file (client, auth_headers)
        
        # Try to access without password
        response = client.get(f"/api/clips/shared/{share_token}")
        
        assert response.status_code == 401
        assert "Password required" in response.json()["detail"]
    
    def test_access_encrypted_shared_clip_with_wrong_password(self, client: TestClient, auth_headers):
        """Test accessing encrypted clip with wrong password"""
        share_token, file_id = self.create_encrypted_clip_with_file (client, auth_headers)
        
        # Try with wrong password
        response = client.post(
            f"/api/clips/shared/{share_token}/access",
            json={"password": "wrongpassword"}
        )
        
        assert response.status_code == 401
        assert "Incorrect password" in response.json()["detail"]
    
    def test_access_encrypted_shared_clip_with_correct_password(self, client: TestClient, auth_headers):
        """Test accessing encrypted clip with correct password"""
        share_token, file_id = self.create_encrypted_clip_with_file (client, auth_headers)
        
        # Access with correct password
        response = client.post(
            f"/api/clips/shared/{share_token}/access",
            json={"password": "secret123"}
        )
        
        assert response.status_code == 200
        clip = response.json()
        assert clip["title"] == "Encrypted File Clip"
        assert len(clip["files"]) == 1
        assert clip["files"][0]["id"] == file_id
    
    def test_download_file_from_shared_clip(self, client: TestClient, auth_headers):
        """Test downloading files from shared clips"""
        share_token, file_ids = self.create_public_clip_with_files(client, auth_headers)
        
        # Download file from shared clip (no auth required)
        file_id = file_ids[0]
        response = client.get(f"/api/files/{file_id}/download")
        
        assert response.status_code == 200
        assert response.content == b"Test file 1 content"
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
    
    def test_download_file_from_encrypted_shared_clip(self, client: TestClient, auth_headers):
        """Test downloading files from encrypted shared clips"""
        share_token, file_id = self.create_encrypted_clip_with_file (client, auth_headers)
        
        # Download file from encrypted clip (no auth required for file download)
        response = client.get(f"/api/files/{file_id}/download")
        
        assert response.status_code == 200
        assert response.content == b"Secret file content"
    
    def test_file_association_validation(self, client: TestClient, auth_headers):
        """Test file association validation"""
        # Try to create clip with non-existent file ID
        clip_data = {
            "title": "Invalid File Clip",
            "content": "This should fail",
            "clip_type": "file",
            "access_level": "public",
            "file_ids": [99999]  # Non-existent file ID
        }
        
        response = client.post("/api/clips/", headers=auth_headers, json=clip_data)
        
        # Should still create clip but without files
        assert response.status_code == 201
        clip = response.json()
        assert len(clip["files"]) == 0
    
    def test_file_ownership_validation(self, client: TestClient):
        """Test that users can only associate their own files"""
        # Create two users
        user1_response = client.post("/api/auth/register", json={
            "username": "user1",
            "email": "user1@test.com",
            "password": "password123"
        })
        assert user1_response.status_code == 201
        
        user2_response = client.post("/api/auth/register", json={
            "username": "user2", 
            "email": "user2@test.com",
            "password": "password123"
        })
        assert user2_response.status_code == 201
        
        # User1 uploads a file
        login1_response = client.post("/api/auth/login", json={
            "username": "user1",
            "password": "password123"
        })
        user1_token = login1_response.json()["access_token"]
        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        
        file_content = b"User1's file"
        file_data = io.BytesIO(file_content)
        
        upload_response = client.post(
            "/api/files/upload",
            headers=user1_headers,
            files={"file": ("user1_file.txt", file_data, "text/plain")}
        )
        assert upload_response.status_code == 201
        file_id = upload_response.json()["file"]["id"]
        
        # User2 tries to create clip with User1's file
        login2_response = client.post("/api/auth/login", json={
            "username": "user2",
            "password": "password123"
        })
        user2_token = login2_response.json()["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}
        
        clip_data = {
            "title": "Stolen File Clip",
            "content": "Trying to use someone else's file",
            "clip_type": "file",
            "access_level": "public",
            "file_ids": [file_id]
        }
        
        response = client.post("/api/clips/", headers=user2_headers, json=clip_data)
        
        # Should create clip but without the file (since user2 doesn't own it)
        assert response.status_code == 201
        clip = response.json()
        assert len(clip["files"]) == 0
