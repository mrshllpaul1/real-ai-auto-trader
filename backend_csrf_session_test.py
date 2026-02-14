#!/usr/bin/env python3
"""
CSRF Protection and Session-Based Authentication Testing Script

Tests the newly implemented CSRF protection and session-based authentication
according to the detailed test plan provided in the review request.
"""

import requests
import json
import sys
import time
from urllib.parse import urljoin


class CSRFSessionTester:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.csrf_token = None
        self.session_token = None
        
    def url(self, path):
        """Build full URL from path"""
        return urljoin(f"{self.base_url}/", path.lstrip('/'))
    
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {test_name}")
        if details:
            print(f"     Details: {details}")
        if not success:
            print(f"     Expected behavior not observed")
        print()
    
    def test_health_endpoints(self):
        """Test 1: Health Endpoints (should work without any auth)"""
        print("=" * 60)
        print("TEST 1: HEALTH ENDPOINTS (No Auth Required)")
        print("=" * 60)
        
        endpoints = [
            ("GET /api/health", "/api/health"),
            ("GET /api/health/deep", "/api/health/deep"),
            ("GET /health", "/health")
        ]
        
        for name, path in endpoints:
            try:
                resp = self.session.get(self.url(path), timeout=10)
                success = resp.status_code == 200
                details = f"Status: {resp.status_code}, Response: {resp.text[:100]}"
                self.log_test(name, success, details)
            except Exception as e:
                self.log_test(name, False, f"Exception: {e}")
    
    def test_csrf_token_endpoint(self):
        """Test 2: CSRF Token Endpoint"""
        print("=" * 60)
        print("TEST 2: CSRF TOKEN ENDPOINT")
        print("=" * 60)
        
        try:
            resp = self.session.get(self.url("/api/auth/csrf-token"), timeout=10)
            success = resp.status_code == 200
            
            if success:
                data = resp.json()
                csrf_token = data.get('csrf_token')
                cookie_token = resp.cookies.get('csrf_token')
                
                if csrf_token and cookie_token:
                    self.csrf_token = csrf_token
                    success = True
                    details = f"Token: {csrf_token[:16]}..., Cookie: {cookie_token[:16]}..."
                else:
                    success = False
                    details = f"Missing token or cookie. Response: {data}"
            else:
                details = f"Status: {resp.status_code}, Response: {resp.text}"
                
            self.log_test("GET /api/auth/csrf-token", success, details)
            
        except Exception as e:
            self.log_test("GET /api/auth/csrf-token", False, f"Exception: {e}")
    
    def test_session_creation(self):
        """Test 3: Session Creation (exempt from CSRF)"""
        print("=" * 60)
        print("TEST 3: SESSION CREATION (CSRF Exempt)")
        print("=" * 60)
        
        try:
            resp = self.session.post(self.url("/api/auth/session"), timeout=10)
            success = resp.status_code == 200
            
            if success:
                data = resp.json()
                session_token = data.get('session_token')
                user_id = data.get('user_id')
                expires_at = data.get('expires_at')
                
                if session_token and session_token.startswith('sess_'):
                    self.session_token = session_token
                    details = f"Token: {session_token[:20]}..., User: {user_id}, Expires: {expires_at}"
                else:
                    success = False
                    details = f"Invalid session token format. Response: {data}"
            else:
                details = f"Status: {resp.status_code}, Response: {resp.text}"
                
            self.log_test("POST /api/auth/session", success, details)
            
        except Exception as e:
            self.log_test("POST /api/auth/session", False, f"Exception: {e}")
    
    def test_csrf_enforcement(self):
        """Test 4: CSRF Enforcement on State-Changing Requests"""
        print("=" * 60)
        print("TEST 4: CSRF ENFORCEMENT ON POST REQUESTS")
        print("=" * 60)
        
        journal_data = {
            "trade_type": "manual",
            "symbol": "BTC",
            "side": "buy",
            "amount_usd": 100,
            "quantity": 0.001,
            "entry_price": 50000
        }
        
        # Test 4a: POST without CSRF token (should get 403 CSRF_MISSING)
        try:
            # Clear any existing CSRF cookies/headers for this test
            temp_session = requests.Session()
            resp = temp_session.post(
                self.url("/api/journal/add"),
                json=journal_data,
                timeout=10
            )
            
            success = resp.status_code == 403
            if success:
                data = resp.json()
                csrf_error = data.get('detail', {}).get('code') == 'CSRF_MISSING'
                success = csrf_error
                details = f"Status: 403, Code: {data.get('detail', {}).get('code')}"
            else:
                details = f"Status: {resp.status_code} (expected 403), Response: {resp.text[:200]}"
                
            self.log_test("POST /api/journal/add WITHOUT CSRF", success, details)
            
        except Exception as e:
            self.log_test("POST /api/journal/add WITHOUT CSRF", False, f"Exception: {e}")
        
        # Test 4b: POST with proper CSRF token (should NOT get 403)
        if self.csrf_token:
            try:
                headers = {'X-CSRF-Token': self.csrf_token}
                resp = self.session.post(
                    self.url("/api/journal/add"),
                    json=journal_data,
                    headers=headers,
                    timeout=10
                )
                
                # Should NOT get 403 (may get 422 validation or 200, but NOT 403 CSRF error)
                success = resp.status_code != 403
                if success:
                    details = f"Status: {resp.status_code} (not 403 CSRF block)"
                else:
                    # Check if it's specifically a CSRF error
                    try:
                        data = resp.json()
                        if data.get('detail', {}).get('code') in ['CSRF_MISSING', 'CSRF_MISMATCH']:
                            details = f"CSRF error when token provided: {data}"
                        else:
                            success = True  # Different error, CSRF worked
                            details = f"Status: {resp.status_code} (CSRF passed, other validation error)"
                    except:
                        details = f"Status: {resp.status_code}, Response: {resp.text[:200]}"
                        
                self.log_test("POST /api/journal/add WITH CSRF", success, details)
                
            except Exception as e:
                self.log_test("POST /api/journal/add WITH CSRF", False, f"Exception: {e}")
        else:
            self.log_test("POST /api/journal/add WITH CSRF", False, "No CSRF token available")
    
    def test_session_validation(self):
        """Test 5: Session Validation"""
        print("=" * 60)
        print("TEST 5: SESSION VALIDATION")
        print("=" * 60)
        
        # Test 5a: Validate with session token
        if self.session_token:
            try:
                headers = {'X-Session-Token': self.session_token}
                resp = self.session.post(
                    self.url("/api/auth/session/validate"),
                    headers=headers,
                    timeout=10
                )
                
                success = resp.status_code == 200
                if success:
                    data = resp.json()
                    valid = data.get('valid')
                    success = valid == True
                    details = f"Valid: {valid}, User: {data.get('user_id')}"
                else:
                    details = f"Status: {resp.status_code}, Response: {resp.text}"
                    
                self.log_test("POST /api/auth/session/validate WITH token", success, details)
                
            except Exception as e:
                self.log_test("POST /api/auth/session/validate WITH token", False, f"Exception: {e}")
        else:
            self.log_test("POST /api/auth/session/validate WITH token", False, "No session token available")
        
        # Test 5b: Validate without session token
        try:
            resp = requests.post(self.url("/api/auth/session/validate"), timeout=10)
            
            success = resp.status_code == 200
            if success:
                data = resp.json()
                valid = data.get('valid')
                success = valid == False
                details = f"Valid: {valid} (expected False)"
            else:
                details = f"Status: {resp.status_code}, Response: {resp.text}"
                
            self.log_test("POST /api/auth/session/validate WITHOUT token", success, details)
            
        except Exception as e:
            self.log_test("POST /api/auth/session/validate WITHOUT token", False, f"Exception: {e}")
    
    def test_api_key_csrf_bypass(self):
        """Test 6: API Key CSRF Bypass"""
        print("=" * 60)
        print("TEST 6: API KEY CSRF BYPASS")
        print("=" * 60)
        
        journal_data = {
            "trade_type": "manual",
            "symbol": "BTC",
            "side": "buy",
            "amount_usd": 100,
            "quantity": 0.001,
            "entry_price": 50000
        }
        
        try:
            headers = {'X-API-Key': 'sk-test-key'}  # Fake API key
            temp_session = requests.Session()
            resp = temp_session.post(
                self.url("/api/journal/add"),
                json=journal_data,
                headers=headers,
                timeout=10
            )
            
            # Should NOT get 403 CSRF error (should get 401 invalid key instead)
            success = resp.status_code != 403
            if success:
                # Expect 401 for invalid API key, or other error, but NOT 403 CSRF
                if resp.status_code == 401:
                    details = f"Status: 401 (invalid API key, CSRF bypassed correctly)"
                else:
                    details = f"Status: {resp.status_code} (CSRF bypassed, different validation)"
            else:
                # Check if it's a CSRF error
                try:
                    data = resp.json()
                    if data.get('detail', {}).get('code') in ['CSRF_MISSING', 'CSRF_MISMATCH']:
                        details = f"CSRF not bypassed for API key: {data}"
                        success = False
                    else:
                        success = True
                        details = f"Status: {resp.status_code} (not CSRF error)"
                except:
                    details = f"Status: {resp.status_code}, Response: {resp.text[:200]}"
                    
            self.log_test("POST with X-API-Key (fake) - CSRF bypass", success, details)
            
        except Exception as e:
            self.log_test("POST with X-API-Key (fake) - CSRF bypass", False, f"Exception: {e}")
    
    def test_full_authenticated_flow(self):
        """Test 7: Full Authenticated Flow"""
        print("=" * 60)
        print("TEST 7: FULL AUTHENTICATED FLOW")
        print("=" * 60)
        
        # Step 7a: Get CSRF token
        try:
            resp = self.session.get(self.url("/api/auth/csrf-token"), timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                csrf_token = data.get('csrf_token')
                self.log_test("Step 7a: Get CSRF token", True, f"Token: {csrf_token[:16]}...")
            else:
                self.log_test("Step 7a: Get CSRF token", False, f"Status: {resp.status_code}")
                return
        except Exception as e:
            self.log_test("Step 7a: Get CSRF token", False, f"Exception: {e}")
            return
        
        # Step 7b: Create session
        try:
            resp = self.session.post(self.url("/api/auth/session"), timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                session_token = data.get('session_token')
                self.log_test("Step 7b: Create session", True, f"Token: {session_token[:20]}...")
            else:
                self.log_test("Step 7b: Create session", False, f"Status: {resp.status_code}")
                return
        except Exception as e:
            self.log_test("Step 7b: Create session", False, f"Exception: {e}")
            return
        
        # Step 7c: Full authenticated POST request
        try:
            headers = {
                'X-CSRF-Token': csrf_token,
                'X-Session-Token': session_token
            }
            journal_data = {
                "trade_type": "manual",
                "symbol": "BTC",
                "side": "buy",
                "amount_usd": 100,
                "quantity": 0.001,
                "entry_price": 50000
            }
            
            resp = self.session.post(
                self.url("/api/journal/add"),
                json=journal_data,
                headers=headers,
                timeout=10
            )
            
            # Expect 200 or 422 (validation), but NOT 403 (CSRF)
            success = resp.status_code in [200, 201, 422] or resp.status_code != 403
            if resp.status_code == 403:
                # Check if it's a CSRF error specifically
                try:
                    data = resp.json()
                    if data.get('detail', {}).get('code') in ['CSRF_MISSING', 'CSRF_MISMATCH']:
                        success = False
                        details = f"CSRF error with full auth: {data}"
                    else:
                        success = True
                        details = f"Status: {resp.status_code} (not CSRF error)"
                except:
                    details = f"Status: {resp.status_code}, Response: {resp.text[:200]}"
            else:
                details = f"Status: {resp.status_code} (authenticated request succeeded)"
                
            self.log_test("Step 7c: Full authenticated POST", success, details)
            
        except Exception as e:
            self.log_test("Step 7c: Full authenticated POST", False, f"Exception: {e}")
    
    def test_get_requests_no_csrf(self):
        """Test 8: GET Requests Still Work (no CSRF needed for GETs)"""
        print("=" * 60)
        print("TEST 8: GET REQUESTS (No CSRF Required)")
        print("=" * 60)
        
        get_endpoints = [
            ("GET /api/kraken/status", "/api/kraken/status"),
            ("GET /api/ensemble/status", "/api/ensemble/status"),
            ("GET /api/tethys/status", "/api/tethys/status"),
            ("GET /api/market/prices?coin_ids=bitcoin", "/api/market/prices?coin_ids=bitcoin")
        ]
        
        for name, path in get_endpoints:
            try:
                temp_session = requests.Session()  # Clean session without CSRF
                resp = temp_session.get(self.url(path), timeout=10)
                success = resp.status_code == 200
                details = f"Status: {resp.status_code}"
                if not success:
                    details += f", Response: {resp.text[:100]}"
                self.log_test(name, success, details)
            except Exception as e:
                self.log_test(name, False, f"Exception: {e}")
    
    def test_session_revocation(self):
        """Test 9: Session Revocation"""
        print("=" * 60)
        print("TEST 9: SESSION REVOCATION")
        print("=" * 60)
        
        if not self.session_token:
            self.log_test("Session revocation test", False, "No session token available")
            return
        
        # Test 9a: Revoke session
        try:
            headers = {'X-Session-Token': self.session_token}
            resp = self.session.post(
                self.url("/api/auth/session/revoke"),
                headers=headers,
                timeout=10
            )
            
            success = resp.status_code == 200
            if success:
                data = resp.json()
                revoked = data.get('revoked')
                success = revoked == True
                details = f"Revoked: {revoked}"
            else:
                details = f"Status: {resp.status_code}, Response: {resp.text}"
                
            self.log_test("POST /api/auth/session/revoke", success, details)
            
        except Exception as e:
            self.log_test("POST /api/auth/session/revoke", False, f"Exception: {e}")
        
        # Test 9b: Validate revoked session (should be invalid)
        try:
            headers = {'X-Session-Token': self.session_token}
            resp = self.session.post(
                self.url("/api/auth/session/validate"),
                headers=headers,
                timeout=10
            )
            
            success = resp.status_code == 200
            if success:
                data = resp.json()
                valid = data.get('valid')
                success = valid == False
                details = f"Valid: {valid} (should be False after revocation)"
            else:
                details = f"Status: {resp.status_code}, Response: {resp.text}"
                
            self.log_test("Validate revoked session", success, details)
            
        except Exception as e:
            self.log_test("Validate revoked session", False, f"Exception: {e}")
    
    def test_security_headers(self):
        """Test 10: Security Headers Still Present"""
        print("=" * 60)
        print("TEST 10: SECURITY HEADERS")
        print("=" * 60)
        
        try:
            resp = self.session.get(self.url("/api/health"), timeout=10)
            
            required_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options', 
                'Strict-Transport-Security'
            ]
            
            present_headers = []
            missing_headers = []
            
            for header in required_headers:
                if header in resp.headers:
                    present_headers.append(f"{header}: {resp.headers[header]}")
                else:
                    missing_headers.append(header)
            
            success = len(missing_headers) == 0
            if success:
                details = f"All headers present: {', '.join(present_headers)}"
            else:
                details = f"Missing: {missing_headers}, Present: {present_headers}"
                
            self.log_test("Security headers check", success, details)
            
        except Exception as e:
            self.log_test("Security headers check", False, f"Exception: {e}")
    
    def run_all_tests(self):
        """Run all CSRF and session authentication tests"""
        print("🔒 CSRF PROTECTION AND SESSION AUTHENTICATION TESTING")
        print(f"Backend URL: {self.base_url}")
        print("=" * 80)
        
        # Run all test groups
        self.test_health_endpoints()
        self.test_csrf_token_endpoint()
        self.test_session_creation()
        self.test_csrf_enforcement()
        self.test_session_validation()
        self.test_api_key_csrf_bypass()
        self.test_full_authenticated_flow()
        self.test_get_requests_no_csrf()
        self.test_session_revocation()
        self.test_security_headers()
        
        print("=" * 80)
        print("🔒 CSRF AND SESSION AUTHENTICATION TESTING COMPLETED")
        print("=" * 80)


def main():
    """Main testing function"""
    # Use the production backend URL from frontend .env
    backend_url = "https://kraken-security-scan.preview.emergentagent.com"
    
    print(f"Testing CSRF Protection and Session Authentication at: {backend_url}")
    print()
    
    tester = CSRFSessionTester(backend_url)
    tester.run_all_tests()


if __name__ == "__main__":
    main()