"""
Test Suite: Signup Flows for The Drop App
Tests for:
- Flow A (Under 14, parent-led): register-child endpoint
- Flow B (14+, self signup): register-self endpoint
- Username availability check
- User lookup by invite/username
- Login for existing users
- Profile update (username, avatar)
"""
import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_LOGIN_EMAIL = "hansel@test.com"
TEST_LOGIN_PASSWORD = "securepass123"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token for existing user"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_LOGIN_EMAIL,
        "password": TEST_LOGIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"Authentication failed - {response.status_code}: {response.text}")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


# ================== USERNAME CHECK TESTS ==================

class TestUsernameCheck:
    """Test GET /api/auth/check-username/{username} endpoint"""
    
    def test_check_username_valid_available(self, api_client):
        """Valid username format should return available status"""
        unique_name = f"testuser{int(time.time())}"
        response = api_client.get(f"{BASE_URL}/api/auth/check-username/{unique_name}")
        assert response.status_code == 200
        data = response.json()
        assert "available" in data
        assert "username" in data
        assert data["username"] == unique_name
        assert data["available"] == True
    
    def test_check_username_too_short(self, api_client):
        """Username with < 3 chars should return invalid format"""
        response = api_client.get(f"{BASE_URL}/api/auth/check-username/ab")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] == False
        assert "reason" in data
        assert "3-20" in data["reason"]
    
    def test_check_username_single_char(self, api_client):
        """Single character username should be invalid"""
        response = api_client.get(f"{BASE_URL}/api/auth/check-username/x")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] == False
    
    def test_check_username_existing_taken(self, api_client):
        """Existing username should return taken"""
        response = api_client.get(f"{BASE_URL}/api/auth/check-username/hansel")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] == False
    
    def test_check_username_with_at_prefix(self, api_client):
        """Username with @ prefix should be stripped and checked"""
        unique_name = f"testnew{int(time.time())}"
        response = api_client.get(f"{BASE_URL}/api/auth/check-username/@{unique_name}")
        assert response.status_code == 200
        data = response.json()
        # @ should be stripped
        assert data["username"] == unique_name


# ================== REGISTER-CHILD TESTS (Flow A: Under 14) ==================

