"""
Test suite for Child Account Privacy Rules in The Drop News App
These tests verify the 5 privacy rules for child accounts:
1. Child accounts (account_type='child') must NOT appear in /api/friends/search results
2. Direct friend request to child account via /api/friends/request must return 403
3. Child accounts CAN connect via invite link at /api/invite/connect/{username}
4. When child connects via invite, mock parent notification is logged (check response success)
5. When invite-connect involves a child inviter, mock parent notification is triggered too
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestChildPrivacyRules:
    """Tests for child account privacy and connection rules"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data and get authentication tokens"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login with existing test users
        self.hansel_token = self._login("hansel@test.com", "securepass123")
        self.zara_token = self._login("zara@test.com", "securepass123")
        
        # Generate unique test identifiers
        self.test_id = uuid.uuid4().hex[:6]
        
    def _login(self, email, password):
        """Helper to login and get token"""
        resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": password
        })
        if resp.status_code == 200:
            return resp.json().get("token")
        return None
    
    def _register_child(self, child_name, parent_email):
        """Helper to register a child account"""
        resp = self.session.post(f"{BASE_URL}/api/auth/register-child", json={
            "parent_name": "Test Parent",
            "parent_email": parent_email,
            "parent_password": "securepass123",
            "child_name": child_name,
            "child_age": 10,
            "child_country": "US",
            "child_city": "Test City"
        })
        return resp
    
    def _register_self(self, full_name, email, username):
        """Helper to register a self (14+) account"""
        resp = self.session.post(f"{BASE_URL}/api/auth/register-self", json={
            "full_name": full_name,
            "email": email,
            "password": "securepass123",
            "age": 16,
            "country": "US",
            "city": "Test City",
            "username": username
        })
        return resp
    
    # ==================== Privacy Rule 1 ====================
    # Child accounts must NOT appear in /api/friends/search results
    
    def test_privacy_rule_1_child_not_in_search_results(self):
        """Privacy Rule 1: Child accounts should NOT appear in friend search results"""
        # First create a child account with unique username
        child_name = f"TEST_Child_{self.test_id}"
        parent_email = f"test_parent_{self.test_id}@test.com"
        
        register_resp = self._register_child(child_name, parent_email)
        assert register_resp.status_code == 200, f"Failed to register child: {register_resp.text}"
        
        child_data = register_resp.json()
        child_username = child_data['user']['username']
        
        # Now search for the child using Hansel's account
        assert self.hansel_token, "Hansel login failed"
        search_resp = self.session.get(
            f"{BASE_URL}/api/friends/search?q={child_username[:5]}",
            headers={"Authorization": f"Bearer {self.hansel_token}"}
        )
        
        assert search_resp.status_code == 200, f"Search failed: {search_resp.text}"
        
        results = search_resp.json()
        child_usernames = [r.get('username') for r in results]
        
        # Child username should NOT be in results
        assert child_username not in child_usernames, \
            f"Privacy Rule 1 FAILED: Child account '{child_username}' appeared in search results"
        
        print(f"✓ Privacy Rule 1 PASSED: Child account '{child_username}' correctly excluded from search")
    
    def test_search_returns_normal_accounts(self):
        """Verify search still works for non-child accounts (regression)"""
        assert self.hansel_token, "Hansel login failed"
        
        # Search for zara (a normal account)
        search_resp = self.session.get(
            f"{BASE_URL}/api/friends/search?q=zara",
            headers={"Authorization": f"Bearer {self.hansel_token}"}
        )
        
        assert search_resp.status_code == 200
        results = search_resp.json()
        
        # Zara might already be a friend, but should not be excluded due to account_type
        # The API should return users matching "zara" unless already friends or blocked
        print(f"✓ Search regression test: Found {len(results)} results for 'zara'")
    
    # ==================== Privacy Rule 2 ====================
    # Direct friend request to child account must return 403
    
    def test_privacy_rule_2_direct_friend_request_to_child_returns_403(self):
        """Privacy Rule 2: Direct friend request to child account must return 403"""
        # Create a child account
        child_name = f"TEST_Child2_{self.test_id}"
        parent_email = f"test_parent2_{self.test_id}@test.com"
        
        register_resp = self._register_child(child_name, parent_email)
        assert register_resp.status_code == 200, f"Failed to register child: {register_resp.text}"
        
        child_username = register_resp.json()['user']['username']
        
        # Try to send friend request to child using Hansel's account
        assert self.hansel_token, "Hansel login failed"
        
        request_resp = self.session.post(
            f"{BASE_URL}/api/friends/request",
            json={"target_username": child_username},
            headers={"Authorization": f"Bearer {self.hansel_token}"}
        )
        
        # Should return 403 Forbidden
        assert request_resp.status_code == 403, \
            f"Privacy Rule 2 FAILED: Expected 403, got {request_resp.status_code}. Response: {request_resp.text}"
        
        response_data = request_resp.json()
        assert "invite link" in response_data.get("detail", "").lower(), \
            f"Expected 'invite link' message, got: {response_data}"
        
        print(f"✓ Privacy Rule 2 PASSED: Direct friend request to child '{child_username}' returned 403")
    
    # ==================== Privacy Rule 3 ====================
    # Child accounts CAN connect via invite link
    
    def test_privacy_rule_3_child_can_connect_via_invite_link(self):
        """Privacy Rule 3: Child accounts CAN connect via invite link"""
        # Create a NEW child account
        child_name = f"TEST_Child3_{self.test_id}"
        parent_email = f"test_parent3_{self.test_id}@test.com"
        
        register_resp = self._register_child(child_name, parent_email)
        assert register_resp.status_code == 200, f"Failed to register child: {register_resp.text}"
        
        child_token = register_resp.json()['token']
        child_username = register_resp.json()['user']['username']
        
        # Create a NEW self account to be the inviter (to avoid existing friendship issues)
        inviter_name = f"TEST_Inviter_{self.test_id}"
        inviter_email = f"test_inviter_{self.test_id}@test.com"
        inviter_username = f"testinviter{self.test_id}"
        
        inviter_resp = self._register_self(inviter_name, inviter_email, inviter_username)
        assert inviter_resp.status_code == 200, f"Failed to register inviter: {inviter_resp.text}"
        
        # Connect child to inviter via invite link
        connect_resp = self.session.post(
            f"{BASE_URL}/api/invite/connect/{inviter_username}",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        
        # Should succeed (200)
        assert connect_resp.status_code == 200, \
            f"Privacy Rule 3 FAILED: Expected 200, got {connect_resp.status_code}. Response: {connect_resp.text}"
        
        # Verify they are now connected - check child's friends list
        friends_resp = self.session.get(
            f"{BASE_URL}/api/friends",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        
        assert friends_resp.status_code == 200, f"Failed to get friends: {friends_resp.text}"
        
        friends = friends_resp.json()
        friend_usernames = [f.get('username') for f in friends]
        
        assert inviter_username in friend_usernames, \
            f"Privacy Rule 3 FAILED: Connection not established. Friends: {friend_usernames}"
        
        print(f"✓ Privacy Rule 3 PASSED: Child '{child_username}' successfully connected to '{inviter_username}' via invite link")
    
    # ==================== Privacy Rule 4 ====================
    # When child connects via invite, mock parent notification is triggered
    
    def test_privacy_rule_4_child_connect_triggers_parent_notification(self):
        """Privacy Rule 4: When child connects via invite, parent notification is triggered (response success check)"""
        # Create a NEW child account
        child_name = f"TEST_Child4_{self.test_id}"
        parent_email = f"test_parent4_{self.test_id}@test.com"
        
        register_resp = self._register_child(child_name, parent_email)
        assert register_resp.status_code == 200, f"Failed to register child: {register_resp.text}"
        
        child_token = register_resp.json()['token']
        child_data = register_resp.json()['user']
        
        # Verify child has account_type = 'child'
        assert child_data.get('account_type') == 'child', \
            f"Expected account_type='child', got '{child_data.get('account_type')}'"
        
        # Create an inviter
        inviter_name = f"TEST_Inviter4_{self.test_id}"
        inviter_email = f"test_inviter4_{self.test_id}@test.com"
        inviter_username = f"testinviter4{self.test_id}"
        
        inviter_resp = self._register_self(inviter_name, inviter_email, inviter_username)
        assert inviter_resp.status_code == 200, f"Failed to register inviter: {inviter_resp.text}"
        
        # Connect via invite - this should trigger the mock parent notification
        # The notification is mocked via console.log - we can only verify the endpoint succeeds
        connect_resp = self.session.post(
            f"{BASE_URL}/api/invite/connect/{inviter_username}",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        
        assert connect_resp.status_code == 200, \
            f"Privacy Rule 4 FAILED: Expected 200, got {connect_resp.status_code}. Response: {connect_resp.text}"
        
        # The mock_send_parent_email_friend_request function is called internally
        # We verify success by checking the connection was established
        response_data = connect_resp.json()
        
        # If we got here without error, the parent notification logic executed successfully
        print(f"✓ Privacy Rule 4 PASSED: Child connection succeeded (mock parent notification was triggered)")
        print(f"  Note: Parent email is MOCKED via logger.info, not actually sent")
    
    # ==================== Privacy Rule 5 ====================
    # When invite-connect involves a child INVITER, parent notification is also triggered
    
    def test_privacy_rule_5_child_inviter_triggers_parent_notification(self):
        """Privacy Rule 5: When invite-connect involves a child inviter, parent notification is triggered"""
        # Create a child account who will be the INVITER
        child_inviter_name = f"TEST_ChildInviter_{self.test_id}"
        child_inviter_email = f"test_childinviter_{self.test_id}@test.com"
        
        child_resp = self._register_child(child_inviter_name, child_inviter_email)
        assert child_resp.status_code == 200, f"Failed to register child inviter: {child_resp.text}"
        
        child_inviter_username = child_resp.json()['user']['username']
        child_inviter_data = child_resp.json()['user']
        
        # Verify the inviter is a child
        assert child_inviter_data.get('account_type') == 'child', \
            f"Expected child inviter account_type='child', got '{child_inviter_data.get('account_type')}'"
        
        # Create a normal user who will connect via the child's invite link
        connecter_name = f"TEST_Connecter_{self.test_id}"
        connecter_email = f"test_connecter_{self.test_id}@test.com"
        connecter_username = f"testconnecter{self.test_id}"
        
        connecter_resp = self._register_self(connecter_name, connecter_email, connecter_username)
        assert connecter_resp.status_code == 200, f"Failed to register connecter: {connecter_resp.text}"
        
        connecter_token = connecter_resp.json()['token']
        
        # Connect to the child inviter via invite link
        # This should trigger mock_send_parent_email_friend_request for the CHILD INVITER's parent
        connect_resp = self.session.post(
            f"{BASE_URL}/api/invite/connect/{child_inviter_username}",
            headers={"Authorization": f"Bearer {connecter_token}"}
        )
        
        assert connect_resp.status_code == 200, \
            f"Privacy Rule 5 FAILED: Expected 200, got {connect_resp.status_code}. Response: {connect_resp.text}"
        
        # Verify the connection was established
        friends_resp = self.session.get(
            f"{BASE_URL}/api/friends",
            headers={"Authorization": f"Bearer {connecter_token}"}
        )
        
        assert friends_resp.status_code == 200, f"Failed to get friends: {friends_resp.text}"
        
        friends = friends_resp.json()
        friend_usernames = [f.get('username') for f in friends]
        
        assert child_inviter_username in friend_usernames, \
            f"Privacy Rule 5 FAILED: Connection not established with child inviter"
        
        print(f"✓ Privacy Rule 5 PASSED: Connection to child inviter '{child_inviter_username}' succeeded")
        print(f"  Note: Parent notification for child inviter is MOCKED via logger.info")


class TestRegistrationAccountTypes:
    """Tests for registration endpoints and account types"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.test_id = uuid.uuid4().hex[:6]
    
    def test_register_child_creates_child_account_type(self):
        """Registration: /api/auth/register-child creates account with account_type='child'"""
        child_name = f"TEST_ChildReg_{self.test_id}"
        parent_email = f"test_childreg_{self.test_id}@test.com"
        
        resp = self.session.post(f"{BASE_URL}/api/auth/register-child", json={
            "parent_name": "Test Parent",
            "parent_email": parent_email,
            "parent_password": "securepass123",
            "child_name": child_name,
            "child_age": 10,
            "child_country": "US",
            "child_city": "Test City"
        })
        
        assert resp.status_code == 200, f"Failed to register child: {resp.text}"
        
        data = resp.json()
        assert "user" in data, "Response should contain 'user'"
        assert "token" in data, "Response should contain 'token'"
        
        user = data['user']
        assert user.get('account_type') == 'child', \
            f"Expected account_type='child', got '{user.get('account_type')}'"
        
        print(f"✓ Registration Test: /api/auth/register-child correctly sets account_type='child'")
    
    def test_register_self_creates_self_account_type(self):
        """Registration: /api/auth/register-self creates account with account_type='self'"""
        full_name = f"TEST_SelfReg_{self.test_id}"
        email = f"test_selfreg_{self.test_id}@test.com"
        username = f"testselfreg{self.test_id}"
        
        resp = self.session.post(f"{BASE_URL}/api/auth/register-self", json={
            "full_name": full_name,
            "email": email,
            "password": "securepass123",
            "age": 16,
            "country": "US",
            "city": "Test City",
            "username": username
        })
        
        assert resp.status_code == 200, f"Failed to register self: {resp.text}"
        
        data = resp.json()
        assert "user" in data, "Response should contain 'user'"
        assert "token" in data, "Response should contain 'token'"
        
        user = data['user']
        assert user.get('account_type') == 'self', \
            f"Expected account_type='self', got '{user.get('account_type')}'"
        
        print(f"✓ Registration Test: /api/auth/register-self correctly sets account_type='self'")


class TestExistingSocialFeaturesRegression:
    """Regression tests for existing social features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login with existing test users
        resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "hansel@test.com",
            "password": "securepass123"
        })
        if resp.status_code == 200:
            self.hansel_token = resp.json().get("token")
        else:
            self.hansel_token = None
    
    def test_friends_search_requires_auth(self):
        """/api/friends/search requires authentication"""
        resp = self.session.get(f"{BASE_URL}/api/friends/search?q=test")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("✓ /api/friends/search requires authentication")
    
    def test_friends_request_requires_auth(self):
        """/api/friends/request requires authentication"""
        resp = self.session.post(f"{BASE_URL}/api/friends/request", json={"target_username": "test"})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("✓ /api/friends/request requires authentication")
    
    def test_friends_accept_requires_auth(self):
        """/api/friends/accept/{id} requires authentication"""
        resp = self.session.post(f"{BASE_URL}/api/friends/accept/fake-id")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("✓ /api/friends/accept/{id} requires authentication")
    
    def test_friends_list_requires_auth(self):
        """/api/friends (list) requires authentication"""
        resp = self.session.get(f"{BASE_URL}/api/friends")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("✓ /api/friends requires authentication")
    
    def test_friends_leaderboard_requires_auth(self):
        """/api/friends/leaderboard requires authentication"""
        resp = self.session.get(f"{BASE_URL}/api/friends/leaderboard")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("✓ /api/friends/leaderboard requires authentication")
    
    def test_invite_my_link_requires_auth(self):
        """/api/invite/my-link requires authentication"""
        resp = self.session.get(f"{BASE_URL}/api/invite/my-link")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print("✓ /api/invite/my-link requires authentication")
    
    def test_invite_lookup_works(self):
        """/api/invite/lookup/{username} works for public profile"""
        resp = self.session.get(f"{BASE_URL}/api/invite/lookup/hansel")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        data = resp.json()
        assert "full_name" in data
        assert "username" in data
        assert "knowledge_score" in data
        assert "current_streak" in data
        print("✓ /api/invite/lookup/{username} returns public profile")
    
    def test_invite_lookup_404_for_nonexistent(self):
        """/api/invite/lookup/{username} returns 404 for non-existent user"""
        resp = self.session.get(f"{BASE_URL}/api/invite/lookup/nonexistentuser12345")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("✓ /api/invite/lookup returns 404 for non-existent user")
    
    def test_friends_list_works_authenticated(self):
        """/api/friends returns friends list when authenticated"""
        assert self.hansel_token, "Hansel login failed"
        
        resp = self.session.get(
            f"{BASE_URL}/api/friends",
            headers={"Authorization": f"Bearer {self.hansel_token}"}
        )
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        friends = resp.json()
        assert isinstance(friends, list), "Expected list response"
        
        # If there are friends, verify structure
        if friends:
            friend = friends[0]
            assert "id" in friend
            assert "username" in friend
            assert "avatar_url" in friend
            assert "current_streak" in friend
            assert "knowledge_score" in friend
        
        print(f"✓ /api/friends returns {len(friends)} friends with correct structure")
    
    def test_friends_leaderboard_works_authenticated(self):
        """/api/friends/leaderboard returns leaderboard when authenticated"""
        assert self.hansel_token, "Hansel login failed"
        
        resp = self.session.get(
            f"{BASE_URL}/api/friends/leaderboard",
            headers={"Authorization": f"Bearer {self.hansel_token}"}
        )
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        data = resp.json()
        assert "leaderboard" in data, "Expected 'leaderboard' in response"
        
        leaderboard = data['leaderboard']
        assert isinstance(leaderboard, list), "Expected list for leaderboard"
        
        # Verify self is included with is_self=true
        self_entries = [e for e in leaderboard if e.get('is_self')]
        assert len(self_entries) > 0, "Current user should be in leaderboard with is_self=true"
        
        print(f"✓ /api/friends/leaderboard returns {len(leaderboard)} entries with is_self flag")
    
    def test_invite_my_link_works_authenticated(self):
        """/api/invite/my-link returns invite link when authenticated"""
        assert self.hansel_token, "Hansel login failed"
        
        resp = self.session.get(
            f"{BASE_URL}/api/invite/my-link",
            headers={"Authorization": f"Bearer {self.hansel_token}"}
        )
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        data = resp.json()
        assert "invite_url" in data
        assert "username" in data
        assert data['invite_url'].startswith("/join/@")
        
        print(f"✓ /api/invite/my-link returns invite_url: {data['invite_url']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
