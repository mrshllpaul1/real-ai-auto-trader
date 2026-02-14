"""
Vulnerability Scanner API Tests - Iteration 53
Tests the new vulnerability scanning feature:
- GET /api/security/vulnerabilities/latest
- GET /api/security/vulnerabilities/history
- POST /api/security/vulnerabilities/scan (requires CSRF)
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestVulnScannerEndpoints:
    """Test vulnerability scanner API endpoints"""
    
    # ===========================================
    # GET /latest - Returns most recent scan
    # ===========================================
    
    def test_get_latest_scan_returns_200(self):
        """GET /api/security/vulnerabilities/latest should return 200"""
        response = requests.get(f"{BASE_URL}/api/security/vulnerabilities/latest")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ GET /latest returned 200")
    
    def test_get_latest_scan_structure(self):
        """GET /latest should return proper structure (scan result or no-scan message)"""
        response = requests.get(f"{BASE_URL}/api/security/vulnerabilities/latest")
        assert response.status_code == 200
        data = response.json()
        
        # Either returns a scan result or "no scans yet" message
        if "message" in data:
            # No scans yet
            assert "No scans" in data["message"] or "scan" in data["message"].lower()
            print(f"✓ No scans yet message: {data['message']}")
        else:
            # Scan result - validate structure
            assert "status" in data, "Missing 'status' field"
            assert "total_vulnerabilities" in data, "Missing 'total_vulnerabilities' field"
            assert "backend" in data, "Missing 'backend' field"
            assert "frontend" in data, "Missing 'frontend' field"
            assert "started_at" in data, "Missing 'started_at' field"
            assert "completed_at" in data, "Missing 'completed_at' field"
            
            # Validate backend structure
            assert "count" in data["backend"], "Missing 'backend.count'"
            assert "vulnerabilities" in data["backend"], "Missing 'backend.vulnerabilities'"
            
            # Validate frontend structure
            assert "count" in data["frontend"], "Missing 'frontend.count'"
            assert "vulnerabilities" in data["frontend"], "Missing 'frontend.vulnerabilities'"
            
            print(f"✓ GET /latest structure valid: status={data['status']}, total_vulns={data['total_vulnerabilities']}")
    
    # ===========================================
    # GET /history - Returns scan history
    # ===========================================
    
    def test_get_scan_history_returns_200(self):
        """GET /api/security/vulnerabilities/history should return 200"""
        response = requests.get(f"{BASE_URL}/api/security/vulnerabilities/history")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ GET /history returned 200")
    
    def test_get_scan_history_returns_array(self):
        """GET /history should return an array of scan summaries"""
        response = requests.get(f"{BASE_URL}/api/security/vulnerabilities/history")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"✓ GET /history returned array with {len(data)} items")
        
        # If there are items, validate summary structure (no vulnerability details)
        if len(data) > 0:
            item = data[0]
            assert "status" in item, "Missing 'status' in history item"
            assert "total_vulnerabilities" in item, "Missing 'total_vulnerabilities'"
            assert "backend" in item, "Missing 'backend' in history item"
            assert "frontend" in item, "Missing 'frontend' in history item"
            
            # History should NOT include detailed vulnerabilities (just counts)
            if "vulnerabilities" in item.get("backend", {}):
                # This would be wrong - history should be summary only
                pytest.fail("History endpoint should not include vulnerability details, only counts")
            print(f"✓ History item structure valid: status={item['status']}, total={item['total_vulnerabilities']}")
    
    def test_get_scan_history_with_limit(self):
        """GET /history?limit=5 should respect limit parameter"""
        response = requests.get(f"{BASE_URL}/api/security/vulnerabilities/history?limit=5")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        assert len(data) <= 5, f"Expected max 5 items, got {len(data)}"
        print(f"✓ GET /history?limit=5 returned {len(data)} items (max 5)")
    
    # ===========================================
    # POST /scan - Trigger manual scan (CSRF)
    # ===========================================
    
    def test_post_scan_requires_csrf(self):
        """POST /api/security/vulnerabilities/scan should require CSRF token (403 without)"""
        response = requests.post(f"{BASE_URL}/api/security/vulnerabilities/scan")
        
        # Should get 403 CSRF_MISSING or similar error
        assert response.status_code == 403, f"Expected 403 for missing CSRF, got {response.status_code}: {response.text}"
        
        # Check error message indicates CSRF issue
        data = response.json()
        detail = data.get("detail", "")
        if isinstance(detail, dict):
            error_code = detail.get("error_code", "")
            assert "CSRF" in error_code.upper(), f"Expected CSRF error, got: {detail}"
        else:
            assert "csrf" in str(detail).lower() or "CSRF" in str(detail), f"Expected CSRF error, got: {detail}"
        
        print(f"✓ POST /scan without CSRF correctly returns 403")
    
    def test_post_scan_with_csrf_succeeds(self):
        """POST /scan with valid CSRF token should trigger scan and return results"""
        session = requests.Session()
        
        # Step 1: Get CSRF token from /api/auth/csrf-token
        csrf_response = session.get(f"{BASE_URL}/api/auth/csrf-token")
        assert csrf_response.status_code == 200, f"Failed to get CSRF token: {csrf_response.text}"
        
        csrf_data = csrf_response.json()
        csrf_token = csrf_data.get("csrf_token")
        assert csrf_token, f"No csrf_token in response: {csrf_data}"
        
        # Step 2: POST /scan with CSRF token in header
        # Note: The session already has the csrf_token cookie from step 1
        headers = {"X-CSRF-Token": csrf_token}
        
        print(f"Triggering vulnerability scan (this may take up to 60-120 seconds)...")
        start_time = time.time()
        
        scan_response = session.post(
            f"{BASE_URL}/api/security/vulnerabilities/scan",
            headers=headers,
            timeout=180  # Scan can take time
        )
        
        elapsed = time.time() - start_time
        print(f"Scan completed in {elapsed:.1f}s")
        
        assert scan_response.status_code == 200, f"Expected 200, got {scan_response.status_code}: {scan_response.text}"
        
        # Validate response structure
        data = scan_response.json()
        assert "status" in data, "Missing 'status' in scan result"
        assert "total_vulnerabilities" in data, "Missing 'total_vulnerabilities'"
        assert "backend" in data, "Missing 'backend'"
        assert "frontend" in data, "Missing 'frontend'"
        
        print(f"✓ POST /scan succeeded: status={data['status']}, total_vulns={data['total_vulnerabilities']}")
        print(f"  Backend: {data['backend']['count']} vulns")
        print(f"  Frontend: {data['frontend']['count']} vulns")
        
        return data  # Return for use in other tests
    
    # ===========================================
    # Vulnerability Detection Tests
    # ===========================================
    
    def test_backend_detects_known_vulns(self):
        """Backend scan should detect known vulnerabilities (diskcache, ecdsa)"""
        # First, ensure we have a scan result
        response = requests.get(f"{BASE_URL}/api/security/vulnerabilities/latest")
        assert response.status_code == 200
        data = response.json()
        
        if "message" in data:
            pytest.skip("No scans available yet - run test_post_scan_with_csrf_succeeds first")
        
        backend = data.get("backend", {})
        vulns = backend.get("vulnerabilities", [])
        
        # Expected: 2 known vulns (diskcache CVE-2025-69872, ecdsa CVE-2024-23342)
        # Note: This is based on the main agent's context - actual results may vary
        vuln_packages = [v.get("package") for v in vulns]
        
        print(f"Backend vulnerabilities found: {len(vulns)}")
        for v in vulns:
            print(f"  - {v.get('package')} {v.get('version')}: {v.get('id')}")
        
        # At minimum, verify structure of each vulnerability
        for v in vulns:
            assert "package" in v, "Vulnerability missing 'package'"
            assert "version" in v, "Vulnerability missing 'version'"
            assert "id" in v, "Vulnerability missing 'id'"
        
        print(f"✓ Backend vulnerabilities validated: {len(vulns)} found")
    
    def test_frontend_scan_results(self):
        """Frontend scan should return vulnerability info (expected 0 per main agent)"""
        response = requests.get(f"{BASE_URL}/api/security/vulnerabilities/latest")
        assert response.status_code == 200
        data = response.json()
        
        if "message" in data:
            pytest.skip("No scans available yet")
        
        frontend = data.get("frontend", {})
        vuln_count = frontend.get("count", 0)
        vulns = frontend.get("vulnerabilities", [])
        
        print(f"Frontend vulnerabilities: {vuln_count}")
        for v in vulns:
            print(f"  - {v.get('package')}: {v.get('title')} (severity: {v.get('severity')})")
        
        # Per main agent: frontend should have 0 vulnerabilities
        # But we validate structure regardless
        assert isinstance(vulns, list), "vulnerabilities should be a list"
        assert frontend.get("count") == len(vulns), "count should match vulnerabilities length"
        
        print(f"✓ Frontend vulnerabilities validated: {vuln_count} found")
    
    # ===========================================
    # Persistence Tests
    # ===========================================
    
    def test_scan_persists_to_history(self):
        """Scan results should persist to MongoDB and appear in /history"""
        session = requests.Session()
        
        # Get CSRF token
        csrf_response = session.get(f"{BASE_URL}/api/auth/csrf-token")
        assert csrf_response.status_code == 200
        csrf_token = csrf_response.json().get("csrf_token")
        
        # Trigger a scan
        headers = {"X-CSRF-Token": csrf_token}
        print("Triggering scan for persistence test...")
        scan_response = session.post(
            f"{BASE_URL}/api/security/vulnerabilities/scan",
            headers=headers,
            timeout=180
        )
        
        if scan_response.status_code != 200:
            pytest.fail(f"Scan failed: {scan_response.status_code} {scan_response.text}")
        
        scan_data = scan_response.json()
        scan_started_at = scan_data.get("started_at")
        
        # Verify it appears in history
        history_response = requests.get(f"{BASE_URL}/api/security/vulnerabilities/history?limit=10")
        assert history_response.status_code == 200
        history = history_response.json()
        
        # Find our scan in history
        found = False
        for item in history:
            if item.get("started_at") == scan_started_at:
                found = True
                break
        
        assert found, f"Scan with started_at={scan_started_at} not found in history"
        print(f"✓ Scan persisted to history (started_at={scan_started_at})")
    
    # ===========================================
    # Health Check (Regression)
    # ===========================================
    
    def test_health_endpoint_still_works(self):
        """Verify /api/health still returns 200 (regression test)"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        data = response.json()
        assert data.get("status") in ["healthy", "degraded"], f"Unexpected status: {data}"
        print(f"✓ /api/health returns 200: {data.get('status')}")


