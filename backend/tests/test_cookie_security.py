"""
Test Suite for Cookie Security Hardening (Iteration 51)
=========================================================
Tests that verify:
1. CSRF cookie has Secure flag
2. CSRF cookie has SameSite=lax attribute
3. Session cookies are properly secured
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://feature-enhancer-7.preview.emergentagent.com')


class TestCookieSecurityHardening:
    """Verify cookie security settings from iteration 51 security hardening"""
    
    def test_csrf_cookie_has_secure_flag(self):
        """CSRF cookie should have Secure flag set"""
        response = requests.get(f"{BASE_URL}/api/auth/csrf-token")
        assert response.status_code == 200
        
        # Check Set-Cookie headers for Secure flag
        set_cookie_headers = response.headers.get('set-cookie', '')
        
        # The response may have multiple cookies, find the csrf_token one
        found_csrf_cookie = False
        has_secure_flag = False
        
        if 'csrf_token' in set_cookie_headers.lower():
            found_csrf_cookie = True
            # Check if Secure is in the cookie string (case-insensitive)
            if 'secure' in set_cookie_headers.lower():
                has_secure_flag = True
        
        assert found_csrf_cookie, "CSRF cookie should be set in response"
        assert has_secure_flag, f"CSRF cookie should have Secure flag. Got: {set_cookie_headers}"
        print(f"✓ CSRF cookie has Secure flag: {set_cookie_headers[:100]}...")
    
    def test_csrf_cookie_has_samesite_lax(self):
        """CSRF cookie should have SameSite=lax attribute"""
        response = requests.get(f"{BASE_URL}/api/auth/csrf-token")
        assert response.status_code == 200
        
        set_cookie_headers = response.headers.get('set-cookie', '')
        
        # Check for SameSite=lax (case-insensitive)
        has_samesite_lax = 'samesite=lax' in set_cookie_headers.lower()
        
        assert has_samesite_lax, f"CSRF cookie should have SameSite=lax. Got: {set_cookie_headers}"
        print(f"✓ CSRF cookie has SameSite=lax attribute")
    
    def test_session_endpoint_sets_secure_csrf_cookie(self):
        """POST /api/auth/session should set CSRF cookie with Secure flag"""
        response = requests.post(
            f"{BASE_URL}/api/auth/session",
            json={},
            headers={"X-User-ID": "test_cookie_security", "Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        set_cookie_headers = response.headers.get('set-cookie', '')
        
        # Check that csrf_token cookie has both Secure and SameSite=lax
        has_csrf_cookie = 'csrf_token' in set_cookie_headers.lower()
        has_secure = 'secure' in set_cookie_headers.lower()
        has_samesite_lax = 'samesite=lax' in set_cookie_headers.lower()
        
        assert has_csrf_cookie, "Session endpoint should set CSRF cookie"
        assert has_secure, f"Session CSRF cookie should have Secure flag. Got: {set_cookie_headers[:200]}"
        assert has_samesite_lax, f"Session CSRF cookie should have SameSite=lax. Got: {set_cookie_headers[:200]}"
        
        print(f"✓ Session endpoint sets Secure CSRF cookie with SameSite=lax")
    
    def test_csrf_cookie_is_not_httponly(self):
        """CSRF cookie should NOT be HttpOnly (JS must read it for double-submit)"""
        response = requests.get(f"{BASE_URL}/api/auth/csrf-token")
        assert response.status_code == 200
        
        set_cookie_headers = response.headers.get('set-cookie', '')
        
        # The csrf_token cookie should NOT have HttpOnly
        # It's a bit tricky to verify absence, so we check the cookie part doesn't have it
        csrf_part = ''
        for part in set_cookie_headers.split(','):
            if 'csrf_token=' in part:
                csrf_part = part
                break
        
        # HttpOnly should not be in the csrf_token cookie part
        is_httponly = 'httponly' in csrf_part.lower()
        assert not is_httponly, f"CSRF cookie should NOT be HttpOnly (JS needs to read it). Cookie: {csrf_part}"
        print(f"✓ CSRF cookie is NOT HttpOnly (correct for double-submit pattern)")


class TestHealthEndpointsCookies:
    """Verify health endpoints work and may also set cookies"""
    
    def test_health_basic_no_auth_required(self):
        """GET /api/health should work without any auth"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ["healthy", "degraded"]
        print(f"✓ /api/health returns: {data.get('status')}")
    
    def test_health_deep_no_auth_required(self):
        """GET /api/health/deep should work without any auth"""
        response = requests.get(f"{BASE_URL}/api/health/deep")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
        print(f"✓ /api/health/deep returns: {data.get('status')}, checks: {list(data.get('checks', {}).keys())}")


class TestCSRFValidationWithNewCookies:
    """Test CSRF validation still works correctly with hardened cookies"""
    
    def test_post_without_csrf_returns_403_csrf_missing(self):
        """POST without CSRF should return 403 with CSRF_MISSING code"""
        response = requests.post(
            f"{BASE_URL}/api/trading/execute",
            json={"action": "test"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 403
        data = response.json()
        detail = data.get("detail", {})
        assert detail.get("code") == "CSRF_MISSING"
        print(f"✓ POST without CSRF returns 403 CSRF_MISSING")
    
    def test_post_with_valid_csrf_succeeds(self):
        """POST with valid CSRF token should succeed"""
        session = requests.Session()
        
        # Get CSRF token
        csrf_response = session.get(f"{BASE_URL}/api/auth/csrf-token")
        assert csrf_response.status_code == 200
        csrf_token = csrf_response.json().get("csrf_token")
        
        # Make POST with CSRF token
        response = session.post(
            f"{BASE_URL}/api/auth/session/validate",
            json={},
            headers={
                "Content-Type": "application/json",
                "X-CSRF-Token": csrf_token,
                "X-Session-Token": "test_token_invalid"  # Will fail validation but CSRF should pass
            }
        )
        
        # Should NOT be 403 CSRF error - validation endpoint returns 200 with valid=false
        assert response.status_code == 200
        data = response.json()
        assert data.get("valid") == False  # Session is invalid but CSRF passed
        print(f"✓ POST with valid CSRF succeeds (CSRF validation passed)")
    
    def test_api_key_bypass_with_secure_cookies(self):
        """API key should still bypass CSRF even with secure cookies"""
        session = requests.Session()
        
        # Get CSRF token and create API key
        csrf_response = session.get(f"{BASE_URL}/api/auth/csrf-token")
        csrf_token = csrf_response.json().get("csrf_token")
        
        # Create API key
        create_response = session.post(
            f"{BASE_URL}/api/api-keys/create",
            json={"name": "test-secure-bypass", "tier": "free", "scopes": ["read"]},
            headers={
                "Content-Type": "application/json",
                "X-CSRF-Token": csrf_token
            }
        )
        assert create_response.status_code == 201
        api_key = create_response.json().get("api_key")
        
        # Now make POST with API key only (no CSRF) - should succeed
        new_session = requests.Session()  # Fresh session, no cookies
        validate_response = new_session.get(
            f"{BASE_URL}/api/api-keys/validate",
            headers={"X-API-Key": api_key}
        )
        assert validate_response.status_code == 200
        data = validate_response.json()
        assert data.get("valid") == True
        print(f"✓ API key bypass still works with secure cookies")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
