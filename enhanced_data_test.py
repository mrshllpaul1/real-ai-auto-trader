#!/usr/bin/env python3
"""
Enhanced Data API Testing
Focused testing for the new Enhanced Data API endpoints.
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

# Backend URL from frontend environment
BASE_URL = "https://smart-trade-ai-68.preview.emergentagent.com/api"

class EnhancedDataTester:
    def __init__(self):
        self.session = None
        self.results = []
        self.failed_tests = []
        self.passed_tests = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={'Content-Type': 'application/json'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name: str, success: bool, status_code: int = None, 
                   response: any = None, error: str = None):
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
                           data: dict = None, expected_status: list = None) -> dict:
        """Generic endpoint tester"""
        if expected_status is None:
            expected_status = [200, 201]
            
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                async with self.session.get(url) as response:
                    status = response.status
                    try:
                        resp_data = await response.json()
                    except:
                        resp_data = await response.text()
            elif method.upper() == 'POST':
                async with self.session.post(url, json=data) as response:
                    status = response.status
                    try:
                        resp_data = await response.json()
                    except:
                        resp_data = await response.text()
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            success = status in expected_status
            self.log_result(test_name, success, status, resp_data, 
                          None if success else f"Unexpected status code: {status}")
            
            return {'success': success, 'status': status, 'data': resp_data}
            
        except Exception as e:
            error_msg = str(e)
            self.log_result(test_name, False, None, None, error_msg)
            return {'success': False, 'error': error_msg}

    async def test_enhanced_data_endpoints(self):
        """Test all Enhanced Data API endpoints"""
        print("🚀 ENHANCED DATA API COMPREHENSIVE TESTING")
        print("=" * 60)
        
        # 1. KRAKEN UNIVERSE ENDPOINTS
        print("\n=== 1. KRAKEN UNIVERSE ENDPOINTS ===")
        
        await self.test_endpoint('GET', '/enhanced-data/kraken-universe/stats', 
                               'Kraken Universe Stats')
        
        await self.test_endpoint('GET', '/enhanced-data/kraken-universe/coins', 
                               'Kraken Universe All Coins')
        
        await self.test_endpoint('GET', '/enhanced-data/kraken-universe/unique-coins', 
                               'Kraken Universe Unique Coins')
        
        await self.test_endpoint('GET', '/enhanced-data/kraken-universe/check-new', 
                               'Kraken Universe Check New Coins')
        
        await self.test_endpoint('GET', '/enhanced-data/kraken-universe/coin/BTC', 
                               'Kraken Universe BTC Pairs')
        
        await self.test_endpoint('GET', '/enhanced-data/kraken-universe/coins?quote_currency=EUR', 
                               'Kraken Universe EUR Pairs')
        
        # 2. ON-CHAIN METRICS ENDPOINTS
        print("\n=== 2. ON-CHAIN METRICS ENDPOINTS ===")
        
        await self.test_endpoint('GET', '/enhanced-data/onchain/supported', 
                               'On-Chain Supported Chains')
        
        await self.test_endpoint('GET', '/enhanced-data/onchain/btc/stats', 
                               'On-Chain BTC Network Stats')
        
        await self.test_endpoint('GET', '/enhanced-data/onchain/eth/stats', 
                               'On-Chain ETH Stats')
        
        await self.test_endpoint('GET', '/enhanced-data/onchain/BTC/whales?min_usd=1000000', 
                               'On-Chain BTC Whale Transactions')
        
        await self.test_endpoint('GET', '/enhanced-data/onchain/btc/mempool', 
                               'On-Chain BTC Mempool Stats')
        
        await self.test_endpoint('GET', '/enhanced-data/onchain/btc/fees', 
                               'On-Chain BTC Fee Estimates')
        
        await self.test_endpoint('GET', '/enhanced-data/onchain/btc/difficulty', 
                               'On-Chain BTC Difficulty Adjustment')
        
        # 3. MULTI-TIMEFRAME ENDPOINTS
        print("\n=== 3. MULTI-TIMEFRAME ENDPOINTS ===")
        
        await self.test_endpoint('GET', '/enhanced-data/multitimeframe/stats', 
                               'Multi-Timeframe Storage Statistics')
        
        await self.test_endpoint('GET', '/enhanced-data/multitimeframe/BTC/features', 
                               'Multi-Timeframe BTC Training Features')
        
        await self.test_endpoint('GET', '/enhanced-data/multitimeframe/BTC/1D', 
                               'Multi-Timeframe BTC Daily OHLCV Data')
        
        await self.test_endpoint('GET', '/enhanced-data/multitimeframe/BTC/multi?timeframes=1h,4h,1D', 
                               'Multi-Timeframe BTC Multi-Timeframe Data')
        
        await self.test_endpoint('GET', '/enhanced-data/multitimeframe/ETH/1h', 
                               'Multi-Timeframe ETH Hourly Data')
        
        # 4. DATA PROVIDER KEYS
        print("\n=== 4. DATA PROVIDER KEYS ===")
        
        await self.test_endpoint('GET', '/enhanced-data/provider-keys/status', 
                               'Data Provider Keys Status')
        
        # 5. OVERALL STATUS
        print("\n=== 5. OVERALL STATUS ===")
        
        await self.test_endpoint('GET', '/enhanced-data/status', 
                               'Enhanced Data Overall Status')
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("🏁 ENHANCED DATA API TEST RESULTS")
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
        
        # Determine overall status
        if failed == 0:
            print("🎉 ALL ENHANCED DATA API ENDPOINTS WORKING PERFECTLY!")
        elif passed / total_tests >= 0.8:
            print("✅ ENHANCED DATA API MOSTLY FUNCTIONAL - Minor issues found")
        else:
            print("⚠️ ENHANCED DATA API HAS SIGNIFICANT ISSUES")

async def main():
    """Main test runner"""
    async with EnhancedDataTester() as tester:
        await tester.test_enhanced_data_endpoints()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner failed: {e}")
        sys.exit(1)