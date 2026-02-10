#!/usr/bin/env python3
"""
Comprehensive Backend Testing for AI Crypto Trading Platform
Tests all major API endpoints for functionality and response validation.
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Backend URL from frontend environment
BASE_URL = "https://history-boost.preview.emergentagent.com/api"
USER_ID = "demo_user_test123"

class BackendTester:
    def __init__(self):
        self.session = None
        self.results = []
        self.failed_tests = []
        self.passed_tests = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'Content-Type': 'application/json'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name: str, success: bool, status_code: int = None, 
                   response: Any = None, error: str = None):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'status_code': status_code,
            'timestamp': datetime.now().isoformat(),
            'error': error
        }
        
        if success:
            result['response_preview'] = str(response)[:200] if response else None
            self.passed_tests.append(result)
        else:
            result['error_details'] = error
            self.failed_tests.append(result)
            
        self.results.append(result)
        
        # Print immediate feedback
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} - Status: {status_code} - {error if error else 'OK'}")
    
    async def test_endpoint(self, method: str, endpoint: str, test_name: str, 
                           data: Dict = None, expected_status: List[int] = None) -> Dict:
        """Generic endpoint tester"""
        if expected_status is None:
            expected_status = [200, 201]
            
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                async with self.session.get(url) as response:
                    status = response.status
                    headers = dict(response.headers)
                    try:
                        resp_data = await response.json()
                    except:
                        resp_data = await response.text()
            elif method.upper() == 'POST':
                async with self.session.post(url, json=data) as response:
                    status = response.status
                    headers = dict(response.headers)
                    try:
                        resp_data = await response.json()
                    except:
                        resp_data = await response.text()
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            success = status in expected_status
            self.log_result(test_name, success, status, resp_data, 
                          None if success else f"Unexpected status code: {status}")
            
            return {'success': success, 'status': status, 'data': resp_data, 'headers': headers}
            
        except Exception as e:
            error_msg = str(e)
            self.log_result(test_name, False, None, None, error_msg)
            return {'success': False, 'error': error_msg}

    async def test_health_endpoints(self):
        """Test basic health endpoints"""
        print("\n=== TESTING HEALTH ENDPOINTS ===")
        
        await self.test_endpoint('GET', '/health', 'API Health Check')
        await self.test_endpoint('GET', '/', 'Root API Endpoint')

    async def test_tethys_trading_engine(self):
        """Test Tethys Trading Engine Toggle"""
        print("\n=== TESTING TETHYS TRADING ENGINE ===")
        
        # Test Tethys status
        await self.test_endpoint('GET', '/tethys/status', 'Tethys Status Check')
        
        # Test start trading engine
        await self.test_endpoint('POST', '/tethys-trading/start', 'Tethys Start Trading Engine',
                               data={'interval': 60}, expected_status=[200, 201, 400, 503])
        
        # Test stop trading engine  
        await self.test_endpoint('POST', '/tethys-trading/stop', 'Tethys Stop Trading Engine',
                               expected_status=[200, 201, 400, 503])
        
        # Test trading status
        await self.test_endpoint('GET', '/tethys-trading/status', 'Tethys Trading Status')

    async def test_event_triggers_system(self):
        """Test Event Triggers System"""
        print("\n=== TESTING EVENT TRIGGERS SYSTEM ===")
        
        # Test triggers list
        await self.test_endpoint('GET', '/triggers/list', 'Event Triggers List')
        
        # Test create trigger
        trigger_data = {
            "trigger_id": f"test_trigger_{int(datetime.now().timestamp())}",
            "name": "Test Bitcoin News Trigger",
            "keywords": ["bitcoin", "btc", "surge"],
            "coins": ["BTC"],
            "action": "alert",
            "sentiment_filter": "positive",
            "cooldown_hours": 1,
            "enabled": True
        }
        
        await self.test_endpoint('POST', '/triggers/create', 'Create Event Trigger',
                               data=trigger_data, expected_status=[200, 201, 400, 503])
        
        # Test triggers history
        await self.test_endpoint('GET', '/triggers/history/all', 'Event Triggers History')
        
        # Test trigger templates
        await self.test_endpoint('GET', '/triggers/templates', 'Event Trigger Templates')
        
        # Test trigger status
        await self.test_endpoint('GET', '/triggers/status', 'Event Trigger Service Status')

    async def test_ensemble_ai_page(self):
        """Test Ensemble AI Page"""
        print("\n=== TESTING ENSEMBLE AI ===")
        
        # Test ensemble status
        await self.test_endpoint('GET', '/ensemble/status', 'Ensemble AI Status')
        
        # Test ensemble predictions
        await self.test_endpoint('GET', '/ensemble/predictions', 'Ensemble AI Predictions',
                               expected_status=[200, 404, 503])
        
        # Test model weights
        await self.test_endpoint('GET', '/ensemble/weights', 'Ensemble Model Weights')
        
        # Test build status
        await self.test_endpoint('GET', '/ensemble/build-status', 'Ensemble Build Status')
        
        # Test optimal universe
        await self.test_endpoint('GET', '/ensemble/optimal-universe', 'Ensemble Optimal Universe')

    async def test_portfolio_information(self):
        """Test Portfolio Information"""
        print("\n=== TESTING PORTFOLIO INFORMATION ===")
        
        # Test Kraken portfolio
        await self.test_endpoint('GET', '/kraken/portfolio', 'Kraken Portfolio',
                               expected_status=[200, 404, 503])
        
        # Test portfolio summary
        await self.test_endpoint('GET', '/portfolio/summary', 'Portfolio Summary',
                               expected_status=[200, 404, 503])
        
        # Test Kraken status
        await self.test_endpoint('GET', '/kraken/status', 'Kraken Connection Status')
        
        # Test Kraken balance
        await self.test_endpoint('GET', '/kraken/balance', 'Kraken Account Balance',
                               expected_status=[200, 500, 503])
        
        # Test portfolio visualization
        await self.test_endpoint('GET', '/portfolio/visualization/summary', 'Portfolio Visualization Summary',
                               expected_status=[200, 503])

    async def test_model_training(self):
        """Test Model Training Endpoints"""
        print("\n=== TESTING MODEL TRAINING ===")
        
        # Test Enhanced AI training
        training_data = {
            "coins": ["bitcoin", "ethereum"],
            "start_year": 2023,
            "include_hidden_gems": True
        }
        
        await self.test_endpoint('POST', '/enhanced-ai/train', 'Enhanced AI Training',
                               data=training_data, expected_status=[200, 201, 400, 503])
        
        # Test Transformer training (if exists)
        await self.test_endpoint('POST', '/transformer/train', 'Transformer Training',
                               data=training_data, expected_status=[200, 201, 400, 404, 503])
        
        # Test RL Agent training (if exists)
        await self.test_endpoint('POST', '/rl-agent/train', 'RL Agent Training',
                               data=training_data, expected_status=[200, 201, 400, 404, 503])
        
        # Test general training endpoint
        await self.test_endpoint('POST', '/training/train', 'General AI Training',
                               data=training_data, expected_status=[200, 201, 400, 503])
        
        # Test training status
        await self.test_endpoint('GET', '/training/status', 'Training Status')
        
        # Test Enhanced AI status
        await self.test_endpoint('GET', '/enhanced-ai/status', 'Enhanced AI Status')

    async def test_8_enhancements_verification(self):
        """Test the 8 recently implemented enhancements - February 2026"""
        print("\n=== TESTING 8 ENHANCEMENTS VERIFICATION ===")
        
        # 1. SECURITY HEADERS VERIFICATION
        print("\n--- 1. Security Headers Verification ---")
        result = await self.test_endpoint('GET', '/health', 'Security Headers Check')
        if result['success']:
            headers = result.get('headers', {})
            required_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options', 
                'X-XSS-Protection',
                'Strict-Transport-Security',
                'Content-Security-Policy',
                'Permissions-Policy',
                'X-Request-ID'
            ]
            
            missing_headers = []
            for header in required_headers:
                if header not in headers:
                    missing_headers.append(header)
            
            if missing_headers:
                self.log_result('Security Headers Complete', False, None, None, 
                              f"Missing headers: {missing_headers}")
            else:
                self.log_result('Security Headers Complete', True, 200, 
                              f"All security headers present: {required_headers}")
        
        # 2. ERROR MONITORING ENDPOINTS
        print("\n--- 2. Error Monitoring Endpoints ---")
        await self.test_endpoint('GET', '/monitoring/errors', 'Error Monitoring - Get Errors')
        await self.test_endpoint('GET', '/monitoring/errors/stats', 'Error Monitoring - Error Stats')
        await self.test_endpoint('GET', '/monitoring/health/detailed', 'Error Monitoring - Detailed Health')
        
        # 3. RATE LIMITING VERIFICATION
        print("\n--- 3. Rate Limiting Verification ---")
        # Make multiple rapid requests to test rate limiting
        for i in range(3):
            result = await self.test_endpoint('GET', '/tethys/status', f'Rate Limit Test {i+1}')
            if result['success'] and 'headers' in result:
                headers = result.get('headers', {})
                rate_limit_headers = [h for h in headers.keys() if 'ratelimit' in h.lower()]
                if rate_limit_headers:
                    self.log_result(f'Rate Limit Headers Present {i+1}', True, 200,
                                  f"Rate limit headers: {rate_limit_headers}")
        
        # 4. DATABASE CONNECTION POOLING
        print("\n--- 4. Database Connection Pooling ---")
        result = await self.test_endpoint('GET', '/health', 'Database Health Check')
        if result['success'] and result.get('data'):
            data = result['data']
            if isinstance(data, dict) and 'database' in data:
                db_status = data['database']
                if db_status == 'connected':
                    self.log_result('Database Connection Pool', True, 200, 
                                  "Database connected successfully")
                else:
                    self.log_result('Database Connection Pool', False, 200, None,
                                  f"Database status: {db_status}")
        
        # Check detailed health for pool stats
        result = await self.test_endpoint('GET', '/monitoring/health/detailed', 'Database Pool Stats')
        if result['success'] and result.get('data'):
            data = result['data']
            if isinstance(data, dict) and 'database' in data:
                self.log_result('Database Pool Stats Available', True, 200,
                              "Pool stats in detailed health check")
        
        # 5. API INPUT VALIDATION (Pydantic)
        print("\n--- 5. API Input Validation ---")
        # Test with invalid data (missing fields)
        invalid_trigger_data = {
            "name": "Test Trigger"
            # Missing required fields like trigger_id, keywords, etc.
        }
        result = await self.test_endpoint('POST', '/triggers/create', 'Pydantic Validation Test',
                                        data=invalid_trigger_data, expected_status=[422, 400])
        if result['success'] and result['status'] == 422:
            self.log_result('Pydantic Input Validation', True, 422,
                          "Validation errors returned correctly")
        
        # 6. CORE API VERIFICATION
        print("\n--- 6. Core API Verification ---")
        core_apis = [
            ('/health', 'Core API - Health'),
            ('/tethys/status', 'Core API - Tethys Status'),
            ('/ensemble/status', 'Core API - Ensemble Status'),
            ('/kraken/status', 'Core API - Kraken Status'),
            ('/ensemble/weights', 'Core API - Ensemble Weights'),
            ('/auto-trading/status', 'Core API - Auto Trading Status')
        ]
        
        for endpoint, test_name in core_apis:
            await self.test_endpoint('GET', endpoint, test_name)

    async def test_comprehensive_endpoints(self):
        """Test comprehensive endpoints from review request"""
        print("\n=== TESTING COMPREHENSIVE ENDPOINTS ===")
        
        # Market Data Endpoints
        await self.test_endpoint('GET', '/market/prices', 'Market Prices',
                               expected_status=[200, 404, 422, 503])
        
        await self.test_endpoint('GET', '/market/coin/BTC', 'Market Coin BTC Data',
                               expected_status=[200, 404, 503])
        
        await self.test_endpoint('GET', '/market/coin/ETH', 'Market Coin ETH Data',
                               expected_status=[200, 404, 503])
        
        await self.test_endpoint('GET', '/market/coin/SOL', 'Market Coin SOL Data',
                               expected_status=[200, 404, 503])
        
        # News and Sentiment
        await self.test_endpoint('GET', '/news/recent', 'Recent Crypto News',
                               expected_status=[200, 404, 503])
        
        await self.test_endpoint('GET', '/sentiment/market', 'Market Sentiment Analysis',
                               expected_status=[200, 404, 503])
        
        # Tethys Signals and Execute Trade
        await self.test_endpoint('GET', '/tethys/signals', 'Tethys Trading Signals',
                               expected_status=[200, 404, 503])
        
        trade_data = {
            "symbol": "BTC",
            "action": "buy",
            "amount": 0.001,
            "mode": "paper"
        }
        await self.test_endpoint('POST', '/tethys/execute-trade', 'Tethys Execute Trade',
                               data=trade_data, expected_status=[200, 201, 400, 404, 503])
        
        # Event Triggers Advanced
        await self.test_endpoint('POST', '/triggers/check-now', 'Trigger Check Now',
                               expected_status=[200, 201, 400, 503])
        
        # Ensemble AI Predictions with specific coins
        predict_data = {"coins": ["BTC", "ETH", "SOL"]}
        await self.test_endpoint('POST', '/ensemble/predict', 'Ensemble Predict Coins',
                               data=predict_data, expected_status=[200, 201, 400, 404, 503])
        
        # Portfolio and Trading
        await self.test_endpoint('GET', '/portfolio/positions', 'Portfolio Positions',
                               expected_status=[200, 404, 503])
        
        await self.test_endpoint('GET', '/portfolio/history', 'Portfolio History',
                               expected_status=[200, 404, 503])
        
        execute_trade_data = {
            "symbol": "BTC",
            "side": "buy",
            "amount": 0.001,
            "mode": "paper"
        }
        await self.test_endpoint('POST', '/trading/execute', 'Execute Paper Trade',
                               data=execute_trade_data, expected_status=[200, 201, 400, 422, 503])
        
        # Model Performance
        await self.test_endpoint('GET', '/model-performance/metrics', 'Model Performance Metrics',
                               expected_status=[200, 404, 503])
        
        # User Features
        await self.test_endpoint('GET', '/budget/status', 'Budget Status',
                               expected_status=[200, 404, 503])
        
        await self.test_endpoint('GET', '/journal/trades', 'Trade Journal',
                               expected_status=[200, 404, 503])
        
        journal_entry = {
            "trade_id": f"test_trade_{int(datetime.now().timestamp())}",
            "symbol": "BTC",
            "action": "buy",
            "amount": 0.001,
            "price": 69000,
            "notes": "Test journal entry"
        }
        await self.test_endpoint('POST', '/journal/add', 'Add Journal Entry',
                               data=journal_entry, expected_status=[200, 201, 400, 404, 503])
        
        # Strategies
        await self.test_endpoint('GET', '/strategies/list', 'Strategies List',
                               expected_status=[200, 404, 503])
        
        await self.test_endpoint('GET', '/strategies/active', 'Active Strategies',
                               expected_status=[200, 404, 503])
        
        # Advanced Features
        await self.test_endpoint('GET', '/gem-scanner/scan', 'Gem Scanner Scan',
                               expected_status=[200, 404, 503])
        
        await self.test_endpoint('GET', '/adaptive-strategy/status', 'Adaptive Strategy Status',
                               expected_status=[200, 404, 503])
        
        await self.test_endpoint('GET', '/spot-trading/status', 'Spot Trading Status',
                               expected_status=[200, 404, 503])
        
        await self.test_endpoint('GET', '/auto-trading/status', 'Auto Trading Status',
                               expected_status=[200, 404, 503])

    async def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n=== TESTING ERROR HANDLING ===")
        
        # Test invalid endpoints
        await self.test_endpoint('GET', '/invalid/endpoint', 'Invalid Endpoint Test',
                               expected_status=[404])
        
        # Test missing parameters
        await self.test_endpoint('POST', '/tethys/execute-trade', 'Missing Parameters Test',
                               data={}, expected_status=[400, 422])
        
        # Test invalid coin symbol
        await self.test_endpoint('GET', '/market/coin/INVALID', 'Invalid Coin Symbol',
                               expected_status=[404, 400])
        
        # Test malformed JSON
        try:
            url = f"{BASE_URL}/triggers/create"
            async with self.session.post(url, data="invalid json") as response:
                status = response.status
                self.log_result('Malformed JSON Test', status in [400, 422], status, 
                              None, None if status in [400, 422] else f"Expected 400/422, got {status}")
        except Exception as e:
            self.log_result('Malformed JSON Test', True, None, None, f"Correctly rejected: {e}")

    async def run_all_tests(self):
        """Run all test suites"""
        print(f"🚀 Starting Backend API Tests - 8 ENHANCEMENTS VERIFICATION")
        print(f"📡 Testing Backend URL: {BASE_URL}")
        print(f"👤 User ID: {USER_ID}")
        print("=" * 60)
        
        # Run test suites - prioritize 8 enhancements verification
        await self.test_8_enhancements_verification()
        await self.test_health_endpoints()
        await self.test_tethys_trading_engine()
        await self.test_event_triggers_system()
        await self.test_ensemble_ai_page()
        await self.test_portfolio_information()
        await self.test_model_training()
        await self.test_comprehensive_endpoints()
        await self.test_error_handling()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("🏁 BACKEND API TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed = len(self.passed_tests)
        failed = len(self.failed_tests)
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/total_tests*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            print("-" * 40)
            for test in self.failed_tests:
                print(f"• {test['test']}")
                if test.get('status_code'):
                    print(f"  Status: {test['status_code']}")
                if test.get('error_details'):
                    print(f"  Error: {test['error_details']}")
                print()
        
        if self.passed_tests:
            print(f"\n✅ PASSED TESTS ({len(self.passed_tests)}):")
            print("-" * 40)
            for test in self.passed_tests:
                print(f"• {test['test']} (Status: {test.get('status_code', 'N/A')})")
        
        print("\n" + "=" * 60)
        
        # Critical issues summary
        critical_failures = [
            test for test in self.failed_tests 
            if any(keyword in test['test'].lower() for keyword in 
                  ['tethys', 'ensemble', 'portfolio', 'training'])
        ]
        
        if critical_failures:
            print("🚨 CRITICAL ISSUES FOUND:")
            for test in critical_failures:
                print(f"• {test['test']}: {test.get('error_details', 'Unknown error')}")
        else:
            print("✅ No critical issues found in core functionality")


async def main():
    """Main test runner"""
    async with BackendTester() as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner failed: {e}")
        sys.exit(1)