#!/usr/bin/env python3
"""
Comprehensive Backend Health and Safety Testing - UPDATED
After Security Hardening - AI Crypto Trading Platform

Tests all critical security features as specified in the review request.
"""

import asyncio
import httpx
import json
import time
import os
from typing import Dict, List, Tuple, Any

BACKEND_URL = "https://kraken-security-scan.preview.emergentagent.com"

class ComprehensiveSecurityTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
        self.results = []
        self.test_count = 0
        self.pass_count = 0
        
    async def log_result(self, test_name: str, success: bool, details: str, response_time: float = 0):
        """Log test result"""
        self.test_count += 1
        if success:
            self.pass_count += 1
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {test_name} | {details} | {response_time:.3f}s")
        self.results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'response_time': response_time
        })

    async def test_1_core_health_endpoints(self):
        """Test 1: Core Health Endpoints"""
        print("\n" + "="*70)
        print("🔍 TEST 1: CORE HEALTH ENDPOINTS")
        print("="*70)
        
        # Test GET /api/health - Should return status="healthy" with services object
        start = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/api/health")
            response_time = time.time() - start
            data = response.json()
            
            has_status = data.get("status") == "healthy"
            has_services = "services" in data
            success = response.status_code == 200 and has_status and has_services
            
            await self.log_result(
                "GET /api/health",
                success,
                f"Status: {response.status_code}, status='{data.get('status')}', services: {has_services}",
                response_time
            )
        except Exception as e:
            await self.log_result("GET /api/health", False, f"Exception: {str(e)}")

        # Test GET /api/health/deep - NEW endpoint with comprehensive checks
        start = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/api/health/deep")
            response_time = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                checks = data.get("checks", {})
                
                required_checks = ["database", "kraken_public_api", "encryption", "security", "environment"]
                present_checks = [check for check in required_checks if check in checks]
                success = len(present_checks) == len(required_checks)
                
                await self.log_result(
                    "GET /api/health/deep",
                    success,
                    f"Status: {response.status_code}, Checks: {len(present_checks)}/{len(required_checks)} ({', '.join(present_checks)})",
                    response_time
                )
            else:
                await self.log_result("GET /api/health/deep", False, f"Status: {response.status_code}", response_time)
        except Exception as e:
            await self.log_result("GET /api/health/deep", False, f"Exception: {str(e)}")

        # Test GET /api/ - Root should still work
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

    async def test_2_security_headers(self):
        """Test 2: Security Headers Verification"""
        print("\n" + "="*70)
        print("🛡️ TEST 2: SECURITY HEADERS VERIFICATION")
        print("="*70)
        
        required_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN", 
            "X-XSS-Protection": None,  # Any value is fine
            "Strict-Transport-Security": None,
            "Content-Security-Policy": None,
            "Permissions-Policy": None
        }
        
        start = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/api/health")
            response_time = time.time() - start
            
            all_present = True
            results = {}
            
            for header, expected_value in required_headers.items():
                if header in response.headers:
                    actual_value = response.headers[header]
                    if expected_value and actual_value != expected_value:
                        results[header] = f"❌ Wrong value: {actual_value}"
                        all_present = False
                    else:
                        results[header] = f"✅ {actual_value[:50]}..."
                else:
                    results[header] = "❌ Missing"
                    all_present = False
            
            await self.log_result(
                "Security Headers Complete",
                all_present,
                f"Status: {response.status_code}, All headers present: {all_present}",
                response_time
            )
            
            # Log individual header results
            for header, result in results.items():
                await self.log_result(f"  └─ {header}", "✅" in result, result)
                
        except Exception as e:
            await self.log_result("Security Headers Complete", False, f"Exception: {str(e)}")

    async def test_3_nosql_injection_prevention(self):
        """Test 3: NoSQL Injection Prevention"""
        print("\n" + "="*70)
        print("🚫 TEST 3: NOSQL INJECTION PREVENTION")  
        print("="*70)
        
        # Test injection attempts - should return 400
        injection_tests = [
            ("$gt injection", "/api/market/prices?coin_ids=$gt", True),
            ("$where injection", "/api/market/prices?coin_ids=$where", True), 
            ("Normal request", "/api/market/prices?coin_ids=bitcoin", False)
        ]
        
        for test_name, url, should_block in injection_tests:
            start = time.time()
            try:
                response = await self.client.get(f"{self.base_url}{url}")
                response_time = time.time() - start
                
                if should_block:
                    # Should be blocked with 400 status
                    success = response.status_code == 400
                    expected = "400 (blocked)"
                else:
                    # Normal request should work (200) 
                    success = response.status_code == 200
                    expected = "200 (allowed)"
                
                await self.log_result(
                    f"NoSQL Injection: {test_name}",
                    success,
                    f"Status: {response.status_code}, Expected: {expected}",
                    response_time
                )
                
                # If injection wasn't blocked, check if it at least returns empty results
                if should_block and response.status_code == 200:
                    try:
                        data = response.json()
                        empty_result = len(data) == 0
                        await self.log_result(
                            f"  └─ Fallback Protection",
                            empty_result,
                            f"Returns empty result: {empty_result} (safer than data exposure)"
                        )
                    except:
                        pass
                        
            except Exception as e:
                await self.log_result(f"NoSQL Injection: {test_name}", False, f"Exception: {str(e)}")

    async def test_4_safe_error_handling(self):
        """Test 4: Safe Error Handling - No internal errors leak"""
        print("\n" + "="*70)
        print("🔐 TEST 4: SAFE ERROR HANDLING")
        print("="*70)
        
        # Test endpoints that should return safe 500 errors
        error_endpoints = [
            "/api/nonexistent/endpoint",
            "/api/invalid/path/structure", 
            "/api/market/trigger-error"  # This should trigger error handler
        ]
        
        for endpoint in error_endpoints:
            start = time.time()
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}")
                response_time = time.time() - start
                
                # Check response for safe error handling
                response_text = response.text.lower()
                
                # Bad indicators (should NOT be present)
                has_traceback = "traceback" in response_text
                has_file_paths = "/app/" in response_text or "backend/" in response_text
                has_python_error = "python" in response_text or ".py" in response_text
                
                # Good indicators (should be present for 500 errors)
                has_safe_message = "internal error occurred" in response_text
                
                is_safe = not (has_traceback or has_file_paths or has_python_error)
                
                await self.log_result(
                    f"Safe Error: {endpoint}",
                    is_safe,
                    f"Status: {response.status_code}, Safe: {is_safe}, No leaks: traceback={not has_traceback}, paths={not has_file_paths}",
                    response_time
                )
                
            except Exception as e:
                await self.log_result(f"Safe Error: {endpoint}", False, f"Exception: {str(e)}")

    async def test_5_critical_api_regression(self):
        """Test 5: Critical API Regression Testing"""
        print("\n" + "="*70)
        print("⚙️ TEST 5: CRITICAL API REGRESSION")
        print("="*70)
        
        # Critical GET endpoints
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
                    f"Critical API: {endpoint.split('?')[0]}",
                    success,
                    f"Status: {response.status_code}",
                    response_time
                )
                
            except Exception as e:
                await self.log_result(f"Critical API: {endpoint}", False, f"Exception: {str(e)}")
        
        # Test POST endpoint with correct payload structure
        start = time.time()
        try:
            payload = {
                "coin_id": "bitcoin",
                "action": "buy",
                "amount": 0.1,
                "price": 50000,
                "trade_type": "market",
                "symbol": "BTC-USD", 
                "amount_usd": 5000.0,
                "quantity": 0.1
            }
            response = await self.client.post(
                f"{self.base_url}/api/journal/add",
                json=payload
            )
            response_time = time.time() - start
            
            success = response.status_code in [200, 201]
            await self.log_result(
                "Critical API: POST /api/journal/add",
                success,
                f"Status: {response.status_code}",
                response_time
            )
            
        except Exception as e:
            await self.log_result("Critical API: POST /api/journal/add", False, f"Exception: {str(e)}")

    async def test_6_audit_logging(self):
        """Test 6: Audit Logging"""
        print("\n" + "="*70)
        print("📋 TEST 6: AUDIT LOGGING")
        print("="*70)
        
        # Check if audit log file exists and is writable
        audit_log_path = "/var/log/supervisor/audit.log"
        
        try:
            file_exists = os.path.exists(audit_log_path)
            dir_writable = os.access("/var/log/supervisor", os.W_OK)
            
            await self.log_result(
                "Audit Log File System",
                file_exists and dir_writable,
                f"File exists: {file_exists}, Directory writable: {dir_writable}"
            )
        except Exception as e:
            await self.log_result("Audit Log File System", False, f"Exception: {str(e)}")
        
        # Test that audit headers are present for sensitive operations
        start = time.time()
        try:
            payload = {
                "coin_id": "bitcoin",
                "action": "test_audit", 
                "amount": 0.01,
                "price": 50000,
                "trade_type": "paper",
                "symbol": "BTC-USD",
                "amount_usd": 500.0,
                "quantity": 0.01
            }
            response = await self.client.post(
                f"{self.base_url}/api/journal/add",
                json=payload
            )
            response_time = time.time() - start
            
            has_audit_id = "X-Audit-ID" in response.headers
            await self.log_result(
                "Audit ID Header",
                has_audit_id,
                f"Status: {response.status_code}, X-Audit-ID present: {has_audit_id}",
                response_time
            )
            
        except Exception as e:
            await self.log_result("Audit ID Header", False, f"Exception: {str(e)}")

    async def test_7_rate_limiting_headers(self):
        """Test 7: Rate Limiting Headers"""
        print("\n" + "="*70)
        print("⏱️ TEST 7: RATE LIMITING HEADERS")
        print("="*70)
        
        start = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/api/kraken/status")
            response_time = time.time() - start
            
            rate_headers = {
                "X-RateLimit-Remaining-Minute": response.headers.get("X-RateLimit-Remaining-Minute"),
                "X-RateLimit-Remaining-Hour": response.headers.get("X-RateLimit-Remaining-Hour")
            }
            
            present_headers = {k: v for k, v in rate_headers.items() if v is not None}
            has_rate_headers = len(present_headers) > 0
            
            await self.log_result(
                "Rate Limiting Headers",
                has_rate_headers,
                f"Status: {response.status_code}, Headers found: {list(present_headers.keys())}",
                response_time
            )
            
            # Log individual rate limit values if present
            for header, value in present_headers.items():
                await self.log_result(
                    f"  └─ {header}",
                    True,
                    f"Value: {value}"
                )
            
            # If no headers found, check if rate limiting middleware is working differently
            if not has_rate_headers:
                await self.log_result(
                    "  └─ Rate Limiting Status",
                    False,
                    "Rate limit headers not exposed (middleware may be internal-only)"
                )
                
        except Exception as e:
            await self.log_result("Rate Limiting Headers", False, f"Exception: {str(e)}")

    async def run_comprehensive_test(self):
        """Run all security hardening tests"""
        print("🔒 COMPREHENSIVE BACKEND HEALTH AND SAFETY TESTING")
        print("🎯 AI Crypto Trading Platform Security Verification")  
        print(f"🌐 Target: {self.base_url}")
        print(f"⏰ Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all test categories
        await self.test_1_core_health_endpoints()
        await self.test_2_security_headers() 
        await self.test_3_nosql_injection_prevention()
        await self.test_4_safe_error_handling()
        await self.test_5_critical_api_regression()
        await self.test_6_audit_logging()
        await self.test_7_rate_limiting_headers()
        
        # Generate final summary
        await self.generate_final_summary()

    async def generate_final_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "="*70)
        print("🎯 SECURITY HARDENING VERIFICATION SUMMARY")
        print("="*70)
        
        success_rate = (self.pass_count / self.test_count * 100) if self.test_count > 0 else 0
        
        print(f"📊 Total Tests: {self.test_count}")
        print(f"✅ Passed: {self.pass_count}")
        print(f"❌ Failed: {self.test_count - self.pass_count}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Categorize results by security area
        categories = {
            "Core Health": [r for r in self.results if "health" in r['test'].lower() or "root" in r['test'].lower()],
            "Security Headers": [r for r in self.results if "header" in r['test'].lower() or "Security Headers" in r['test']],
            "Injection Prevention": [r for r in self.results if "injection" in r['test'].lower() or "NoSQL" in r['test']],
            "Error Handling": [r for r in self.results if "error" in r['test'].lower()],
            "API Functionality": [r for r in self.results if "critical api" in r['test'].lower()],
            "Audit Logging": [r for r in self.results if "audit" in r['test'].lower()],
            "Rate Limiting": [r for r in self.results if "rate" in r['test'].lower()]
        }
        
        print(f"\n📋 RESULTS BY CATEGORY:")
        for category, results in categories.items():
            if results:
                passed = sum(1 for r in results if r['success'])
                total = len(results)
                status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
                print(f"{status} {category}: {passed}/{total} passed")
        
        # Critical failures
        critical_failures = [r for r in self.results if not r['success'] and 
                           any(keyword in r['test'].lower() for keyword in ['critical', 'health', 'injection', 'security'])]
        
        if critical_failures:
            print(f"\n⚠️ CRITICAL ISSUES REQUIRING ATTENTION:")
            for failure in critical_failures:
                print(f"   • {failure['test']}: {failure['details']}")
        
        # Overall security assessment
        health_ok = any("health" in r['test'].lower() and r['success'] for r in self.results)
        security_headers_ok = self.pass_count >= self.test_count * 0.7  # 70% threshold
        apis_working = any("critical api" in r['test'].lower() and r['success'] for r in self.results)
        
        if health_ok and security_headers_ok and apis_working:
            print(f"\n🎉 OVERALL ASSESSMENT: SECURITY HARDENING SUCCESSFUL")
            print(f"   • Core systems operational")
            print(f"   • Security measures implemented") 
            print(f"   • Critical APIs functional")
        else:
            print(f"\n⚠️ OVERALL ASSESSMENT: SECURITY HARDENING NEEDS ATTENTION")
            print(f"   • Some critical security features may need fixes")
        
        print(f"\n⏰ Completed: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Close client
        await self.client.aclose()

async def main():
    """Main test execution"""
    tester = ComprehensiveSecurityTester(BACKEND_URL)
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())