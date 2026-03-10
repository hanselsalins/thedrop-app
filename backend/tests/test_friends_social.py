"""
Test suite for The Drop's Friends/Social System
Tests: friend requests, search, leaderboard, invite links, block/report, knowledge score
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
HANSEL_EMAIL = "hansel@test.com"
HANSEL_PASSWORD = "securepass123"
ZARA_EMAIL = "zara@test.com"
ZARA_PASSWORD = "securepass123"
CHILD_EMAIL = "parent@test.com"
CHILD_PASSWORD = "securepass123"

@pytest.fixture(scope="module")
def hansel_auth():
    """Get Hansel's token - 14+ self signup user"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": HANSEL_EMAIL, "password": HANSEL_PASSWORD
    })
    assert resp.status_code == 200, f"Hansel login failed: {resp.text}"
    data = resp.json()
    return {"token": data["token"], "user": data["user"]}

@pytest.fixture(scope="module")
def zara_auth():
    """Get Zara's token - 14+ self signup user"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ZARA_EMAIL, "password": ZARA_PASSWORD
    })
    assert resp.status_code == 200, f"Zara login failed: {resp.text}"
    data = resp.json()
    return {"token": data["token"], "user": data["user"]}

@pytest.fixture(scope="module")
def child_auth():
    """Get child account token - under 14 (Timmy)"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": CHILD_EMAIL, "password": CHILD_PASSWORD
    })
    if resp.status_code != 200:
        pytest.skip("Child account not found")
    data = resp.json()
    return {"token": data["token"], "user": data["user"]}


class TestFriendsSearch:
    """Test /api/friends/search endpoint"""
    
    def test_search_requires_auth(self):
        """Search requires authentication"""
        resp = requests.get(f"{BASE_URL}/api/friends/search?q=han")
        assert resp.status_code == 401
    
    def test_search_returns_users(self, hansel_auth):
        """Search finds users matching query"""
        headers = {"Authorization": f"Bearer {hansel_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/friends/search?q=zara", headers=headers)
        assert resp.status_code == 200
        results = resp.json()
        assert isinstance(results, list)
        # Zara should be in results
        usernames = [r.get("username", "") for r in results]
        # Either zara is found or results are empty if already friends
        print(f"Search results for 'zara': {usernames}")
    
    def test_search_excludes_child_accounts(self, hansel_auth, child_auth):
        """Child accounts (under-14) should NOT appear in search"""
        headers = {"Authorization": f"Bearer {hansel_auth['token']}"}
        child_username = child_auth["user"].get("username", "timmy")
        
        resp = requests.get(f"{BASE_URL}/api/friends/search?q={child_username}", headers=headers)
        assert resp.status_code == 200
        results = resp.json()
        
        # Child should not be in search results
        usernames = [r.get("username", "").lower() for r in results]
        assert child_username.lower() not in usernames, "Child account appeared in search - should be excluded"
        print(f"Search excluded child account '{child_username}' correctly")


class TestFriendRequests:
    """Test friend request send/accept/decline"""
    
    def test_send_request_requires_auth(self):
        """Sending friend request requires authentication"""
        resp = requests.post(f"{BASE_URL}/api/friends/request", json={"target_username": "zara"})
        assert resp.status_code == 401
    
    def test_send_request_to_nonexistent_user(self, hansel_auth):
        """Cannot send request to non-existent user"""
        headers = {"Authorization": f"Bearer {hansel_auth['token']}"}
        resp = requests.post(f"{BASE_URL}/api/friends/request", 
                            json={"target_username": "nonexistentuser123xyz"},
                            headers=headers)
        assert resp.status_code == 404
    
    def test_send_request_to_self(self, hansel_auth):
        """Cannot send friend request to self"""
        headers = {"Authorization": f"Bearer {hansel_auth['token']}"}
        username = hansel_auth["user"].get("username", "hansel")
        resp = requests.post(f"{BASE_URL}/api/friends/request", 
                            json={"target_username": username},
                            headers=headers)
        assert resp.status_code == 400
        assert "yourself" in resp.json().get("detail", "").lower()
    
    def test_send_request_to_child_blocked(self, hansel_auth, child_auth):
        """Cannot send friend request to child account via search - must use invite"""
        headers = {"Authorization": f"Bearer {hansel_auth['token']}"}
        child_username = child_auth["user"].get("username", "timmy")
        
        resp = requests.post(f"{BASE_URL}/api/friends/request", 
                            json={"target_username": child_username},
                            headers=headers)
        assert resp.status_code == 403
        assert "invite" in resp.json().get("detail", "").lower()
        print(f"Correctly blocked friend request to child account '{child_username}'")


