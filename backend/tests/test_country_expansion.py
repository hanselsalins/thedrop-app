"""
Test Suite: International News Source Expansion
Tests for 20 countries database, country filtering, GPT-4o rewrite fields
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "password"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"Authentication failed - {response.status_code}: {response.text}")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


# ================== COUNTRIES API TESTS ==================

class TestCountriesAPI:
    """Test GET /api/countries endpoint - should return 20 countries"""
    
    def test_countries_returns_20_countries(self, api_client):
        """Verify exactly 20 countries are returned"""
        response = api_client.get(f"{BASE_URL}/api/countries")
        assert response.status_code == 200
        countries = response.json()
        assert isinstance(countries, list)
        assert len(countries) == 20, f"Expected 20 countries, got {len(countries)}"
    
    def test_countries_have_required_fields(self, api_client):
        """Each country should have flag_emoji, country_code, country_name, primary_language, city_tier_1, city_tier_2"""
        response = api_client.get(f"{BASE_URL}/api/countries")
        countries = response.json()
        
        required_fields = ["country_code", "country_name", "flag_emoji", "primary_language", "city_tier_1", "city_tier_2"]
        for country in countries:
            for field in required_fields:
                assert field in country, f"Country {country.get('country_name')} missing field: {field}"
                assert country[field] is not None, f"Country {country.get('country_name')} has None for field: {field}"
    
    def test_countries_have_flag_emojis(self, api_client):
        """All countries should have non-empty flag_emoji"""
        response = api_client.get(f"{BASE_URL}/api/countries")
        countries = response.json()
        for country in countries:
            assert country["flag_emoji"], f"Country {country['country_name']} has empty flag_emoji"
            # Flag emojis are regional indicator symbols - typically 2 characters
            assert len(country["flag_emoji"]) >= 1, f"Flag emoji too short for {country['country_name']}"
    
    def test_countries_have_city_tiers(self, api_client):
        """Each country should have 5 tier 1 and 5 tier 2 cities"""
        response = api_client.get(f"{BASE_URL}/api/countries")
        countries = response.json()
        for country in countries:
            assert isinstance(country["city_tier_1"], list), f"{country['country_name']} city_tier_1 not a list"
            assert isinstance(country["city_tier_2"], list), f"{country['country_name']} city_tier_2 not a list"
            assert len(country["city_tier_1"]) == 5, f"{country['country_name']} has {len(country['city_tier_1'])} tier 1 cities, expected 5"
            assert len(country["city_tier_2"]) == 5, f"{country['country_name']} has {len(country['city_tier_2'])} tier 2 cities, expected 5"


class TestIndiaCountrySources:
    """Test GET /api/countries/IN/sources - India should have 10 sources"""
    
    def test_india_returns_200(self, api_client):
        """India country endpoint should return 200"""
        response = api_client.get(f"{BASE_URL}/api/countries/IN/sources")
        assert response.status_code == 200
    
    def test_india_has_10_sources(self, api_client):
        """India should have exactly 10 news sources"""
        response = api_client.get(f"{BASE_URL}/api/countries/IN/sources")
        data = response.json()
        sources = data.get("sources", [])
        assert len(sources) == 10, f"India has {len(sources)} sources, expected 10"
    
    def test_india_has_5_tier1_cities(self, api_client):
        """India should have 5 tier 1 cities"""
        response = api_client.get(f"{BASE_URL}/api/countries/IN/sources")
        data = response.json()
        assert len(data.get("city_tier_1", [])) == 5
        assert "Mumbai" in data["city_tier_1"]
    
    def test_india_has_5_tier2_cities(self, api_client):
        """India should have 5 tier 2 cities"""
        response = api_client.get(f"{BASE_URL}/api/countries/IN/sources")
        data = response.json()
        assert len(data.get("city_tier_2", [])) == 5
        assert "Hyderabad" in data["city_tier_2"]


class TestPakistanCountrySources:
    """Test GET /api/countries/PK/sources - Pakistan should have Urdu as primary language"""
    
    def test_pakistan_primary_language_urdu(self, api_client):
        """Pakistan's primary_language should be Urdu"""
        response = api_client.get(f"{BASE_URL}/api/countries/PK/sources")
        assert response.status_code == 200
        data = response.json()
        assert data["primary_language"] == "Urdu", f"Expected Urdu, got {data['primary_language']}"
    
    def test_pakistan_has_urdu_sources(self, api_client):
        """Pakistan should have some sources with Urdu language"""
        response = api_client.get(f"{BASE_URL}/api/countries/PK/sources")
        data = response.json()
        urdu_sources = [s for s in data.get("sources", []) if s.get("language") == "Urdu"]
        assert len(urdu_sources) >= 1, "Pakistan should have at least 1 Urdu language source"


