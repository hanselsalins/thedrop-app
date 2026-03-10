import requests
import json
import sys
from datetime import datetime, date
import time

class NewsAggregatorAPITester:
    def __init__(self, base_url="https://news-cards-kids.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.auth_token = None
        self.test_user_id = None

    def log_test(self, name, success, details="", expected_status=None, actual_status=None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": name,
            "success": success,
            "details": details,
            "expected_status": expected_status,
            "actual_status": actual_status
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    Details: {details}")
        if not success and expected_status and actual_status:
            print(f"    Expected: {expected_status}, Got: {actual_status}")
        print()

    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/")
            success = response.status_code == 200
            details = f"Response: {response.json()}" if success else f"Error: {response.text}"
            self.log_test("API Root", success, details, 200, response.status_code)
            return success
        except Exception as e:
            self.log_test("API Root", False, f"Exception: {str(e)}")
            return False

    def test_get_categories(self):
        """Test GET /api/categories - should return 6 categories"""
        try:
            response = requests.get(f"{self.base_url}/api/categories")
            if response.status_code == 200:
                categories = response.json()
                if len(categories) == 6:
                    expected_cats = ["world", "science", "money", "history", "entertainment", "local"]
                    actual_cats = [cat["id"] for cat in categories]
                    if all(cat in actual_cats for cat in expected_cats):
                        details = f"Found all 6 categories: {actual_cats}"
                        self.log_test("GET Categories", True, details)
                        return True
                    else:
                        details = f"Missing categories. Expected: {expected_cats}, Got: {actual_cats}"
                        self.log_test("GET Categories", False, details)
                        return False
                else:
                    details = f"Expected 6 categories, got {len(categories)}"
                    self.log_test("GET Categories", False, details)
                    return False
            else:
                self.log_test("GET Categories", False, f"HTTP {response.status_code}", 200, response.status_code)
                return False
        except Exception as e:
            self.log_test("GET Categories", False, f"Exception: {str(e)}")
            return False

    def test_register_user(self):
        """Test POST /api/auth/register - create user with all fields and auto-calculate age group"""
        try:
            # Test user data with DOB that should result in 14-16 age group
            test_data = {
                "full_name": "Test User Auth",
                "email": f"testauth_{int(time.time())}@example.com",
                "password": "testpass123",
                "dob": "2010-01-15",  # Should result in 14-16 age group
                "gender": "male",
                "city": "Test City",
                "country": "United States"
            }
            
            response = requests.post(f"{self.base_url}/api/auth/register", json=test_data)
            
            if response.status_code == 200:
                result = response.json()
                if "token" in result and "user" in result:
                    user = result["user"]
                    required_fields = ["id", "full_name", "email", "dob", "gender", "city", "country", "age_group", "created_at"]
                    missing_fields = [field for field in required_fields if field not in user]
                    
                    if not missing_fields:
                        # Verify age group calculation
                        expected_age_group = self.calculate_expected_age_group(test_data["dob"])
                        if user["age_group"] == expected_age_group:
                            self.auth_token = result["token"]
                            self.test_user_id = user["id"]
                            details = f"Created user: {user['id']}, age_group: {user['age_group']}"
                            self.log_test("POST /auth/register", True, details)
                            return True
                        else:
                            details = f"Age group calculation error: expected {expected_age_group}, got {user['age_group']}"
                            self.log_test("POST /auth/register", False, details)
                            return False
                    else:
                        details = f"Missing fields in user: {missing_fields}"
                        self.log_test("POST /auth/register", False, details)
                        return False
                else:
                    details = f"Missing token or user in response: {result.keys()}"
                    self.log_test("POST /auth/register", False, details)
                    return False
            else:
                self.log_test("POST /auth/register", False, f"HTTP {response.status_code}: {response.text}", 200, response.status_code)
                return False
        except Exception as e:
            self.log_test("POST /auth/register", False, f"Exception: {str(e)}")
            return False

    def calculate_expected_age_group(self, dob_str):
        """Helper to calculate expected age group from DOB"""
        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age <= 10:
                return "8-10"
            elif age <= 13:
                return "11-13"
            elif age <= 16:
                return "14-16"
            else:
                return "17-20"
        except Exception:
            return "14-16"

    def test_login_existing_user(self):
        """Test POST /api/auth/login with existing test user"""
        try:
            test_credentials = {
                "email": "test@example.com",
                "password": "test123"
            }
            
            response = requests.post(f"{self.base_url}/api/auth/login", json=test_credentials)
            
            if response.status_code == 200:
                result = response.json()
                if "token" in result and "user" in result:
                    user = result["user"]
                    required_fields = ["id", "full_name", "email", "age_group"]
                    missing_fields = [field for field in required_fields if field not in user]
                    
                    if not missing_fields:
                        details = f"Logged in existing user: {user['email']}, age_group: {user.get('age_group', 'N/A')}"
                        self.log_test("POST /auth/login (existing user)", True, details)
                        return True
                    else:
                        details = f"Missing fields in user: {missing_fields}"
                        self.log_test("POST /auth/login (existing user)", False, details)
                        return False
                else:
                    details = f"Missing token or user in response: {result.keys()}"
                    self.log_test("POST /auth/login (existing user)", False, details)
                    return False
            else:
                self.log_test("POST /auth/login (existing user)", False, f"HTTP {response.status_code}: {response.text}", 200, response.status_code)
                return False
        except Exception as e:
            self.log_test("POST /auth/login (existing user)", False, f"Exception: {str(e)}")
            return False

    def test_auth_me_endpoint(self):
        """Test GET /api/auth/me - get current authenticated user"""
        if not self.auth_token:
            self.log_test("GET /auth/me", False, "No auth token available from register test")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
            
            if response.status_code == 200:
                user = response.json()
                required_fields = ["id", "full_name", "email", "age_group"]
                missing_fields = [field for field in required_fields if field not in user]
                
                if not missing_fields:
                    if user["id"] == self.test_user_id:
                        details = f"Retrieved authenticated user: {user['id']}"
                        self.log_test("GET /auth/me", True, details)
                        return True
                    else:
                        details = f"User ID mismatch: expected {self.test_user_id}, got {user['id']}"
                        self.log_test("GET /auth/me", False, details)
                        return False
                else:
                    details = f"Missing fields: {missing_fields}"
                    self.log_test("GET /auth/me", False, details)
                    return False
            else:
                self.log_test("GET /auth/me", False, f"HTTP {response.status_code}", 200, response.status_code)
                return False
        except Exception as e:
            self.log_test("GET /auth/me", False, f"Exception: {str(e)}")
            return False

    def test_update_user_profile(self):
        """Test PUT /api/auth/me - update user location"""
        if not self.auth_token:
            self.log_test("PUT /auth/me", False, "No auth token available from register test")
            return False
        
        try:
            update_data = {
                "city": "Updated City", 
                "country": "Updated Country"
            }
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.put(f"{self.base_url}/api/auth/me", json=update_data, headers=headers)
            
            if response.status_code == 200:
                user = response.json()
                if user.get("city") == "Updated City" and user.get("country") == "Updated Country":
                    details = f"Updated user location successfully"
                    self.log_test("PUT /auth/me", True, details)
                    return True
                else:
                    details = f"Location not updated properly: city={user.get('city')}, country={user.get('country')}"
                    self.log_test("PUT /auth/me", False, details)
                    return False
            else:
                self.log_test("PUT /auth/me", False, f"HTTP {response.status_code}", 200, response.status_code)
                return False
        except Exception as e:
            self.log_test("PUT /auth/me", False, f"Exception: {str(e)}")
            return False

    def test_invalid_credentials(self):
        """Test login with invalid credentials"""
        try:
            invalid_credentials = {
                "email": "nonexistent@example.com",
                "password": "wrongpassword"
            }
            
            response = requests.post(f"{self.base_url}/api/auth/login", json=invalid_credentials)
            
            if response.status_code == 401:
                details = "Properly rejected invalid credentials"
                self.log_test("Invalid Credentials Test", True, details)
                return True
            else:
                details = f"Should have returned 401 for invalid credentials, got {response.status_code}"
                self.log_test("Invalid Credentials Test", False, details)
                return False
        except Exception as e:
            self.log_test("Invalid Credentials Test", False, f"Exception: {str(e)}")
            return False

    def test_duplicate_email_registration(self):
        """Test registering with already used email"""
        try:
            duplicate_data = {
                "full_name": "Duplicate User",
                "email": "test@example.com",  # This email should already exist
                "password": "testpass123",
                "dob": "2008-01-15",
                "gender": "female",
                "city": "Test City",
                "country": "United States"
            }
            
            response = requests.post(f"{self.base_url}/api/auth/register", json=duplicate_data)
            
            if response.status_code == 400:
                details = "Properly rejected duplicate email registration"
                self.log_test("Duplicate Email Test", True, details)
                return True
            else:
                details = f"Should have returned 400 for duplicate email, got {response.status_code}"
                self.log_test("Duplicate Email Test", False, details)
                return False
        except Exception as e:
            self.log_test("Duplicate Email Test", False, f"Exception: {str(e)}")
            return False

    def test_unauthenticated_access(self):
        """Test accessing /auth/me without token"""
        try:
            response = requests.get(f"{self.base_url}/api/auth/me")
            
            if response.status_code == 401:
                details = "Properly rejected unauthenticated access"
                self.log_test("Unauthenticated Access Test", True, details)
                return True
            else:
                details = f"Should have returned 401 for unauthenticated access, got {response.status_code}"
                self.log_test("Unauthenticated Access Test", False, details)
                return False
        except Exception as e:
            self.log_test("Unauthenticated Access Test", False, f"Exception: {str(e)}")
            return False

    def test_get_articles(self):
        """Test GET /api/articles - should return articles with rewrites"""
        try:
            params = {"age_group": "14-16", "limit": 10}
            response = requests.get(f"{self.base_url}/api/articles", params=params)
            
            if response.status_code == 200:
                articles = response.json()
                if len(articles) > 0:
                    # Check first article structure
                    article = articles[0]
                    required_fields = ["id", "original_title", "original_url", "source", "category", "image_url", "published_at"]
                    missing_fields = [field for field in required_fields if field not in article]
                    
                    if not missing_fields:
                        details = f"Found {len(articles)} articles with proper structure"
                        if article.get("rewrite"):
                            details += f", rewrites available"
                        self.log_test("GET Articles", True, details)
                        return True
                    else:
                        details = f"Missing fields in article: {missing_fields}"
                        self.log_test("GET Articles", False, details)
                        return False
                else:
                    details = "No articles found - this may indicate crawling hasn't happened yet"
                    self.log_test("GET Articles", False, details)
                    return False
            else:
                self.log_test("GET Articles", False, f"HTTP {response.status_code}", 200, response.status_code)
                return False
        except Exception as e:
            self.log_test("GET Articles", False, f"Exception: {str(e)}")
            return False

    def test_get_articles_by_category(self):
        """Test GET /api/articles with category filter"""
        try:
            params = {"age_group": "14-16", "category": "world", "limit": 5}
            response = requests.get(f"{self.base_url}/api/articles", params=params)
            
            if response.status_code == 200:
                articles = response.json()
                if len(articles) > 0:
                    # Check if all articles are from world category
                    world_articles = [a for a in articles if a.get("category") == "world"]
                    if len(world_articles) == len(articles):
                        details = f"Found {len(articles)} world category articles"
                        self.log_test("GET Articles (By Category)", True, details)
                        return True
                    else:
                        details = f"Category filter not working: {len(world_articles)}/{len(articles)} world articles"
                        self.log_test("GET Articles (By Category)", False, details)
                        return False
                else:
                    details = "No world articles found"
                    self.log_test("GET Articles (By Category)", False, details)
                    return False
            else:
                self.log_test("GET Articles (By Category)", False, f"HTTP {response.status_code}", 200, response.status_code)
                return False
        except Exception as e:
            self.log_test("GET Articles (By Category)", False, f"Exception: {str(e)}")
            return False

    def test_get_single_article(self):
        """Test GET /api/articles/{id} - get single article detail"""
        # First get an article ID
        try:
            response = requests.get(f"{self.base_url}/api/articles", params={"limit": 1})
            if response.status_code != 200 or len(response.json()) == 0:
                self.log_test("GET Single Article", False, "No articles available to test single article endpoint")
                return False
            
            article_id = response.json()[0]["id"]
            
            # Now test single article endpoint
            response = requests.get(f"{self.base_url}/api/articles/{article_id}", params={"age_group": "14-16"})
            
            if response.status_code == 200:
                article = response.json()
                required_fields = ["id", "original_title", "original_url", "source", "category", "image_url", "published_at", "original_content"]
                missing_fields = [field for field in required_fields if field not in article]
                
                if not missing_fields:
                    details = f"Retrieved article {article_id} with all fields"
                    if article.get("rewrite"):
                        details += f", rewrite available"
                    self.log_test("GET Single Article", True, details)
                    return True
                else:
                    details = f"Missing fields: {missing_fields}"
                    self.log_test("GET Single Article", False, details)
                    return False
            else:
                self.log_test("GET Single Article", False, f"HTTP {response.status_code}", 200, response.status_code)
                return False
        except Exception as e:
            self.log_test("GET Single Article", False, f"Exception: {str(e)}")
            return False

    def test_get_stats(self):
        """Test GET /api/stats - should return article and user counts"""
        try:
            response = requests.get(f"{self.base_url}/api/stats")
            if response.status_code == 200:
                stats = response.json()
                required_fields = ["total_articles", "total_users", "by_category"]
                missing_fields = [field for field in required_fields if field not in stats]
                
                if not missing_fields:
                    details = f"Stats: {stats['total_articles']} articles, {stats['total_users']} users"
                    self.log_test("GET Stats", True, details)
                    return True
                else:
                    details = f"Missing fields in stats: {missing_fields}"
                    self.log_test("GET Stats", False, details)
                    return False
            else:
                self.log_test("GET Stats", False, f"HTTP {response.status_code}", 200, response.status_code)
                return False
        except Exception as e:
            self.log_test("GET Stats", False, f"Exception: {str(e)}")
            return False

    def test_invalid_age_group(self):
        """Test registering with invalid data"""
        try:
            # Test with missing required fields
            test_data = {
                "full_name": "",  # Empty name
                "email": "invalid-email",  # Invalid email format
                "password": "123",  # Too short password
                "dob": "2050-01-15",  # Future date
                "gender": "male",
                "city": "Test City", 
                "country": "United States"
            }
            response = requests.post(f"{self.base_url}/api/auth/register", json=test_data)
            
            if response.status_code == 400:
                details = "Properly rejected invalid registration data"
                self.log_test("Invalid Registration Data Test", True, details)
                return True
            else:
                details = f"Should have returned 400 for invalid data, got {response.status_code}"
                self.log_test("Invalid Registration Data Test", False, details)
                return False
        except Exception as e:
            self.log_test("Invalid Registration Data Test", False, f"Exception: {str(e)}")
            return False

    # ========== NEW ENGAGEMENT FEATURES TESTS ==========

    def test_get_streak(self):
        """Test GET /api/streak - get reading streak for authenticated user"""
        if not self.auth_token:
            self.log_test("GET Streak", False, "No auth token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.get(f"{self.base_url}/api/streak", headers=headers)
            
            if response.status_code == 200:
                streak = response.json()
                required_fields = ["current_streak", "longest_streak", "last_read_date", "read_today"]
                missing_fields = [field for field in required_fields if field not in streak]
                
                if not missing_fields:
                    details = f"Current: {streak['current_streak']}, Longest: {streak['longest_streak']}, Read today: {streak['read_today']}"
                    self.log_test("GET Streak", True, details)
                    return True
                else:
                    details = f"Missing fields: {missing_fields}"
                    self.log_test("GET Streak", False, details)
                    return False
            else:
                self.log_test("GET Streak", False, f"HTTP {response.status_code}", 200, response.status_code)
                return False
        except Exception as e:
            self.log_test("GET Streak", False, f"Exception: {str(e)}")
            return False

    def test_record_read(self):
        """Test POST /api/streak/read - record a read and update streak"""
        if not self.auth_token:
            self.log_test("POST Streak Read", False, "No auth token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.post(f"{self.base_url}/api/streak/read", json={}, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                required_fields = ["current_streak", "longest_streak", "last_read_date"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if not missing_fields:
                    details = f"Updated streak - Current: {result['current_streak']}, Longest: {result['longest_streak']}"
                    self.log_test("POST Streak Read", True, details)
                    return True
                else:
                    details = f"Missing fields: {missing_fields}"
                    self.log_test("POST Streak Read", False, details)
                    return False
            else:
                self.log_test("POST Streak Read", False, f"HTTP {response.status_code}", 200, response.status_code)
                return False
        except Exception as e:
            self.log_test("POST Streak Read", False, f"Exception: {str(e)}")
            return False

    def test_article_reaction(self):
        """Test POST /api/articles/{id}/react - toggle reaction"""
        if not self.auth_token:
            self.log_test("Article React", False, "No auth token available")
            return False
            
        try:
            # Get an article first
            response = requests.get(f"{self.base_url}/api/articles", params={"limit": 1})
            if response.status_code != 200 or len(response.json()) == 0:
                self.log_test("Article React", False, "No articles available for reaction test")
                return False
            
            article_id = response.json()[0]["id"]
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test adding a reaction
            reaction_data = {"reaction": "mind_blown"}
            response = requests.post(f"{self.base_url}/api/articles/{article_id}/react", 
                                   json=reaction_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if "action" in result and "reaction" in result:
                    action = result["action"]
                    reaction = result["reaction"]
                    details = f"Reaction {reaction} {action} successfully"
                    self.log_test("Article React", True, details)
                    return True
                else:
                    details = f"Missing action/reaction in response: {result}"
                    self.log_test("Article React", False, details)
                    return False
            else:
                self.log_test("Article React", False, f"HTTP {response.status_code}", 200, response.status_code)
                return False
        except Exception as e:
            self.log_test("Article React", False, f"Exception: {str(e)}")
            return False

    def test_get_article_reactions(self):
        """Test GET /api/articles/{id}/reactions - get reaction counts"""
        try:
            # Get an article first
            response = requests.get(f"{self.base_url}/api/articles", params={"limit": 1})
            if response.status_code != 200 or len(response.json()) == 0:
                self.log_test("Get Article Reactions", False, "No articles available for reaction test")
                return False
            
            article_id = response.json()[0]["id"]
            headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
            
            response = requests.get(f"{self.base_url}/api/articles/{article_id}/reactions", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if "counts" in result:
                    counts = result["counts"]
                    user_reaction = result.get("user_reaction")
                    details = f"Reaction counts: {counts}, user_reaction: {user_reaction}"
                    self.log_test("Get Article Reactions", True, details)
                    return True
                else:
                    details = f"Missing counts in response: {result}"
                    self.log_test("Get Article Reactions", False, details)
                    return False
            else:
                self.log_test("Get Article Reactions", False, f"HTTP {response.status_code}", 200, response.status_code)
                return False
        except Exception as e:
            self.log_test("Get Article Reactions", False, f"Exception: {str(e)}")
            return False

    def test_get_micro_facts(self):
        """Test GET /api/micro-facts - get micro-facts for age group"""
        try:
            response = requests.get(f"{self.base_url}/api/micro-facts", params={"age_group": "8-10"})
            
            if response.status_code == 200:
                facts = response.json()
                if isinstance(facts, list):
                    if len(facts) > 0:
                        fact = facts[0]
                        required_fields = ["fact", "category"]
                        missing_fields = [field for field in required_fields if field not in fact]
                        
                        if not missing_fields:
                            details = f"Found {len(facts)} micro-facts for age group 8-10"
                            self.log_test("GET Micro Facts", True, details)
                            return True
                        else:
                            details = f"Missing fields in micro-fact: {missing_fields}"
                            self.log_test("GET Micro Facts", False, details)
                            return False
                    else:
                        details = "No micro-facts found - may need to be generated"
                        self.log_test("GET Micro Facts", False, details)
                        return False
                else:
                    details = f"Expected array, got: {type(facts)}"
                    self.log_test("GET Micro Facts", False, details)
                    return False
            else:
                self.log_test("GET Micro Facts", False, f"HTTP {response.status_code}", 200, response.status_code)
                return False
        except Exception as e:
            self.log_test("GET Micro Facts", False, f"Exception: {str(e)}")
            return False

    def test_get_source_logos(self):
        """Test GET /api/source-logos - get source logos"""
        try:
            response = requests.get(f"{self.base_url}/api/source-logos")
            
            if response.status_code == 200:
                logos = response.json()
                if isinstance(logos, list):
                    if len(logos) > 0:
                        logo = logos[0]
                        required_fields = ["source", "logo_url"]
                        missing_fields = [field for field in required_fields if field not in logo]
                        
                        if not missing_fields:
                            details = f"Found {len(logos)} source logos"
                            self.log_test("GET Source Logos", True, details)
                            return True
                        else:
                            details = f"Missing fields in source logo: {missing_fields}"
                            self.log_test("GET Source Logos", False, details)
                            return False
                    else:
                        details = "No source logos found"
                        self.log_test("GET Source Logos", False, details)
                        return False
                else:
                    details = f"Expected array, got: {type(logos)}"
                    self.log_test("GET Source Logos", False, details)
                    return False
            else:
                self.log_test("GET Source Logos", False, f"HTTP {response.status_code}", 200, response.status_code)
                return False
        except Exception as e:
            self.log_test("GET Source Logos", False, f"Exception: {str(e)}")
            return False

    def test_articles_include_engagement_fields(self):
        """Test GET /api/articles includes new engagement fields"""
        try:
            params = {"age_group": "8-10", "limit": 5}
            response = requests.get(f"{self.base_url}/api/articles", params=params)
            
            if response.status_code == 200:
                articles = response.json()
                if len(articles) > 0:
                    article = articles[0]
                    engagement_fields = ["source_logo", "reaction_counts", "why_reason"]
                    missing_fields = [field for field in engagement_fields if field not in article]
                    
                    if not missing_fields:
                        details = f"Articles include all engagement fields: {engagement_fields}"
                        self.log_test("Articles Engagement Fields", True, details)
                        return True
                    else:
                        details = f"Missing engagement fields: {missing_fields}"
                        self.log_test("Articles Engagement Fields", False, details)
                        return False
                else:
                    details = "No articles found to test engagement fields"
                    self.log_test("Articles Engagement Fields", False, details)
                    return False
            else:
                self.log_test("Articles Engagement Fields", False, f"HTTP {response.status_code}", 200, response.status_code)
                return False
        except Exception as e:
            self.log_test("Articles Engagement Fields", False, f"Exception: {str(e)}")
            return False

    def test_invalid_reaction(self):
        """Test invalid reaction types are rejected"""
        if not self.auth_token:
            self.log_test("Invalid Reaction Test", False, "No auth token available")
            return False
            
        try:
            # Get an article first
            response = requests.get(f"{self.base_url}/api/articles", params={"limit": 1})
            if response.status_code != 200 or len(response.json()) == 0:
                self.log_test("Invalid Reaction Test", False, "No articles available")
                return False
            
            article_id = response.json()[0]["id"]
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test invalid reaction
            reaction_data = {"reaction": "invalid_reaction"}
            response = requests.post(f"{self.base_url}/api/articles/{article_id}/react", 
                                   json=reaction_data, headers=headers)
            
            if response.status_code == 400:
                details = "Properly rejected invalid reaction type"
                self.log_test("Invalid Reaction Test", True, details)
                return True
            else:
                details = f"Should have returned 400 for invalid reaction, got {response.status_code}"
                self.log_test("Invalid Reaction Test", False, details)
                return False
        except Exception as e:
            self.log_test("Invalid Reaction Test", False, f"Exception: {str(e)}")
            return False

    # ========== NOTIFICATION SYSTEM TESTS ==========

    def test_get_notification_settings(self):
        """Test GET /api/notifications/settings - returns user notification preferences"""
        if not self.auth_token:
            self.log_test("GET Notification Settings", False, "No auth token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.get(f"{self.base_url}/api/notifications/settings", headers=headers)
            
            if response.status_code == 200:
                settings = response.json()
                required_fields = ["streak_reminders", "milestone_alerts", "daily_news_alerts", "has_device_token", "timezone"]
                missing_fields = [field for field in required_fields if field not in settings]
                
                if not missing_fields:
                    details = f"Settings: streak_reminders={settings['streak_reminders']}, milestone_alerts={settings['milestone_alerts']}, daily_news_alerts={settings['daily_news_alerts']}"
                    self.log_test("GET Notification Settings", True, details)
                    return True
                else:
                    details = f"Missing fields: {missing_fields}"
                    self.log_test("GET Notification Settings", False, details)
                    return False
            else:
                self.log_test("GET Notification Settings", False, f"HTTP {response.status_code}", 200, response.status_code)
                return False
        except Exception as e:
            self.log_test("GET Notification Settings", False, f"Exception: {str(e)}")
            return False

    def test_update_notification_settings(self):
        """Test PUT /api/notifications/settings - updates notification toggles"""
        if not self.auth_token:
            self.log_test("PUT Notification Settings", False, "No auth token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Update specific settings
            update_data = {
                "streak_reminders": False,
                "milestone_alerts": True,
                "daily_news_alerts": False
            }
            
            response = requests.put(f"{self.base_url}/api/notifications/settings", 
                                  json=update_data, headers=headers)
            
            if response.status_code == 200:
                settings = response.json()
                if (settings.get("streak_reminders") == False and 
                    settings.get("milestone_alerts") == True and 
                    settings.get("daily_news_alerts") == False):
                    details = "Successfully updated notification preferences"
                    self.log_test("PUT Notification Settings", True, details)
                    return True
                else:
                    details = f"Settings not updated correctly: {settings}"
                    self.log_test("PUT Notification Settings", False, details)
                    return False
            else:
                self.log_test("PUT Notification Settings", False, f"HTTP {response.status_code}", 200, response.status_code)
                return False
        except Exception as e:
            self.log_test("PUT Notification Settings", False, f"Exception: {str(e)}")
            return False

    def test_register_device_token(self):
        """Test POST /api/notifications/register-device - stores device token"""
        if not self.auth_token:
            self.log_test("POST Register Device", False, "No auth token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            device_data = {
                "token": f"test_device_token_{int(time.time())}",
                "platform": "web"
            }
            
            response = requests.post(f"{self.base_url}/api/notifications/register-device", 
                                   json=device_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if "message" in result and "token_count" in result:
                    details = f"Device registered: {result['message']}, tokens: {result['token_count']}"
                    self.log_test("POST Register Device", True, details)
                    return True
                else:
                    details = f"Missing fields in response: {result}"
                    self.log_test("POST Register Device", False, details)
                    return False
            else:
                self.log_test("POST Register Device", False, f"HTTP {response.status_code}", 200, response.status_code)
                return False
        except Exception as e:
            self.log_test("POST Register Device", False, f"Exception: {str(e)}")
            return False

    def test_check_streak_reminders(self):
        """Test POST /api/notifications/check-streaks - queues reminders for users who haven't read today"""
        try:
            response = requests.post(f"{self.base_url}/api/notifications/check-streaks")
            
            if response.status_code == 200:
                result = response.json()
                if "checked" in result and "reminders_queued" in result:
                    details = f"Checked {result['checked']} users, queued {result['reminders_queued']} reminders"
                    self.log_test("POST Check Streaks", True, details)
                    return True
                else:
                    details = f"Missing fields in response: {result}"
                    self.log_test("POST Check Streaks", False, details)
                    return False
            else:
                self.log_test("POST Check Streaks", False, f"HTTP {response.status_code}", 200, response.status_code)
                return False
        except Exception as e:
            self.log_test("POST Check Streaks", False, f"Exception: {str(e)}")
            return False

    def test_get_notification_log(self):
        """Test GET /api/notifications/log - returns notification history"""
        if not self.auth_token:
            self.log_test("GET Notification Log", False, "No auth token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.get(f"{self.base_url}/api/notifications/log", headers=headers)
            
            if response.status_code == 200:
                logs = response.json()
                if isinstance(logs, list):
                    details = f"Retrieved {len(logs)} notification log entries"
                    self.log_test("GET Notification Log", True, details)
                    return True
                else:
                    details = f"Expected array, got: {type(logs)}"
                    self.log_test("GET Notification Log", False, details)
                    return False
            else:
                self.log_test("GET Notification Log", False, f"HTTP {response.status_code}", 200, response.status_code)
                return False
        except Exception as e:
            self.log_test("GET Notification Log", False, f"Exception: {str(e)}")
            return False

    def test_milestone_notification(self):
        """Test POST /api/streak/read returns milestone field when hitting a milestone"""
        if not self.auth_token:
            self.log_test("Milestone Notification Test", False, "No auth token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Record reads to potentially hit a milestone (this user is likely at 1 streak)
            response = requests.post(f"{self.base_url}/api/streak/read", json={}, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                required_fields = ["current_streak", "longest_streak", "last_read_date"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if not missing_fields:
                    milestone = result.get("milestone")
                    if milestone:
                        details = f"Milestone reached: {milestone.get('milestone')} days - {milestone.get('message')}"
                    else:
                        details = f"No milestone this time (streak: {result['current_streak']})"
                    self.log_test("Milestone Notification Test", True, details)
                    return True
                else:
                    details = f"Missing fields: {missing_fields}"
                    self.log_test("Milestone Notification Test", False, details)
                    return False
            else:
                self.log_test("Milestone Notification Test", False, f"HTTP {response.status_code}", 200, response.status_code)
                return False
        except Exception as e:
            self.log_test("Milestone Notification Test", False, f"Exception: {str(e)}")
            return False

    def test_notification_rate_limiting(self):
        """Test rate limiting - max 2 notifications per user per day"""
        if not self.auth_token:
            self.log_test("Notification Rate Limiting", False, "No auth token available")
            return False
            
        try:
            # First, trigger some notifications by checking streaks multiple times
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Check current notification count first
            response = requests.get(f"{self.base_url}/api/notifications/log", headers=headers)
            if response.status_code != 200:
                self.log_test("Notification Rate Limiting", False, "Cannot access notification log")
                return False
            
            initial_logs = response.json()
            initial_count = len([log for log in initial_logs if log.get("timestamp", "").startswith(date.today().isoformat())])
            
            # Try to trigger streak reminders multiple times
            for i in range(3):
                response = requests.post(f"{self.base_url}/api/notifications/check-streaks")
                time.sleep(0.5)  # Small delay between requests
            
            # Check final notification count
            response = requests.get(f"{self.base_url}/api/notifications/log", headers=headers)
            if response.status_code == 200:
                final_logs = response.json()
                final_count = len([log for log in final_logs if log.get("timestamp", "").startswith(date.today().isoformat())])
                
                if final_count <= 2:  # Rate limiting should prevent more than 2 per day
                    details = f"Rate limiting working: {final_count} notifications today (max 2)"
                    self.log_test("Notification Rate Limiting", True, details)
                    return True
                else:
                    details = f"Rate limiting failed: {final_count} notifications today (should be max 2)"
                    self.log_test("Notification Rate Limiting", False, details)
                    return False
            else:
                self.log_test("Notification Rate Limiting", False, "Cannot verify final notification count")
                return False
        except Exception as e:
            self.log_test("Notification Rate Limiting", False, f"Exception: {str(e)}")
            return False

def main():
    print("🧪 Starting News Aggregator API Tests (Auth & Engagement Features)")
    print("=" * 60)
    
    tester = NewsAggregatorAPITester()
    
    # Authentication & Core API tests
    tests_to_run = [
        tester.test_api_root,
        tester.test_get_categories,
        tester.test_register_user,
        tester.test_auth_me_endpoint,
        tester.test_update_user_profile,
        tester.test_login_existing_user,
        tester.test_invalid_credentials,
        tester.test_duplicate_email_registration,
        tester.test_unauthenticated_access,
        tester.test_get_articles,
        tester.test_get_articles_by_category,
        tester.test_get_single_article,
        tester.test_get_stats,
        tester.test_invalid_age_group,
        
        # Engagement Features Tests
        tester.test_get_streak,
        tester.test_record_read,
        tester.test_article_reaction,
        tester.test_get_article_reactions,
        tester.test_get_micro_facts,
        tester.test_get_source_logos,
        tester.test_articles_include_engagement_fields,
        tester.test_invalid_reaction,
        
        # Notification System Tests
        tester.test_get_notification_settings,
        tester.test_update_notification_settings,
        tester.test_register_device_token,
        tester.test_check_streak_reminders,
        tester.test_get_notification_log,
        tester.test_milestone_notification,
        tester.test_notification_rate_limiting,
    ]
    
    # Run all tests
    for test in tests_to_run:
        test()
        time.sleep(0.5)  # Brief pause between tests
    
    # Print final results
    print("=" * 60)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        print("\nFailed tests:")
        for result in tester.test_results:
            if not result["success"]:
                print(f"  - {result['test']}: {result['details']}")
        return 1

if __name__ == "__main__":
    sys.exit(main())