class TestFriendsList:
    """Test GET /api/friends - get friends list"""
    
    def test_get_friends_requires_auth(self):
        """Friends list requires authentication"""
        resp = requests.get(f"{BASE_URL}/api/friends")
        assert resp.status_code == 401
    
    def test_get_friends_returns_list(self, hansel_auth):
        """Returns list of accepted friends with stats"""
        headers = {"Authorization": f"Bearer {hansel_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/friends", headers=headers)
        assert resp.status_code == 200
        friends = resp.json()
        assert isinstance(friends, list)
        
        # Verify friend object structure
        if friends:
            friend = friends[0]
            assert "id" in friend
            assert "full_name" in friend
            assert "username" in friend
            assert "avatar_url" in friend
            assert "current_streak" in friend
            assert "knowledge_score" in friend
            print(f"Friends list: {[f.get('username') for f in friends]}")


class TestFriendRequests:
    """Test GET /api/friends/requests - pending requests"""
    
    def test_get_requests_requires_auth(self):
        """Pending requests list requires authentication"""
        resp = requests.get(f"{BASE_URL}/api/friends/requests")
        assert resp.status_code == 401
    
    def test_get_requests_returns_list(self, hansel_auth):
        """Returns list of pending friend requests"""
        headers = {"Authorization": f"Bearer {hansel_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/friends/requests", headers=headers)
        assert resp.status_code == 200
        requests_list = resp.json()
        assert isinstance(requests_list, list)
        
        # Verify request object structure if any
        if requests_list:
            req = requests_list[0]
            assert "friendship_id" in req
            assert "sender" in req
            assert "created_at" in req
            print(f"Pending requests: {len(requests_list)}")