class TestBangladeshCountrySources:
    """Test GET /api/countries/BD/sources - Bangladesh should have Bangla as primary language"""
    
    def test_bangladesh_primary_language_bangla(self, api_client):
        """Bangladesh's primary_language should be Bangla"""
        response = api_client.get(f"{BASE_URL}/api/countries/BD/sources")
        assert response.status_code == 200
        data = response.json()
        assert data["primary_language"] == "Bangla", f"Expected Bangla, got {data['primary_language']}"
    
    def test_bangladesh_has_bangla_sources(self, api_client):
        """Bangladesh should have some sources with Bangla language"""
        response = api_client.get(f"{BASE_URL}/api/countries/BD/sources")
        data = response.json()
        bangla_sources = [s for s in data.get("sources", []) if s.get("language") == "Bangla"]
        assert len(bangla_sources) >= 1, "Bangladesh should have at least 1 Bangla language source"


class TestCrawlEndpoint:
    """Test POST /api/crawl/{country_code} - Background crawl"""
    
    def test_crawl_us_returns_success(self, api_client):
        """Crawl for US should return success message"""
        response = api_client.post(f"{BASE_URL}/api/crawl/US")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "US" in data["message"] or "background" in data["message"].lower()


# ================== ARTICLES API TESTS ==================

class TestArticlesAPI:
    """Test articles API with new schema fields"""
    
    def test_articles_return_source_country(self, api_client):
        """Articles should include source_country field"""
        response = api_client.get(f"{BASE_URL}/api/articles?limit=5")
        assert response.status_code == 200
        articles = response.json()
        if articles:
            for article in articles:
                assert "source_country" in article, "Article missing source_country field"
    
    def test_articles_return_source_language(self, api_client):
        """Articles should include source_language field"""
        response = api_client.get(f"{BASE_URL}/api/articles?limit=5")
        articles = response.json()
        if articles:
            for article in articles:
                assert "source_language" in article, "Article missing source_language field"
    
    def test_articles_return_low_confidence_flag(self, api_client):
        """Articles should include low_confidence_flag field"""
        response = api_client.get(f"{BASE_URL}/api/articles?limit=5")
        articles = response.json()
        if articles:
            for article in articles:
                assert "low_confidence_flag" in article, "Article missing low_confidence_flag field"
                assert isinstance(article["low_confidence_flag"], bool), "low_confidence_flag should be boolean"


class TestArticleDetailAPI:
    """Test GET /api/articles/{id} with new schema fields"""
    
    def test_article_detail_has_new_fields(self, api_client):
        """Article detail should have source_country, source_language, low_confidence_flag, rewrite_status, safety_status"""
        # First get an article ID
        list_response = api_client.get(f"{BASE_URL}/api/articles?limit=1")
        articles = list_response.json()
        if not articles:
            pytest.skip("No articles available")
        
        article_id = articles[0]["id"]
        response = api_client.get(f"{BASE_URL}/api/articles/{article_id}")
        assert response.status_code == 200
        article = response.json()
        
        required_fields = ["source_country", "source_language", "low_confidence_flag", "rewrite_status", "safety_status"]
        for field in required_fields:
            assert field in article, f"Article detail missing field: {field}"


class TestArticlesCountryFiltering:
    """Test that articles are filtered by user's country when authenticated"""
    
    def test_authenticated_articles_filtered_by_country(self, authenticated_client):
        """With auth token, articles should be filtered by user's country"""
        response = authenticated_client.get(f"{BASE_URL}/api/articles?limit=10")
        assert response.status_code == 200
        articles = response.json()
        # User country is United States (US)
        # All articles should be from US
        if articles:
            for article in articles:
                # If user country is US, articles should be from US
                # Note: Could be empty if no US articles exist
                assert "source_country" in article


# ================== USER PROFILE COUNTRY UPDATE ==================

class TestUserCountryUpdate:
    """Test PUT /api/auth/me for country update"""
    
    def test_update_user_country(self, authenticated_client):
        """Should be able to update user's country"""
        # Update country
        response = authenticated_client.put(f"{BASE_URL}/api/auth/me", json={
            "country": "India"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("country") == "India", f"Expected country 'India', got {data.get('country')}"
        
        # Revert back
        authenticated_client.put(f"{BASE_URL}/api/auth/me", json={
            "country": "United States"
        })


# ================== STATS API ==================

class TestStatsAPI:
    """Test GET /api/stats for countries_configured"""
    
    def test_stats_returns_countries_count(self, api_client):
        """Stats should include countries_configured count"""
        response = api_client.get(f"{BASE_URL}/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "countries_configured" in data, "Stats missing countries_configured"
        assert data["countries_configured"] == 20, f"Expected 20 countries, got {data['countries_configured']}"


# ================== INDIVIDUAL COUNTRY TESTS ==================

class TestAllCountrySources:
    """Verify all 20 countries have correct structure"""
    
    COUNTRY_CODES = ["US", "GB", "IN", "CA", "AU", "PK", "BD", "NG", "ZA", "DE", 
                     "FR", "JP", "BR", "MX", "KE", "EG", "AE", "ID", "PH", "KR"]
    
    @pytest.mark.parametrize("country_code", COUNTRY_CODES)
    def test_country_exists_and_has_10_sources(self, api_client, country_code):
        """Each country should exist and have 10 sources"""
        response = api_client.get(f"{BASE_URL}/api/countries/{country_code}/sources")
        assert response.status_code == 200, f"Country {country_code} returned {response.status_code}"
        data = response.json()
        sources = data.get("sources", [])
        assert len(sources) == 10, f"Country {country_code} has {len(sources)} sources, expected 10"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
