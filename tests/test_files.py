"""
Tests for file management endpoints
"""

import io
from fastapi.testclient import TestClient


class TestFileEndpoints:
    """Test file management endpoints"""
    
    def test_upload_file(self, client: TestClient, auth_headers):
        """Test file upload"""
        # Create a test file
        file_content = b"This is a test file content"
        file_data = io.BytesIO(file_content)
        
        response = client.post(
            "/api/files/upload",
            headers=auth_headers,
            files={"file": ("test.txt", file_data, "text/plain")}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "File uploaded successfully"
        assert data["file"]["original_filename"] == "test.txt"
        assert data["file"]["mime_type"] == "text/plain"
        assert data["file"]["file_size"] == len(file_content)
    
    def test_upload_file_with_clip(self, client: TestClient, auth_headers):
        """Test file upload associated with a clip"""
        # Create a clip first
        clip_response = client.post("/api/clips/", headers=auth_headers, json={
            "title": "Test Clip",
            "content": "Test content",
            "clip_type": "text"
        })
        clip_id = clip_response.json()["id"]
        
        # Upload file associated with clip
        file_content = b"File for clip"
        file_data = io.BytesIO(file_content)
        
        response = client.post(
            f"/api/files/upload?clip_id={clip_id}",
            headers=auth_headers,
            files={"file": ("clip_file.txt", file_data, "text/plain")}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["file"]["clip_id"] == clip_id
    
    def test_upload_file_nonexistent_clip(self, client: TestClient, auth_headers):
        """Test file upload with nonexistent clip"""
        file_content = b"Test content"
        file_data = io.BytesIO(file_content)
        
        response = client.post(
            "/api/files/upload?clip_id=999",
            headers=auth_headers,
            files={"file": ("test.txt", file_data, "text/plain")}
        )
        
        assert response.status_code == 404
        assert "Clip not found" in response.json()["detail"]
    
    def test_get_files(self, client: TestClient, auth_headers):
        """Test getting user's files"""
        # Upload some files first
        for i in range(3):
            file_content = f"File content {i}".encode()
            file_data = io.BytesIO(file_content)
            
            client.post(
                "/api/files/upload",
                headers=auth_headers,
                files={"file": (f"test{i}.txt", file_data, "text/plain")}
            )
        
        response = client.get("/api/files/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["files"]) == 3
        assert data["total"] == 3
        assert data["page"] == 1
    
    def test_get_file_info(self, client: TestClient, auth_headers):
        """Test getting file information"""
        # Upload a file
        file_content = b"Test file content"
        file_data = io.BytesIO(file_content)
        
        upload_response = client.post(
            "/api/files/upload",
            headers=auth_headers,
            files={"file": ("test.txt", file_data, "text/plain")}
        )
        file_id = upload_response.json()["file"]["id"]
        
        # Get file info
        response = client.get(f"/api/files/{file_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == file_id
        assert data["original_filename"] == "test.txt"
        assert data["mime_type"] == "text/plain"
    
    def test_get_nonexistent_file_info(self, client: TestClient, auth_headers):
        """Test getting info for nonexistent file"""
        response = client.get("/api/files/999", headers=auth_headers)
        
        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]
    
    def test_download_file(self, client: TestClient, auth_headers):
        """Test file download"""
        # Upload a file
        file_content = b"Test file content for download"
        file_data = io.BytesIO(file_content)
        
        upload_response = client.post(
            "/api/files/upload",
            headers=auth_headers,
            files={"file": ("download_test.txt", file_data, "text/plain")}
        )
        file_id = upload_response.json()["file"]["id"]
        
        # Download the file
        response = client.get(f"/api/files/{file_id}/download", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.content == file_content
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
    
    def test_download_nonexistent_file(self, client: TestClient, auth_headers):
        """Test downloading nonexistent file"""
        response = client.get("/api/files/999/download", headers=auth_headers)
        
        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]
    
    def test_delete_file(self, client: TestClient, auth_headers):
        """Test file deletion"""
        # Upload a file
        file_content = b"File to delete"
        file_data = io.BytesIO(file_content)
        
        upload_response = client.post(
            "/api/files/upload",
            headers=auth_headers,
            files={"file": ("delete_test.txt", file_data, "text/plain")}
        )
        file_id = upload_response.json()["file"]["id"]
        
        # Delete the file
        response = client.delete(f"/api/files/{file_id}", headers=auth_headers)
        
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = client.get(f"/api/files/{file_id}", headers=auth_headers)
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_file(self, client: TestClient, auth_headers):
        """Test deleting nonexistent file"""
        response = client.delete("/api/files/999", headers=auth_headers)
        
        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]
    
    def test_file_deduplication(self, client: TestClient, auth_headers):
        """Test file deduplication"""
        # Upload the same file twice
        file_content = b"Duplicate file content"
        
        # First upload
        file_data1 = io.BytesIO(file_content)
        response1 = client.post(
            "/api/files/upload",
            headers=auth_headers,
            files={"file": ("file1.txt", file_data1, "text/plain")}
        )
        
        # Second upload (same content, different name)
        file_data2 = io.BytesIO(file_content)
        response2 = client.post(
            "/api/files/upload",
            headers=auth_headers,
            files={"file": ("file2.txt", file_data2, "text/plain")}
        )
        
        assert response1.status_code == 201
        assert response2.status_code == 201
        
        file1 = response1.json()["file"]
        file2 = response2.json()["file"]
        
        # Should have same hash but different original filenames
        assert file1["file_hash"] == file2["file_hash"]
        assert file1["original_filename"] == "file1.txt"
        assert file2["original_filename"] == "file2.txt"
    
    def test_unauthorized_file_access(self, client: TestClient):
        """Test accessing files without authentication"""
        response = client.get("/api/files/")
        assert response.status_code == 401
        
        response = client.post("/api/files/upload")
        assert response.status_code == 401