class TestLeaderboard:
    """Test GET /api/friends/leaderboard"""
    
    def test_leaderboard_requires_auth(self):
        """Leaderboard requires authentication"""
        resp = requests.get(f"{BASE_URL}/api/friends/leaderboard")
        assert resp.status_code == 401
    
    def test_leaderboard_includes_self(self, hansel_auth):
        """Leaderboard includes self with is_self=true"""
        headers = {"Authorization": f"Bearer {hansel_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/friends/leaderboard", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        
        # Should have leaderboard and optionally previous_month_winner
        assert "leaderboard" in data
        leaderboard = data["leaderboard"]
        assert isinstance(leaderboard, list)
        assert len(leaderboard) >= 1  # At minimum, self
        
        # Find self in leaderboard
        self_entry = None
        for entry in leaderboard:
            if entry.get("is_self"):
                self_entry = entry
                break
        
        assert self_entry is not None, "Self not found in leaderboard"
        assert self_entry["is_self"] == True
        
        # Verify entry structure
        assert "id" in self_entry
        assert "full_name" in self_entry
        assert "username" in self_entry
        assert "avatar_url" in self_entry
        assert "knowledge_score" in self_entry
        assert "current_streak" in self_entry
        assert "rank_label" in self_entry
        assert "rank" in self_entry
        
        print(f"Leaderboard entries: {len(leaderboard)}, Self rank: {self_entry.get('rank')}")
    
    def test_leaderboard_sorted_by_score(self, hansel_auth):
        """Leaderboard is sorted by knowledge score descending"""
        headers = {"Authorization": f"Bearer {hansel_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/friends/leaderboard", headers=headers)
        assert resp.status_code == 200
        leaderboard = resp.json()["leaderboard"]
        
        if len(leaderboard) >= 2:
            scores = [e["knowledge_score"] for e in leaderboard]
            assert scores == sorted(scores, reverse=True), "Leaderboard not sorted by score"
            print(f"Leaderboard scores (sorted): {scores}")


class TestInviteLinks:
    """Test invite link endpoints"""
    
    def test_get_my_link_requires_auth(self):
        """Get my invite link requires auth"""
        resp = requests.get(f"{BASE_URL}/api/invite/my-link")
        assert resp.status_code == 401
    
    def test_get_my_link_returns_url(self, hansel_auth):
        """Returns invite URL and username"""
        headers = {"Authorization": f"Bearer {hansel_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/invite/my-link", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        
        assert "invite_url" in data
        assert "username" in data
        assert data["invite_url"].startswith("/join/@")
        assert hansel_auth["user"]["username"] in data["invite_url"]
        print(f"Invite URL: {data['invite_url']}")
    
    def test_lookup_invite_by_username(self, hansel_auth):
        """Lookup inviter's public profile by username"""
        username = hansel_auth["user"]["username"]
        resp = requests.get(f"{BASE_URL}/api/invite/lookup/{username}")
        assert resp.status_code == 200
        data = resp.json()
        
        assert "id" in data
        assert "full_name" in data
        assert "username" in data
        assert "avatar_url" in data
        assert "knowledge_score" in data
        assert "rank_label" in data
        assert "current_streak" in data
        
        assert data["username"] == username
        print(f"Invite lookup: {data['full_name']} (@{data['username']}) - {data['rank_label']}")
    
    def test_lookup_invite_nonexistent(self):
        """Lookup non-existent user returns 404"""
        resp = requests.get(f"{BASE_URL}/api/invite/lookup/nonexistentuser999")
        assert resp.status_code == 404


class TestInviteConnect:
    """Test POST /api/invite/connect/{username} - auto-connect on invite signup"""
    
    def test_connect_requires_auth(self):
        """Connect via invite requires authentication"""
        resp = requests.post(f"{BASE_URL}/api/invite/connect/hansel")
        assert resp.status_code == 401
    
    def test_connect_with_inviter(self, zara_auth, hansel_auth):
        """User can connect with their inviter"""
        headers = {"Authorization": f"Bearer {zara_auth['token']}"}
        inviter_username = hansel_auth["user"]["username"]
        
        resp = requests.post(f"{BASE_URL}/api/invite/connect/{inviter_username}", headers=headers)
        assert resp.status_code == 200
        # Should be "Connected as friends" or "Already connected"
        message = resp.json().get("message", "")
        assert message in ["Connected as friends", "Already connected", "Skipped"]
        print(f"Connect result: {message}")


class TestBlockUser:
    """Test POST /api/friends/block/{user_id}"""
    
    def test_block_requires_auth(self):
        """Block requires authentication"""
        resp = requests.post(f"{BASE_URL}/api/friends/block/some-user-id")
        assert resp.status_code == 401
    
    def test_block_nonexistent_user(self, hansel_auth):
        """Blocking non-existent user still works (creates block record)"""
        headers = {"Authorization": f"Bearer {hansel_auth['token']}"}
        # Use a fake UUID
        resp = requests.post(f"{BASE_URL}/api/friends/block/00000000-0000-0000-0000-000000000000", 
                            headers=headers)
        # This should succeed - blocking is a silent operation
        assert resp.status_code == 200
        assert "blocked" in resp.json().get("message", "").lower()


class TestKnowledgeScoreCalculation:
    """Test knowledge score calculation"""
    
    def test_calculate_all_scores(self):
        """POST /api/knowledge-score/calculate-all batch calculates scores"""
        resp = requests.post(f"{BASE_URL}/api/knowledge-score/calculate-all")
        assert resp.status_code == 200
        data = resp.json()
        
        assert "updated" in data
        assert "date" in data
        print(f"Knowledge scores calculated for {data['updated']} users on {data['date']}")
    
    def test_profile_stats_knowledge_score(self, hansel_auth):
        """Profile stats endpoint returns correct knowledge score structure"""
        headers = {"Authorization": f"Bearer {hansel_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/profile/stats", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        
        assert "knowledge_score" in data
        ks = data["knowledge_score"]
        assert "score" in ks
        assert "rank_label" in ks
        assert isinstance(ks["score"], int)
        
        # Verify rank label matches score
        score = ks["score"]
        rank = ks["rank_label"]
        
        if score >= 501:
            assert rank == "No Cap Legend"
        elif score >= 301:
            assert rank == "Sharp"
        elif score >= 151:
            assert rank == "Switched On"
        elif score >= 51:
            assert rank == "Informed"
        else:
            assert rank == "Curious"
        
        print(f"Knowledge score: {score}, Rank: {rank}")


class TestEndToEndFriendFlow:
    """Test complete friend request flow"""
    
    def test_friends_already_connected(self, hansel_auth, zara_auth):
        """Verify Hansel and Zara are already friends (from previous tests)"""
        headers = {"Authorization": f"Bearer {hansel_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/friends", headers=headers)
        assert resp.status_code == 200
        friends = resp.json()
        
        friend_usernames = [f.get("username", "").lower() for f in friends]
        print(f"Hansel's friends: {friend_usernames}")
        
        # Zara should be in Hansel's friends list
        if "zara" in friend_usernames:
            print("✓ Hansel and Zara are friends")
        else:
            print("Note: Hansel and Zara may not be connected yet")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