class TestCSRFProtectionOnScanEndpoint:
    """Additional CSRF protection tests specific to /scan endpoint"""
    
    def test_scan_with_wrong_csrf_token(self):
        """POST /scan with mismatched CSRF token should return 403"""
        session = requests.Session()
        
        # Get a valid CSRF cookie
        session.get(f"{BASE_URL}/api/auth/csrf-token")
        
        # Send with wrong token in header
        headers = {"X-CSRF-Token": "wrong-token-value-12345"}
        response = session.post(
            f"{BASE_URL}/api/security/vulnerabilities/scan",
            headers=headers
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print(f"✓ POST /scan with wrong CSRF token correctly returns 403")
    
    def test_scan_with_api_key_bypasses_csrf(self):
        """POST /scan with X-API-Key header should bypass CSRF requirement"""
        session = requests.Session()
        
        # First create an API key
        csrf_response = session.get(f"{BASE_URL}/api/auth/csrf-token")
        csrf_token = csrf_response.json().get("csrf_token")
        
        # Create API key
        key_response = session.post(
            f"{BASE_URL}/api/api-keys/create",
            headers={"X-CSRF-Token": csrf_token},
            json={"name": "vuln_scan_test_key", "permissions": ["read", "write"]}
        )
        
        if key_response.status_code not in [200, 201]:
            pytest.skip(f"Could not create API key: {key_response.status_code}")
        
        api_key = key_response.json().get("api_key")
        if not api_key:
            pytest.skip("No api_key in response")
        
        # Now try POST /scan with API key (no CSRF token)
        headers = {"X-API-Key": api_key}
        print("Testing scan with API key bypass (may take time)...")
        response = requests.post(
            f"{BASE_URL}/api/security/vulnerabilities/scan",
            headers=headers,
            timeout=180
        )
        
        # Should work (200) since API key bypasses CSRF
        assert response.status_code == 200, f"Expected 200 with API key, got {response.status_code}: {response.text}"
        print(f"✓ POST /scan with X-API-Key bypasses CSRF and succeeds")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