class TestRegisterChild:
    """Test POST /api/auth/register-child endpoint - Parent-led signup for under 14"""
    
    def test_register_child_success(self, api_client):
        """Valid child registration should return token and user"""
        unique_suffix = int(time.time())
        response = api_client.post(f"{BASE_URL}/api/auth/register-child", json={
            "parent_name": "Test Parent",
            "parent_email": f"testparent{unique_suffix}@test.com",
            "parent_password": "securepass123",
            "child_name": "Test Child",
            "child_age": 10,
            "child_country": "United States",
            "child_city": "New York",
            "avatar_url": "https://api.dicebear.com/9.x/adventurer/svg?seed=testchild"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Check token
        assert "token" in data
        assert len(data["token"]) > 0
        
        # Check user object
        assert "user" in data
        user = data["user"]
        assert user["account_type"] == "child"
        assert user["full_name"] == "Test Child"
        assert "age_group" in user
        assert user["age_group"] in ["8-10", "11-13"]  # age 10 should be 8-10
        assert "username" in user
        assert len(user["username"]) >= 3
        assert "avatar_url" in user
        assert "invite_code" in user
        assert len(user["invite_code"]) == 8
    
    def test_register_child_age_group_8_10(self, api_client):
        """Child age <= 10 should get age_group '8-10'"""
        unique_suffix = int(time.time()) + 1
        response = api_client.post(f"{BASE_URL}/api/auth/register-child", json={
            "parent_name": "Parent B",
            "parent_email": f"parentb{unique_suffix}@test.com",
            "parent_password": "securepass123",
            "child_name": "Young Kid",
            "child_age": 9,
            "child_country": "India"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["age_group"] == "8-10"
    
    def test_register_child_age_group_11_13(self, api_client):
        """Child age 11-13 should get age_group '11-13'"""
        unique_suffix = int(time.time()) + 2
        response = api_client.post(f"{BASE_URL}/api/auth/register-child", json={
            "parent_name": "Parent C",
            "parent_email": f"parentc{unique_suffix}@test.com",
            "parent_password": "securepass123",
            "child_name": "Tween Kid",
            "child_age": 12,
            "child_country": "Canada"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["age_group"] == "11-13"
    
    def test_register_child_rejects_age_14_plus(self, api_client):
        """Registration with age >= 14 should be rejected"""
        unique_suffix = int(time.time()) + 3
        response = api_client.post(f"{BASE_URL}/api/auth/register-child", json={
            "parent_name": "Parent D",
            "parent_email": f"parentd{unique_suffix}@test.com",
            "parent_password": "securepass123",
            "child_name": "Teen",
            "child_age": 14,
            "child_country": "UK"
        })
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "14" in data["detail"] or "self" in data["detail"].lower()
    
    def test_register_child_rejects_short_password(self, api_client):
        """Password < 8 chars should be rejected"""
        unique_suffix = int(time.time()) + 4
        response = api_client.post(f"{BASE_URL}/api/auth/register-child", json={
            "parent_name": "Parent E",
            "parent_email": f"parente{unique_suffix}@test.com",
            "parent_password": "short",
            "child_name": "Kid E",
            "child_age": 10,
            "child_country": "Australia"
        })
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "8" in data["detail"] or "password" in data["detail"].lower()
    
    def test_register_child_rejects_duplicate_email(self, api_client):
        """Duplicate parent email should be rejected"""
        response = api_client.post(f"{BASE_URL}/api/auth/register-child", json={
            "parent_name": "Parent F",
            "parent_email": TEST_LOGIN_EMAIL,  # Already exists
            "parent_password": "securepass123",
            "child_name": "Kid F",
            "child_age": 10,
            "child_country": "Germany"
        })
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "email" in data["detail"].lower() or "registered" in data["detail"].lower()


# ================== REGISTER-SELF TESTS (Flow B: 14+) ==================

class TestRegisterSelf:
    """Test POST /api/auth/register-self endpoint - Self signup for 14+"""
    
    def test_register_self_success(self, api_client):
        """Valid self registration should return token and user"""
        unique_suffix = int(time.time())
        username = f"selfuser{unique_suffix}"
        response = api_client.post(f"{BASE_URL}/api/auth/register-self", json={
            "full_name": "Self Teen",
            "email": f"selfteen{unique_suffix}@test.com",
            "password": "securepass123",
            "age": 16,
            "country": "United States",
            "city": "Los Angeles",
            "username": username,
            "avatar_url": "https://api.dicebear.com/9.x/adventurer/svg?seed=selfteen"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Check token
        assert "token" in data
        assert len(data["token"]) > 0
        
        # Check user object
        assert "user" in data
        user = data["user"]
        assert user["account_type"] == "self"
        assert user["full_name"] == "Self Teen"
        assert user["username"] == username
        assert "age_group" in user
        assert user["age_group"] in ["14-16", "17-20"]
        assert "avatar_url" in user
        assert "invite_code" in user
        assert len(user["invite_code"]) == 8
    
    def test_register_self_age_group_14_16(self, api_client):
        """Self signup age 14-16 should get age_group '14-16'"""
        unique_suffix = int(time.time()) + 10
        username = f"teen{unique_suffix}"
        response = api_client.post(f"{BASE_URL}/api/auth/register-self", json={
            "full_name": "Teen User",
            "email": f"teen{unique_suffix}@test.com",
            "password": "securepass123",
            "age": 15,
            "country": "India",
            "username": username
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["age_group"] == "14-16"
    
    def test_register_self_age_group_17_20(self, api_client):
        """Self signup age 17+ should get age_group '17-20'"""
        unique_suffix = int(time.time()) + 11
        username = f"youngadult{unique_suffix}"
        response = api_client.post(f"{BASE_URL}/api/auth/register-self", json={
            "full_name": "Young Adult",
            "email": f"youngadult{unique_suffix}@test.com",
            "password": "securepass123",
            "age": 18,
            "country": "Canada",
            "username": username
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["age_group"] == "17-20"
    
    def test_register_self_rejects_age_under_14(self, api_client):
        """Self registration with age < 14 should be rejected"""
        unique_suffix = int(time.time()) + 12
        response = api_client.post(f"{BASE_URL}/api/auth/register-self", json={
            "full_name": "Young Kid",
            "email": f"kid{unique_suffix}@test.com",
            "password": "securepass123",
            "age": 13,
            "country": "UK",
            "username": f"kid{unique_suffix}"
        })
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "14" in data["detail"] or "parent" in data["detail"].lower()
    
    def test_register_self_rejects_duplicate_username(self, api_client):
        """Duplicate username should be rejected"""
        unique_suffix = int(time.time()) + 13
        response = api_client.post(f"{BASE_URL}/api/auth/register-self", json={
            "full_name": "New User",
            "email": f"newuser{unique_suffix}@test.com",
            "password": "securepass123",
            "age": 16,
            "country": "US",
            "username": "hansel"  # Already exists
        })
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "username" in data["detail"].lower() or "taken" in data["detail"].lower()
    
    def test_register_self_rejects_duplicate_email(self, api_client):
        """Duplicate email should be rejected"""
        unique_suffix = int(time.time()) + 14
        response = api_client.post(f"{BASE_URL}/api/auth/register-self", json={
            "full_name": "Dup User",
            "email": TEST_LOGIN_EMAIL,  # Already exists
            "password": "securepass123",
            "age": 16,
            "country": "US",
            "username": f"dupuser{unique_suffix}"
        })
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "email" in data["detail"].lower() or "registered" in data["detail"].lower()
    
    def test_register_self_rejects_invalid_username_format(self, api_client):
        """Invalid username format should be rejected"""
        unique_suffix = int(time.time()) + 15
        response = api_client.post(f"{BASE_URL}/api/auth/register-self", json={
            "full_name": "Invalid User",
            "email": f"invalid{unique_suffix}@test.com",
            "password": "securepass123",
            "age": 16,
            "country": "US",
            "username": "ab"  # Too short
        })
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    def test_register_self_rejects_short_password(self, api_client):
        """Password < 8 chars should be rejected"""
        unique_suffix = int(time.time()) + 16
        response = api_client.post(f"{BASE_URL}/api/auth/register-self", json={
            "full_name": "Short Pass",
            "email": f"shortpass{unique_suffix}@test.com",
            "password": "short",
            "age": 16,
            "country": "US",
            "username": f"shortpass{unique_suffix}"
        })
        assert response.status_code == 400


# ================== USER-BY-INVITE TESTS ==================

class TestUserByInvite:
    """Test GET /api/auth/user-by-invite/{invite_code} endpoint"""
    
    def test_lookup_by_username(self, api_client):
        """Should return public profile when looking up by username"""
        response = api_client.get(f"{BASE_URL}/api/auth/user-by-invite/hansel")
        assert response.status_code == 200
        data = response.json()
        assert "full_name" in data
        assert "username" in data
        assert "avatar_url" in data
        assert "knowledge_score" in data
        assert "current_streak" in data
        assert "invite_code" in data
        # Should NOT include sensitive data
        assert "email" not in data
        assert "password_hash" not in data
    
    def test_lookup_by_invite_code(self, api_client):
        """Should return public profile when looking up by invite_code"""
        # First get the invite code from a known user
        login_response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_LOGIN_EMAIL,
            "password": TEST_LOGIN_PASSWORD
        })
        invite_code = login_response.json()["user"]["invite_code"]
        
        response = api_client.get(f"{BASE_URL}/api/auth/user-by-invite/{invite_code}")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "hansel"
    
    def test_lookup_nonexistent_user(self, api_client):
        """Looking up nonexistent user should return 404"""
        response = api_client.get(f"{BASE_URL}/api/auth/user-by-invite/nonexistent999")
        assert response.status_code == 404


# ================== LOGIN TESTS ==================

class TestLogin:
    """Test POST /api/auth/login endpoint - Should work for existing users"""
    
    def test_login_existing_user(self, api_client):
        """Login with valid credentials should work"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_LOGIN_EMAIL,
            "password": TEST_LOGIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_LOGIN_EMAIL
    
    def test_login_invalid_credentials(self, api_client):
        """Login with invalid credentials should fail"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_LOGIN_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, api_client):
        """Login with nonexistent email should fail"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "anypassword"
        })
        assert response.status_code == 401


# ================== PROFILE UPDATE TESTS ==================

class TestProfileUpdate:
    """Test PUT /api/auth/me endpoint - Update username and avatar"""
    
    def test_update_avatar_url(self, authenticated_client):
        """Should be able to update avatar_url"""
        new_avatar = "https://api.dicebear.com/9.x/adventurer/svg?seed=newavatar"
        response = authenticated_client.put(f"{BASE_URL}/api/auth/me", json={
            "avatar_url": new_avatar
        })
        assert response.status_code == 200
        data = response.json()
        assert data["avatar_url"] == new_avatar
        
        # Revert
        authenticated_client.put(f"{BASE_URL}/api/auth/me", json={
            "avatar_url": "https://api.dicebear.com/9.x/adventurer/svg?seed=hansel"
        })
    
    def test_update_username_rejects_taken(self, authenticated_client):
        """Updating to a taken username should fail"""
        # First create another user
        api_client = requests.Session()
        api_client.headers.update({"Content-Type": "application/json"})
        unique_suffix = int(time.time()) + 100
        api_client.post(f"{BASE_URL}/api/auth/register-self", json={
            "full_name": "Other User",
            "email": f"other{unique_suffix}@test.com",
            "password": "securepass123",
            "age": 16,
            "country": "US",
            "username": f"otherusername{unique_suffix}"
        })
        
        # Try to update hansel to the same username
        response = authenticated_client.put(f"{BASE_URL}/api/auth/me", json={
            "username": f"otherusername{unique_suffix}"
        })
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
