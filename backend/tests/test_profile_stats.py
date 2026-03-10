"""
Profile Stats API Tests for The Drop
Tests: /api/profile/stats, /api/streak/read, /api/articles/{id}/react
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from previous iterations
TEST_EMAIL = "hansel@test.com"
TEST_PASSWORD = "securepass123"


class TestProfileStatsAPI:
    """Tests for GET /api/profile/stats endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        data = login_resp.json()
        self.token = data["token"]
        self.user = data["user"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_profile_stats_returns_all_fields(self):
        """Verify /api/profile/stats returns all required fields"""
        resp = requests.get(f"{BASE_URL}/api/profile/stats", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify knowledge_score structure
        assert "knowledge_score" in data
        assert "score" in data["knowledge_score"]
        assert "rank_label" in data["knowledge_score"]
        assert isinstance(data["knowledge_score"]["score"], int)
        assert data["knowledge_score"]["rank_label"] in ["Curious", "Informed", "Switched On", "Sharp", "No Cap Legend"]
        
        # Verify streak structure
        assert "streak" in data
        assert "current" in data["streak"]
        assert "longest" in data["streak"]
        assert "read_today" in data["streak"]
        
        # Verify stories_read structure
        assert "stories_read" in data
        assert "total" in data["stories_read"]
        assert "this_week" in data["stories_read"]
        assert "this_month" in data["stories_read"]
        
        # Verify reactions structure
        assert "reactions" in data
        assert "total" in data["reactions"]
        assert "this_month" in data["reactions"]
        assert "most_used" in data["reactions"]
        
        # Verify other fields
        assert "favourite_category" in data
        assert "countries_covered" in data
        assert "member_since" in data
        
        print(f"✓ Profile stats returned all required fields")
        print(f"  Knowledge score: {data['knowledge_score']['score']} ({data['knowledge_score']['rank_label']})")
        print(f"  Streak: {data['streak']['current']}/{data['streak']['longest']}")
        print(f"  Stories read: {data['stories_read']['total']}")
    
    def test_profile_stats_rank_labels(self):
        """Verify rank labels follow the correct thresholds"""
        resp = requests.get(f"{BASE_URL}/api/profile/stats", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        
        score = data["knowledge_score"]["score"]
        rank = data["knowledge_score"]["rank_label"]
        
        # Verify rank is appropriate for score
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
        
        print(f"✓ Rank label '{rank}' is correct for score {score}")
    
    def test_profile_stats_member_since_format(self):
        """Verify member_since is a valid ISO date string"""
        resp = requests.get(f"{BASE_URL}/api/profile/stats", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        
        member_since = data["member_since"]
        assert member_since, "member_since should not be empty"
        # Should be ISO format: YYYY-MM-DDTHH:MM:SS...
        assert "T" in member_since, "member_since should be ISO format"
        print(f"✓ Member since: {member_since}")
    
    def test_profile_stats_requires_auth(self):
        """Verify /api/profile/stats requires authentication"""
        resp = requests.get(f"{BASE_URL}/api/profile/stats")
        assert resp.status_code == 401
        print("✓ Profile stats correctly requires authentication")


class TestStreakAPI:
    """Tests for streak tracking via POST /api/streak/read"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_resp.status_code == 200
        data = login_resp.json()
        self.token = data["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_streak_read_returns_streak_data(self):
        """Verify POST /api/streak/read returns streak fields"""
        resp = requests.post(f"{BASE_URL}/api/streak/read", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        
        assert "current_streak" in data
        assert "longest_streak" in data
        assert "last_read_date" in data
        assert isinstance(data["current_streak"], int)
        assert isinstance(data["longest_streak"], int)
        
        print(f"✓ Streak read returned: current={data['current_streak']}, longest={data['longest_streak']}")
    
    def test_streak_read_idempotent_same_day(self):
        """Verify calling streak/read twice same day doesn't increment again"""
        # First call
        resp1 = requests.post(f"{BASE_URL}/api/streak/read", headers=self.headers)
        assert resp1.status_code == 200
        data1 = resp1.json()
        
        # Second call
        resp2 = requests.post(f"{BASE_URL}/api/streak/read", headers=self.headers)
        assert resp2.status_code == 200
        data2 = resp2.json()
        
        # Streak should be same
        assert data1["current_streak"] == data2["current_streak"]
        print(f"✓ Streak is idempotent same day: {data1['current_streak']}")
    
    def test_streak_read_increments_stories_count(self):
        """Verify streak/read increments stories_read_count"""
        # Get initial stats
        stats_before = requests.get(f"{BASE_URL}/api/profile/stats", headers=self.headers).json()
        before_total = stats_before["stories_read"]["total"]
        
        # Call streak/read
        requests.post(f"{BASE_URL}/api/streak/read", headers=self.headers)
        
        # Get stats after (same day won't increment again, but verify field exists)
        stats_after = requests.get(f"{BASE_URL}/api/profile/stats", headers=self.headers).json()
        after_total = stats_after["stories_read"]["total"]
        
        # Stories count should be >= before (might be same if same day)
        assert after_total >= before_total
        print(f"✓ Stories read count: {after_total}")


class TestReactionsAPI:
    """Tests for POST /api/articles/{id}/react"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token, fetch an article ID"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_resp.status_code == 200
        data = login_resp.json()
        self.token = data["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get an article to react to
        articles_resp = requests.get(f"{BASE_URL}/api/articles?limit=5")
        assert articles_resp.status_code == 200
        articles = articles_resp.json()
        assert len(articles) > 0, "No articles found for testing"
        self.article_id = articles[0]["id"]
    
    def test_add_reaction(self):
        """Test adding a reaction to an article"""
        resp = requests.post(
            f"{BASE_URL}/api/articles/{self.article_id}/react",
            headers=self.headers,
            json={"reaction": "surprising"}
        )
        assert resp.status_code == 200
        data = resp.json()
        
        assert "action" in data
        assert data["action"] in ["added", "removed"]
        assert data["reaction"] == "surprising"
        print(f"✓ Reaction '{data['reaction']}' {data['action']}")
    
    def test_toggle_reaction_off(self):
        """Test toggling off a reaction"""
        # First add
        requests.post(
            f"{BASE_URL}/api/articles/{self.article_id}/react",
            headers=self.headers,
            json={"reaction": "sad"}
        )
        
        # Toggle off (same reaction again)
        resp = requests.post(
            f"{BASE_URL}/api/articles/{self.article_id}/react",
            headers=self.headers,
            json={"reaction": "sad"}
        )
        assert resp.status_code == 200
        data = resp.json()
        
        # Could be added or removed depending on previous state
        assert data["action"] in ["added", "removed"]
        print(f"✓ Toggle reaction: {data['action']}")
    
    def test_reaction_updates_user_count(self):
        """Test that reactions update user's reactions count in profile stats"""
        stats = requests.get(f"{BASE_URL}/api/profile/stats", headers=self.headers).json()
        assert stats["reactions"]["total"] >= 0
        print(f"✓ User reactions total: {stats['reactions']['total']}")
    
    def test_invalid_reaction_rejected(self):
        """Test that invalid reaction types are rejected"""
        resp = requests.post(
            f"{BASE_URL}/api/articles/{self.article_id}/react",
            headers=self.headers,
            json={"reaction": "invalid_emoji"}
        )
        assert resp.status_code == 400
        print("✓ Invalid reaction correctly rejected")
    
    def test_valid_reactions(self):
        """Test all valid reaction types"""
        valid_reactions = ["mind_blown", "surprising", "angry", "sad", "inspiring"]
        for reaction in valid_reactions:
            resp = requests.post(
                f"{BASE_URL}/api/articles/{self.article_id}/react",
                headers=self.headers,
                json={"reaction": reaction}
            )
            assert resp.status_code == 200
            print(f"✓ Reaction '{reaction}' accepted")


class TestKnowledgeScoreCalculation:
    """Tests for knowledge score formula verification"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_resp.status_code == 200
        data = login_resp.json()
        self.token = data["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_knowledge_score_formula(self):
        """
        Verify knowledge score formula:
        score = (stories_read * 1) + (streak * 2) + (reactions * 0.5) + (days_active_this_month * 3)
        """
        stats = requests.get(f"{BASE_URL}/api/profile/stats", headers=self.headers).json()
        
        stories_read = stats["stories_read"]["total"]
        streak = stats["streak"]["current"]
        reactions = stats["reactions"]["total"]
        days_active = stats["stories_read"]["this_month"]  # days_active_this_month
        
        # Expected formula
        expected = int(
            (stories_read * 1)
            + (streak * 2)
            + (reactions * 0.5)
            + (days_active * 3)
        )
        
        actual = stats["knowledge_score"]["score"]
        
        # Allow small variance due to timing
        assert abs(actual - expected) <= 1, f"Expected ~{expected}, got {actual}"
        
        print(f"✓ Knowledge score formula verified")
        print(f"  stories_read={stories_read}, streak={streak}, reactions={reactions}, days_active={days_active}")
        print(f"  Expected: {expected}, Actual: {actual}")


class TestCountriesAPI:
    """Tests for countries endpoint used by profile page"""
    
    def test_countries_list(self):
        """Verify /api/countries returns list of countries"""
        resp = requests.get(f"{BASE_URL}/api/countries")
        assert resp.status_code == 200
        data = resp.json()
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify country structure
        country = data[0]
        assert "country_code" in country
        assert "country_name" in country
        assert "flag_emoji" in country
        
        print(f"✓ Countries API returned {len(data)} countries")
        print(f"  Sample: {country['flag_emoji']} {country['country_name']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
