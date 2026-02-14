#!/usr/bin/env python3
"""
State Persistence System Testing - July 2025
==============================================
Testing the new State Persistence system for Tethys AI Crypto Trading Platform.
This system fixes issues where buttons (Auto Trading, Monitoring, Orchestrator, etc.) 
would reset when users navigate away from pages.

Test Coverage:
1. System State API endpoints
2. State Persistence Integration with existing endpoints
3. Complete test scenario: set -> verify -> stop -> verify
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Backend URL configuration
BASE_URL = "https://kraken-security-scan.preview.emergentagent.com/api"

class StatePersistenceTester:
    def __init__(self):
        self.results = {
            'system_state_api': [],
            'auto_trading_integration': [],
            'adaptive_monitoring_integration': [],
            'master_orchestrator_integration': [],
            'tethys_trading_integration': [],
            'tethys_status_badge': [],
            'test_scenario': []
        }
        self.session = requests.Session()
        self.session.timeout = 30

    def test_endpoint(self, method: str, endpoint: str, data: Dict = None, 
                     expected_status: int = 200, category: str = 'unknown') -> Dict:
        """Test individual endpoint and return result"""
        url = f"{BASE_URL}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            duration = time.time() - start_time
            
            result = {
                'endpoint': endpoint,
                'method': method,
                'status_code': response.status_code,
                'expected_status': expected_status,
                'success': response.status_code == expected_status,
                'duration': round(duration, 3),
                'response_size': len(response.content),
                'timestamp': datetime.now().isoformat()
            }
            
            # Try to parse JSON response
            try:
                result['response'] = response.json()
            except:
                result['response'] = response.text[:500]
            
            # Add to appropriate category
            if category in self.results:
                self.results[category].append(result)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            result = {
                'endpoint': endpoint,
                'method': method,
                'status_code': 0,
                'expected_status': expected_status,
                'success': False,
                'duration': round(duration, 3),
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
            if category in self.results:
                self.results[category].append(result)
            
            return result

    def test_system_state_api(self):
        """Test System State API endpoints"""
        print("🔄 Testing System State API endpoints...")
        
        # 1. GET /api/system-state/all - Should return all component states
        self.test_endpoint('GET', '/system-state/all', 
                          category='system_state_api')
        
        # 2. GET /api/system-state/{component} - Test specific components
        components = ['auto_trading', 'adaptive_monitoring', 'master_orchestrator', 'tethys_trading']
        for component in components:
            self.test_endpoint('GET', f'/system-state/{component}', 
                              category='system_state_api')
        
        # 3. POST /api/system-state/set - Set component state
        test_data = {
            "component": "auto_trading",
            "is_running": True,
            "user_id": "default",
            "metadata": {"test": "state_persistence_test"}
        }
        self.test_endpoint('POST', '/system-state/set', data=test_data,
                          category='system_state_api')
        
        # 4. GET /api/system-state/running/summary - Should return summary of running components
        self.test_endpoint('GET', '/system-state/running/summary', 
                          category='system_state_api')

    def test_auto_trading_integration(self):
        """Test Auto Trading state persistence integration"""
        print("🔄 Testing Auto Trading state persistence integration...")
        
        # 1. GET /api/auto-trading/status - Should include persisted_running field
        self.test_endpoint('GET', '/auto-trading/status', 
                          category='auto_trading_integration')
        
        # 2. POST /api/auto-trading/start - Should persist auto_trading state as running
        self.test_endpoint('POST', '/auto-trading/start', 
                          category='auto_trading_integration')
        
        # 3. Verify state persisted after start
        time.sleep(1)  # Allow time for state persistence
        self.test_endpoint('GET', '/auto-trading/status', 
                          category='auto_trading_integration')
        
        # 4. POST /api/auto-trading/stop - Should persist auto_trading state as stopped
        self.test_endpoint('POST', '/auto-trading/stop', 
                          category='auto_trading_integration')
        
        # 5. Verify state persisted after stop
        time.sleep(1)  # Allow time for state persistence
        self.test_endpoint('GET', '/auto-trading/status', 
                          category='auto_trading_integration')

    def test_adaptive_monitoring_integration(self):
        """Test Adaptive Monitoring state persistence"""
        print("🔄 Testing Adaptive Monitoring state persistence...")
        
        # 1. GET /api/adaptive-strategy/status - Should reflect persisted monitoring state
        self.test_endpoint('GET', '/adaptive-strategy/status', 
                          category='adaptive_monitoring_integration')
        
        # 2. POST /api/adaptive-strategy/monitoring/start - Should persist state
        self.test_endpoint('POST', '/adaptive-strategy/monitoring/start', 
                          category='adaptive_monitoring_integration')
        
        # 3. Verify state after start
        time.sleep(1)
        self.test_endpoint('GET', '/adaptive-strategy/status', 
                          category='adaptive_monitoring_integration')
        
        # 4. POST /api/adaptive-strategy/monitoring/stop - Should persist stopped state
        self.test_endpoint('POST', '/adaptive-strategy/monitoring/stop', 
                          category='adaptive_monitoring_integration')
        
        # 5. Verify state after stop
        time.sleep(1)
        self.test_endpoint('GET', '/adaptive-strategy/status', 
                          category='adaptive_monitoring_integration')

    def test_master_orchestrator_integration(self):
        """Test Master Orchestrator state persistence"""
        print("🔄 Testing Master Orchestrator state persistence...")
        
        # Note: Based on the review request, these endpoints should exist
        # If they don't exist yet, we'll document that in our findings
        
        # 1. GET /api/master/status - Should include persisted_running field
        self.test_endpoint('GET', '/master/status', 
                          category='master_orchestrator_integration')
        
        # 2. POST /api/master/start - Should persist state
        self.test_endpoint('POST', '/master/start', 
                          category='master_orchestrator_integration')
        
        # 3. Verify state after start
        time.sleep(1)
        self.test_endpoint('GET', '/master/status', 
                          category='master_orchestrator_integration')
        
        # 4. POST /api/master/stop - Should persist stopped state
        self.test_endpoint('POST', '/master/stop', 
                          category='master_orchestrator_integration')
        
        # 5. Verify state after stop
        time.sleep(1)
        self.test_endpoint('GET', '/master/status', 
                          category='master_orchestrator_integration')

    def test_tethys_trading_integration(self):
        """Test Tethys Trading state persistence"""
        print("🔄 Testing Tethys Trading state persistence...")
        
        # 1. GET /api/tethys-trading/status - Should include persisted_running field
        self.test_endpoint('GET', '/tethys-trading/status', 
                          category='tethys_trading_integration')
        
        # 2. POST /api/tethys-trading/start - Should persist state
        self.test_endpoint('POST', '/tethys-trading/start', 
                          category='tethys_trading_integration')
        
        # 3. Verify state after start
        time.sleep(1)
        self.test_endpoint('GET', '/tethys-trading/status', 
                          category='tethys_trading_integration')
        
        # 4. POST /api/tethys-trading/stop - Should persist stopped state
        self.test_endpoint('POST', '/tethys-trading/stop', 
                          category='tethys_trading_integration')
        
        # 5. Verify state after stop
        time.sleep(1)
        self.test_endpoint('GET', '/tethys-trading/status', 
                          category='tethys_trading_integration')

    def test_tethys_status_badge(self):
        """Test Tethys Status Badge with persisted states"""
        print("🔄 Testing Tethys Status Badge...")
        
        # GET /api/tethys/status - Should include persisted_states object showing all Tethys-related component states
        self.test_endpoint('GET', '/tethys/status', 
                          category='tethys_status_badge')

    def run_complete_test_scenario(self):
        """Run the complete test scenario from the review request"""
        print("🔄 Running complete test scenario...")
        
        # 1. Set auto_trading to running via /api/system-state/set
        print("   Step 1: Setting auto_trading to running...")
        set_data = {
            "component": "auto_trading",
            "is_running": True,
            "user_id": "default",
            "metadata": {"test_scenario": "complete_cycle"}
        }
        result1 = self.test_endpoint('POST', '/system-state/set', data=set_data,
                                   category='test_scenario')
        
        time.sleep(2)  # Allow time for state persistence
        
        # 2. Verify /api/auto-trading/status shows persisted_running: true
        print("   Step 2: Verifying auto-trading status shows persisted_running: true...")
        result2 = self.test_endpoint('GET', '/auto-trading/status', 
                                   category='test_scenario')
        
        # 3. Stop it via /api/auto-trading/stop
        print("   Step 3: Stopping auto-trading...")
        result3 = self.test_endpoint('POST', '/auto-trading/stop', 
                                   category='test_scenario')
        
        time.sleep(2)  # Allow time for state persistence
        
        # 4. Verify state persisted as stopped
        print("   Step 4: Verifying state persisted as stopped...")
        result4 = self.test_endpoint('GET', '/auto-trading/status', 
                                   category='test_scenario')
        
        # Analyze the scenario results
        scenario_success = True
        scenario_details = []
        
        if result1['success']:
            scenario_details.append("✅ Step 1: Successfully set auto_trading to running")
        else:
            scenario_details.append("❌ Step 1: Failed to set auto_trading to running")
            scenario_success = False
        
        if result2['success'] and 'response' in result2:
            response = result2['response']
            if isinstance(response, dict) and response.get('persisted_running') == True:
                scenario_details.append("✅ Step 2: auto-trading status shows persisted_running: true")
            else:
                scenario_details.append("❌ Step 2: auto-trading status missing persisted_running field or not true")
                scenario_success = False
        else:
            scenario_details.append("❌ Step 2: Failed to get auto-trading status")
            scenario_success = False
        
        if result3['success']:
            scenario_details.append("✅ Step 3: Successfully stopped auto-trading")
        else:
            scenario_details.append("❌ Step 3: Failed to stop auto-trading")
            scenario_success = False
        
        if result4['success'] and 'response' in result4:
            response = result4['response']
            if isinstance(response, dict) and response.get('persisted_running') == False:
                scenario_details.append("✅ Step 4: auto-trading status shows persisted_running: false")
            else:
                scenario_details.append("❌ Step 4: auto-trading status missing persisted_running field or not false")
                scenario_success = False
        else:
            scenario_details.append("❌ Step 4: Failed to get auto-trading status after stop")
            scenario_success = False
        
        # Add scenario summary to results
        self.results['test_scenario'].append({
            'scenario': 'complete_test_cycle',
            'success': scenario_success,
            'details': scenario_details,
            'timestamp': datetime.now().isoformat()
        })

    def run_all_tests(self):
        """Run all state persistence tests"""
        print("🚀 Starting State Persistence System Testing...")
        print(f"Backend URL: {BASE_URL}")
        print("=" * 80)
        
        start_time = time.time()
        
        # Run all test categories
        self.test_system_state_api()
        self.test_auto_trading_integration()
        self.test_adaptive_monitoring_integration()
        self.test_master_orchestrator_integration()
        self.test_tethys_trading_integration()
        self.test_tethys_status_badge()
        self.run_complete_test_scenario()
        
        total_duration = time.time() - start_time
        
        # Generate comprehensive report
        self.generate_report(total_duration)

    def generate_report(self, total_duration: float):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("🎯 STATE PERSISTENCE SYSTEM TEST RESULTS")
        print("=" * 80)
        
        total_tests = 0
        total_passed = 0
        
        for category, tests in self.results.items():
            if not tests:
                continue
                
            category_passed = sum(1 for t in tests if t.get('success', False))
            category_total = len(tests)
            total_tests += category_total
            total_passed += category_passed
            
            success_rate = (category_passed / category_total * 100) if category_total > 0 else 0
            
            print(f"\n📊 {category.upper().replace('_', ' ')}:")
            print(f"   Success Rate: {success_rate:.1f}% ({category_passed}/{category_total})")
            
            # Show individual test results
            for test in tests:
                if test.get('success', False):
                    status_icon = "✅"
                    duration_info = f" ({test.get('duration', 0):.3f}s)"
                else:
                    status_icon = "❌"
                    duration_info = f" (ERROR: {test.get('error', 'Unknown error')})"
                
                if 'endpoint' in test:
                    print(f"   {status_icon} {test['method']} {test['endpoint']}{duration_info}")
                elif 'scenario' in test:
                    print(f"   {status_icon} {test['scenario']}")
                    for detail in test.get('details', []):
                        print(f"      {detail}")
        
        # Overall summary
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🎉 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {total_passed}")
        print(f"   Failed: {total_tests - total_passed}")
        print(f"   Success Rate: {overall_success_rate:.1f}%")
        print(f"   Total Duration: {total_duration:.2f}s")
        print(f"   Average Response Time: {self.calculate_avg_response_time():.3f}s")
        
        # Critical findings
        self.analyze_critical_findings()
        
        print("\n" + "=" * 80)

    def calculate_avg_response_time(self) -> float:
        """Calculate average response time across all tests"""
        durations = []
        for category, tests in self.results.items():
            for test in tests:
                if 'duration' in test and test['success']:
                    durations.append(test['duration'])
        
        return sum(durations) / len(durations) if durations else 0

    def analyze_critical_findings(self):
        """Analyze and report critical findings"""
        print(f"\n🔍 CRITICAL FINDINGS:")
        
        # Check if System State API is working
        system_state_tests = self.results.get('system_state_api', [])
        system_state_working = any(t.get('success', False) for t in system_state_tests)
        
        if system_state_working:
            print("   ✅ System State API is operational")
        else:
            print("   ❌ CRITICAL: System State API is not working")
        
        # Check if persisted_running field is present in status endpoints
        persisted_running_found = False
        for category in ['auto_trading_integration', 'tethys_trading_integration']:
            tests = self.results.get(category, [])
            for test in tests:
                if (test.get('success', False) and 
                    'status' in test.get('endpoint', '') and 
                    isinstance(test.get('response'), dict) and
                    'persisted_running' in test.get('response', {})):
                    persisted_running_found = True
                    break
        
        if persisted_running_found:
            print("   ✅ persisted_running field found in status endpoints")
        else:
            print("   ⚠️  persisted_running field not found in status endpoints")
        
        # Check test scenario success
        scenario_tests = self.results.get('test_scenario', [])
        scenario_success = any(t.get('success', False) for t in scenario_tests)
        
        if scenario_success:
            print("   ✅ Complete test scenario passed")
        else:
            print("   ❌ CRITICAL: Complete test scenario failed")
        
        # Check for missing endpoints
        missing_endpoints = []
        for category, tests in self.results.items():
            for test in tests:
                if test.get('status_code') == 404:
                    missing_endpoints.append(f"{test.get('method', 'GET')} {test.get('endpoint', 'unknown')}")
        
        if missing_endpoints:
            print("   ⚠️  Missing endpoints detected:")
            for endpoint in missing_endpoints:
                print(f"      - {endpoint}")
        else:
            print("   ✅ All expected endpoints are available")


if __name__ == "__main__":
    tester = StatePersistenceTester()
    tester.run_all_tests()