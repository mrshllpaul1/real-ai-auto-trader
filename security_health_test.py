#!/usr/bin/env python3
"""
Comprehensive Backend Health and Safety Testing
After Security Hardening - AI Crypto Trading Platform

This script tests:
1. Core Health Endpoints (including new /api/health/deep)
2. Security Headers Verification
3. NoSQL Injection Prevention 
4. Safe Error Handling
5. Critical API Regression Testing
6. Audit Logging
7. Rate Limiting Headers
"""

import asyncio
import httpx
import json
import time
import os
from typing import Dict, List, Tuple, Any
from pathlib import Path

# Backend URL from environment
BACKEND_URL = "https://csrf-api-guard.preview.emergentagent.com"

class SecurityTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
        self.results = []
        
    async def log_result(self, test_name: str, success: bool, details: str, response_time: float = 0):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {test_name} | {details} | {response_time:.3f}s")
        self.results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'response_time': response_time
        })

    async def test_core_health_endpoints(self):
        """Test core health endpoints"""
        print("\n" + "="*60)
        print("1. TESTING CORE HEALTH ENDPOINTS")
        print("="*60)
        
        # Test basic health endpoint
        start = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/api/health")
            response_time = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                has_status = "status" in data
                has_services = "services" in data
                await self.log_result(
                    "GET /api/health", 
                    has_status, 
                    f"Status: {response.status_code}, Has status: {has_status}, Has services: {has_services}",
                    response_time
                )
            else:
                await self.log_result("GET /api/health", False, f"Status: {response.status_code}", response_time)
        except Exception as e:
            await self.log_result("GET /api/health", False, f"Exception: {str(e)}")
        
        # Test new deep health endpoint
        start = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/api/health/deep")
            response_time = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                has_checks = "checks" in data
                has_database = "database" in data.get("checks", {})
                has_kraken = "kraken_public_api" in data.get("checks", {})
                has_encryption = "encryption" in data.get("checks", {})
                has_security = "security" in data.get("checks", {})
                has_environment = "environment" in data.get("checks", {})
                
                all_components = has_database and has_kraken and has_encryption and has_security and has_environment
                
                await self.log_result(
                    "GET /api/health/deep", 
                    all_components, 
                    f"Status: {response.status_code}, Components: DB={has_database}, Kraken={has_kraken}, Encrypt={has_encryption}, Security={has_security}, Env={has_environment}",
                    response_time
                )
            else:
                await self.log_result("GET /api/health/deep", False, f"Status: {response.status_code}", response_time)
        except Exception as e:
            await self.log_result("GET /api/health/deep", False, f"Exception: {str(e)}")
        
        # Test root endpoint
        start = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/api/")
            response_time = time.time() - start
            
            success = response.status_code == 200
            await self.log_result(
                "GET /api/ (root)", 
                success, 
                f"Status: {response.status_code}",
                response_time
            )
        except Exception as e:
            await self.log_result("GET /api/ (root)", False, f"Exception: {str(e)}")

    async def test_security_headers(self):
        """Test security headers on API responses"""
        print("\n" + "="*60)
        print("2. TESTING SECURITY HEADERS")
        print("="*60)
        
        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "Permissions-Policy"
        ]
        
        start = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/api/health")
            response_time = time.time() - start
            
            missing_headers = []
            present_headers = {}
            
            for header in required_headers:
                if header in response.headers:
                    present_headers[header] = response.headers[header]
                else:
                    missing_headers.append(header)
            
            success = len(missing_headers) == 0
            details = f"Present: {len(present_headers)}/{len(required_headers)}"
            if missing_headers:
                details += f", Missing: {missing_headers}"
            
            await self.log_result(
                "Security Headers Check", 
                success, 
                details,
                response_time
            )
            
            # Log individual headers
            for header, value in present_headers.items():
                await self.log_result(
                    f"Header: {header}",
                    True,
                    f"Value: {value}"
                )
            
        except Exception as e:
            await self.log_result("Security Headers Check", False, f"Exception: {str(e)}")

    async def test_nosql_injection_prevention(self):
        """Test NoSQL injection prevention"""
        print("\n" + "="*60)
        print("3. TESTING NOSQL INJECTION PREVENTION")
        print("="*60)
        
        injection_tests = [
            ("$gt", "/api/market/prices?coin_ids=$gt"),
            ("$where", "/api/market/prices?coin_ids=$where"),
            ("$regex", "/api/market/prices?coin_ids=$regex"),
            ("normal", "/api/market/prices?coin_ids=bitcoin")
        ]
        
        for test_name, url in injection_tests:
            start = time.time()
            try:
                response = await self.client.get(f"{self.base_url}{url}")
                response_time = time.time() - start
                
                if "injection" in test_name or test_name in ["$gt", "$where", "$regex"]:
                    # Should be blocked (400 Bad Request)
                    expected_blocked = response.status_code == 400
                    await self.log_result(
                        f"NoSQL Injection Block ({test_name})",
                        expected_blocked,
                        f"Status: {response.status_code} (Expected: 400 for blocked injection)",
                        response_time
                    )
                else:
                    # Normal request should work or return expected error (not 400 injection block)
                    success = response.status_code != 400 or "Invalid request parameters" not in str(response.text)
                    await self.log_result(
                        f"Normal Request ({test_name})",
                        success,
                        f"Status: {response.status_code}",
                        response_time
                    )
            except Exception as e:
                await self.log_result(f"NoSQL Injection Test ({test_name})", False, f"Exception: {str(e)}")

    async def test_safe_error_handling(self):
        """Test that internal errors don't leak sensitive information"""
        print("\n" + "="*60)
        print("4. TESTING SAFE ERROR HANDLING")
        print("="*60)
        
        # Test endpoints that might produce errors
        error_test_endpoints = [
            "/api/nonexistent/endpoint",
            "/api/market/prices/invalid",
            "/api/ensemble/invalid-operation"
        ]
        
        for endpoint in error_test_endpoints:
            start = time.time()
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}")
                response_time = time.time() - start
                
                # Check that error responses don't contain sensitive information
                response_text = response.text.lower()
                has_traceback = "traceback" in response_text
                has_file_path = "/app/" in response_text or "backend/" in response_text
                has_internal_error = "internal error occurred" in response_text
                
                # Good: Should have safe error message, no tracebacks/paths
                safe_error = not has_traceback and not has_file_path
                
                await self.log_result(
                    f"Safe Error Handling {endpoint}",
                    safe_error,
                    f"Status: {response.status_code}, Safe: {safe_error}, Traceback: {has_traceback}, Paths: {has_file_path}",
                    response_time
                )
                
            except Exception as e:
                await self.log_result(f"Safe Error Handling {endpoint}", False, f"Exception: {str(e)}")

    async def test_critical_api_regression(self):
        """Test critical API endpoints to ensure they still work after security hardening"""
        print("\n" + "="*60)
        print("5. TESTING CRITICAL API REGRESSION")
        print("="*60)
        
        critical_endpoints = [
            "/api/kraken/status",
            "/api/ensemble/status", 
            "/api/tethys/status",
            "/api/auto-trading/status",
            "/api/sentiment/market",
            "/api/market/prices?coin_ids=bitcoin,ethereum",
            "/api/kraken-exec/status",
            "/api/triggers/list"
        ]
        
        for endpoint in critical_endpoints:
            start = time.time()
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}")
                response_time = time.time() - start
                
                success = response.status_code == 200
                await self.log_result(
                    f"Critical API {endpoint}",
                    success,
                    f"Status: {response.status_code}",
                    response_time
                )
                
            except Exception as e:
                await self.log_result(f"Critical API {endpoint}", False, f"Exception: {str(e)}")
        
        # Test POST endpoint (journal add)
        start = time.time()
        try:
            payload = {
                "coin_id": "bitcoin",
                "action": "buy", 
                "amount": 0.1,
                "price": 50000
            }
            response = await self.client.post(
                f"{self.base_url}/api/journal/add",
                json=payload
            )
            response_time = time.time() - start
            
            success = response.status_code in [200, 201]
            await self.log_result(
                "Critical API POST /api/journal/add",
                success,
                f"Status: {response.status_code}",
                response_time
            )
            
        except Exception as e:
            await self.log_result("Critical API POST /api/journal/add", False, f"Exception: {str(e)}")

    async def test_audit_logging(self):
        """Test that audit logging is working"""
        print("\n" + "="*60)
        print("6. TESTING AUDIT LOGGING")
        print("="*60)
        
        # Check if audit log file exists and is writable
        audit_log_path = "/var/log/supervisor/audit.log"
        
        try:
            # Check if file exists
            if os.path.exists(audit_log_path):
                # Check if we can write to it (indirectly by checking directory permissions)
                log_dir = os.path.dirname(audit_log_path)
                writable = os.access(log_dir, os.W_OK)
                await self.log_result(
                    "Audit Log File Accessible",
                    True,
                    f"File exists: True, Directory writable: {writable}"
                )
            else:
                await self.log_result(
                    "Audit Log File Accessible",
                    False,
                    "Audit log file does not exist"
                )
        except Exception as e:
            await self.log_result("Audit Log File Accessible", False, f"Exception: {str(e)}")
        
        # Test that audit headers are present in responses to sensitive operations
        start = time.time()
        try:
            payload = {"coin_id": "bitcoin", "action": "test", "amount": 0.01, "price": 50000}
            response = await self.client.post(
                f"{self.base_url}/api/journal/add",
                json=payload
            )
            response_time = time.time() - start
            
            has_audit_id = "X-Audit-ID" in response.headers
            await self.log_result(
                "Audit ID Header Present",
                has_audit_id,
                f"Status: {response.status_code}, X-Audit-ID present: {has_audit_id}",
                response_time
            )
            
        except Exception as e:
            await self.log_result("Audit ID Header Present", False, f"Exception: {str(e)}")

    async def test_rate_limiting_headers(self):
        """Test that rate limiting headers are present"""
        print("\n" + "="*60)
        print("7. TESTING RATE LIMITING HEADERS")
        print("="*60)
        
        expected_rate_headers = [
            "X-RateLimit-Remaining-Minute",
            "X-RateLimit-Remaining-Hour"
        ]
        
        start = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/api/health")
            response_time = time.time() - start
            
            present_headers = {}
            for header in expected_rate_headers:
                if header in response.headers:
                    present_headers[header] = response.headers[header]
            
            has_rate_headers = len(present_headers) > 0
            await self.log_result(
                "Rate Limiting Headers",
                has_rate_headers,
                f"Present headers: {list(present_headers.keys())}",
                response_time
            )
            
            # Log individual rate limit values
            for header, value in present_headers.items():
                await self.log_result(
                    f"Rate Limit {header}",
                    True,
                    f"Value: {value}"
                )
                
        except Exception as e:
            await self.log_result("Rate Limiting Headers", False, f"Exception: {str(e)}")

    async def run_all_tests(self):
        """Run all security and health tests"""
        print("🔒 COMPREHENSIVE BACKEND HEALTH AND SAFETY TESTING")
        print(f"🎯 Target: {self.base_url}")
        print(f"⏰ Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all test categories
        await self.test_core_health_endpoints()
        await self.test_security_headers()
        await self.test_nosql_injection_prevention()
        await self.test_safe_error_handling()
        await self.test_critical_api_regression()
        await self.test_audit_logging()
        await self.test_rate_limiting_headers()
        
        # Generate summary
        await self.generate_summary()
        
    async def generate_summary(self):
        """Generate test summary"""
        print("\n" + "="*60)
        print("🎯 SECURITY & HEALTH TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n⏰ Completed: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Close client
        await self.client.aclose()

async def main():
    """Main test execution"""
    tester = SecurityTester(BACKEND_URL)
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())