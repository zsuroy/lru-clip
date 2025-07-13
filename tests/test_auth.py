"""
Tests for authentication endpoints
"""

import pytest
from fastapi.testclient import TestClient


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_register_success(self, client: TestClient):
        """Test successful user registration"""
        response = client.post("/api/auth/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpassword123",
            "full_name": "New User"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "newuser"
        assert data["user"]["email"] == "newuser@example.com"
    
    def test_register_duplicate_username(self, client: TestClient, test_user):
        """Test registration with duplicate username"""
        response = client.post("/api/auth/register", json={
            "username": "testuser",  # Already exists
            "email": "different@example.com",
            "password": "password123"
        })
        
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]
    
    def test_register_duplicate_email(self, client: TestClient, test_user):
        """Test registration with duplicate email"""
        response = client.post("/api/auth/register", json={
            "username": "differentuser",
            "email": "test@example.com",  # Already exists
            "password": "password123"
        })
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    def test_register_invalid_data(self, client: TestClient):
        """Test registration with invalid data"""
        # Short password
        response = client.post("/api/auth/register", json={
            "username": "user",
            "email": "user@example.com",
            "password": "123"  # Too short
        })
        assert response.status_code == 422
        
        # Invalid email
        response = client.post("/api/auth/register", json={
            "username": "user",
            "email": "invalid-email",
            "password": "password123"
        })
        assert response.status_code == 422
    
    def test_login_success(self, client: TestClient, test_user):
        """Test successful login"""
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "testuser"
    
    def test_login_with_email(self, client: TestClient, test_user):
        """Test login with email instead of username"""
        response = client.post("/api/auth/login", json={
            "username": "test@example.com",  # Using email
            "password": "testpassword123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["username"] == "testuser"
    
    def test_login_wrong_password(self, client: TestClient, test_user):
        """Test login with wrong password"""
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with nonexistent user"""
        response = client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "password123"
        })
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_get_current_user(self, client: TestClient, auth_headers):
        """Test getting current user info"""
        response = client.get("/api/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["is_active"] is True
    
    def test_get_current_user_unauthorized(self, client: TestClient):
        """Test getting current user without authentication"""
        response = client.get("/api/auth/me")
        
        assert response.status_code == 401
    
    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token"""
        response = client.get("/api/auth/me", headers={
            "Authorization": "Bearer invalid-token"
        })
        
        assert response.status_code == 401
    
    def test_refresh_token(self, client: TestClient, auth_headers):
        """Test token refresh"""
        response = client.post("/api/auth/refresh", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "testuser"
