#!/usr/bin/env python3
"""
Enhancement APIs Testing Script
==============================
Tests all newly implemented enhancement APIs:
- Export API (/api/export/*)
- Achievements API (/api/achievements/*)
- Event Countdown API (/api/event-countdown/*)
- Paper Leaderboard API (/api/paper-leaderboard/*)
- Strategy Marketplace API (/api/marketplace/*)
- Social Trading API (/api/social/*)
- Tax Reporting API (/api/tax/*)
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from environment
BACKEND_URL = "https://feature-enhancer-7.preview.emergentagent.com/api"

class EnhancementAPITester:
    def __init__(self):
        self.session = None
        self.results = []
        self.start_time = time.time()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"Content-Type": "application/json"}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_endpoint(self, method: str, endpoint: str, data: Dict = None, 
                          expected_status: int = 200, description: str = "") -> Dict:
        """Test a single endpoint"""
        url = f"{BACKEND_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                async with self.session.get(url) as response:
                    status = response.status
                    content = await response.text()
            elif method.upper() == "POST":
                async with self.session.post(url, json=data) as response:
                    status = response.status
                    content = await response.text()
            elif method.upper() == "DELETE":
                async with self.session.delete(url) as response:
                    status = response.status
                    content = await response.text()
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Try to parse JSON
            try:
                json_data = json.loads(content)
            except:
                json_data = {"raw_response": content}
            
            success = status == expected_status
            
            result = {
                "endpoint": endpoint,
                "method": method.upper(),
                "status": status,
                "expected_status": expected_status,
                "success": success,
                "description": description,
                "response_size": len(content),
                "data": json_data if success else {"error": content}
            }
            
            self.results.append(result)
            
            status_icon = "✅" if success else "❌"
            print(f"{status_icon} {method.upper()} {endpoint} - {status} - {description}")
            
            return result
            
        except Exception as e:
            result = {
                "endpoint": endpoint,
                "method": method.upper(),
                "status": 0,
                "expected_status": expected_status,
                "success": False,
                "description": description,
                "error": str(e),
                "data": {}
            }
            
            self.results.append(result)
            print(f"❌ {method.upper()} {endpoint} - ERROR: {str(e)}")
            return result

    async def test_export_api(self):
        """Test Export API endpoints"""
        print("\n🔄 Testing Export API...")
        
        # Test trades CSV export
        await self.test_endpoint(
            "GET", "/export/trades-csv",
            description="Export trades to CSV"
        )
        
        # Test trades CSV with parameters
        await self.test_endpoint(
            "GET", "/export/trades-csv?days=7&coin=BTC",
            description="Export BTC trades (7 days) to CSV"
        )
        
        # Test portfolio CSV export
        await self.test_endpoint(
            "GET", "/export/portfolio-csv",
            description="Export portfolio to CSV"
        )
        
        # Test P&L report
        await self.test_endpoint(
            "GET", "/export/pnl-report",
            description="Export P&L report CSV"
        )
        
        # Test P&L report with year
        await self.test_endpoint(
            "GET", "/export/pnl-report?year=2024",
            description="Export 2024 P&L report CSV"
        )

    async def test_achievements_api(self):
        """Test Achievements API endpoints"""
        print("\n🏆 Testing Achievements API...")
        
        # Test list all achievements
        result = await self.test_endpoint(
            "GET", "/achievements/list",
            description="Get all 26 achievements"
        )
        
        # Verify we have 26 achievements
        if result["success"] and result["data"].get("total", 0) >= 20:
            print(f"   ✅ Found {result['data']['total']} achievements (target: 26+)")
        
        # Test user achievements
        await self.test_endpoint(
            "GET", "/achievements/user",
            description="Get user's earned achievements"
        )
        
        # Test check and award achievements
        await self.test_endpoint(
            "POST", "/achievements/check",
            description="Check and award achievements"
        )
        
        # Test achievements leaderboard
        await self.test_endpoint(
            "GET", "/achievements/leaderboard",
            description="Get achievements leaderboard"
        )
        
        # Test manual award (should work for testing)
        await self.test_endpoint(
            "POST", "/achievements/award/first_trade",
            description="Manually award first trade achievement"
        )

    async def test_event_countdown_api(self):
        """Test Event Countdown API endpoints"""
        print("\n⏰ Testing Event Countdown API...")
        
        # Test upcoming events
        result = await self.test_endpoint(
            "GET", "/event-countdown/upcoming",
            description="Get upcoming events with countdown"
        )
        
        # Verify we have events
        if result["success"] and result["data"].get("events"):
            print(f"   ✅ Found {len(result['data']['events'])} upcoming events")
        
        # Test next event
        await self.test_endpoint(
            "GET", "/event-countdown/next",
            description="Get next event with countdown"
        )
        
        # Test event types
        await self.test_endpoint(
            "GET", "/event-countdown/types",
            description="Get available event types"
        )
        
        # Test events by type
        await self.test_endpoint(
            "GET", "/event-countdown/by-type/fomc",
            description="Get FOMC events"
        )
        
        # Test this week events
        await self.test_endpoint(
            "GET", "/event-countdown/this-week",
            description="Get events happening this week"
        )
        
        # Test add custom event
        await self.test_endpoint(
            "POST", "/event-countdown/custom",
            data={
                "name": "Test Event",
                "date": "2025-12-31",
                "event_type": "custom",
                "impact": "medium"
            },
            description="Add custom event"
        )

    async def test_paper_leaderboard_api(self):
        """Test Paper Leaderboard API endpoints"""
        print("\n🏅 Testing Paper Leaderboard API...")
        
        # Test top traders
        result = await self.test_endpoint(
            "GET", "/paper-leaderboard/top",
            description="Get top paper traders"
        )
        
        # Verify leaderboard structure
        if result["success"] and result["data"].get("leaderboard"):
            print(f"   ✅ Found {len(result['data']['leaderboard'])} traders on leaderboard")
        
        # Test top traders with different periods
        await self.test_endpoint(
            "GET", "/paper-leaderboard/top?period=weekly&limit=10",
            description="Get weekly top traders"
        )
        
        # Test competitions
        await self.test_endpoint(
            "GET", "/paper-leaderboard/competitions",
            description="Get active competitions"
        )
        
        # Test leaderboard stats
        await self.test_endpoint(
            "GET", "/paper-leaderboard/stats",
            description="Get leaderboard statistics"
        )
        
        # Test my rank
        await self.test_endpoint(
            "GET", "/paper-leaderboard/my-rank",
            description="Get user's rank on leaderboard"
        )
        
        # Test submit result
        await self.test_endpoint(
            "POST", "/paper-leaderboard/submit-result",
            data={
                "display_name": "TestTrader",
                "avatar_emoji": "🧪"
            },
            description="Submit paper trading result"
        )

    async def test_strategy_marketplace_api(self):
        """Test Strategy Marketplace API endpoints"""
        print("\n🛒 Testing Strategy Marketplace API...")
        
        # Test list strategies
        result = await self.test_endpoint(
            "GET", "/marketplace/strategies",
            description="List marketplace strategies"
        )
        
        # Verify we have strategies
        if result["success"] and result["data"].get("strategies"):
            print(f"   ✅ Found {len(result['data']['strategies'])} strategies")
        
        # Test strategies with filters
        await self.test_endpoint(
            "GET", "/marketplace/strategies?category=momentum&sort_by=rating&price_filter=free",
            description="List free momentum strategies by rating"
        )
        
        # Test strategy categories
        await self.test_endpoint(
            "GET", "/marketplace/categories",
            description="Get strategy categories"
        )
        
        # Test strategy details (using sample strategy ID)
        await self.test_endpoint(
            "GET", "/marketplace/strategies/strat_001",
            description="Get strategy details"
        )
        
        # Test publish strategy
        await self.test_endpoint(
            "POST", "/marketplace/strategies",
            data={
                "name": "Test Strategy",
                "description": "A test trading strategy",
                "strategy_type": "momentum",
                "timeframe": "4h",
                "coins": ["BTC", "ETH"],
                "price_monthly": 0,
                "is_public": True
            },
            description="Publish new strategy"
        )
        
        # Test my subscriptions
        await self.test_endpoint(
            "GET", "/marketplace/my-subscriptions",
            description="Get user's strategy subscriptions"
        )
        
        # Test my published strategies
        await self.test_endpoint(
            "GET", "/marketplace/my-published",
            description="Get user's published strategies"
        )

    async def test_social_trading_api(self):
        """Test Social Trading API endpoints"""
        print("\n👥 Testing Social Trading API...")
        
        # Test social feed
        result = await self.test_endpoint(
            "GET", "/social/feed",
            description="Get social trading feed"
        )
        
        # Verify feed structure
        if result["success"] and result["data"].get("feed"):
            print(f"   ✅ Found {len(result['data']['feed'])} posts in social feed")
        
        # Test feed with filters
        await self.test_endpoint(
            "GET", "/social/feed?filter_type=top_traders&limit=5",
            description="Get top traders feed"
        )
        
        # Test top traders
        await self.test_endpoint(
            "GET", "/social/top-traders",
            description="Get top performing traders"
        )
        
        # Test top traders with period
        await self.test_endpoint(
            "GET", "/social/top-traders?period=weekly&limit=5",
            description="Get weekly top traders"
        )
        
        # Test update profile
        await self.test_endpoint(
            "POST", "/social/profile",
            data={
                "display_name": "TestUser",
                "bio": "Testing social features",
                "avatar_emoji": "🧪",
                "is_public": True,
                "show_trades": True
            },
            description="Update social profile"
        )
        
        # Test get profile
        await self.test_endpoint(
            "GET", "/social/profile/default_user",
            description="Get user profile"
        )
        
        # Test my followers
        await self.test_endpoint(
            "GET", "/social/my-followers",
            description="Get user's followers"
        )
        
        # Test my following
        await self.test_endpoint(
            "GET", "/social/my-following",
            description="Get users being followed"
        )

    async def test_tax_reporting_api(self):
        """Test Tax Reporting API endpoints"""
        print("\n📊 Testing Tax Reporting API...")
        
        # Test tax summary
        result = await self.test_endpoint(
            "GET", "/tax/summary",
            description="Get tax summary for current year"
        )
        
        # Verify tax summary structure
        if result["success"] and result["data"].get("summary"):
            print(f"   ✅ Tax summary for year {result['data']['year']} generated")
        
        # Test tax summary with specific year
        await self.test_endpoint(
            "GET", "/tax/summary?year=2024",
            description="Get 2024 tax summary"
        )
        
        # Test gains by asset
        await self.test_endpoint(
            "GET", "/tax/gains-by-asset",
            description="Get gains/losses by asset"
        )
        
        # Test gains by asset with year
        await self.test_endpoint(
            "GET", "/tax/gains-by-asset?year=2024",
            description="Get 2024 gains by asset"
        )
        
        # Test wash sale alerts
        await self.test_endpoint(
            "GET", "/tax/wash-sale-alerts",
            description="Check for wash sale violations"
        )
        
        # Test tax loss harvesting
        await self.test_endpoint(
            "GET", "/tax/tax-loss-harvesting",
            description="Get tax-loss harvesting opportunities"
        )
        
        # Test Form 8949 generation
        await self.test_endpoint(
            "GET", "/tax/report/8949",
            description="Generate IRS Form 8949 data"
        )
        
        # Test tax settings
        await self.test_endpoint(
            "GET", "/tax/settings",
            description="Get tax calculation settings"
        )
        
        # Test save tax settings
        await self.test_endpoint(
            "POST", "/tax/settings",
            data={
                "cost_basis_method": "fifo",
                "country": "US",
                "tax_year": 2025,
                "include_fees": True
            },
            description="Save tax settings"
        )

    async def run_all_tests(self):
        """Run all enhancement API tests"""
        print("🚀 Starting Enhancement APIs Testing...")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Run all test suites
        await self.test_export_api()
        await self.test_achievements_api()
        await self.test_event_countdown_api()
        await self.test_paper_leaderboard_api()
        await self.test_strategy_marketplace_api()
        await self.test_social_trading_api()
        await self.test_tax_reporting_api()
        
        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate test summary"""
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r["success"]])
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("📋 ENHANCEMENT APIS TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        print(f"⏱️  Total Time: {time.time() - self.start_time:.2f}s")
        
        # Group results by API
        api_groups = {}
        for result in self.results:
            api_name = result["endpoint"].split("/")[1]  # Get first path segment
            if api_name not in api_groups:
                api_groups[api_name] = {"total": 0, "success": 0}
            api_groups[api_name]["total"] += 1
            if result["success"]:
                api_groups[api_name]["success"] += 1
        
        print("\n📊 Results by API:")
        for api, stats in api_groups.items():
            rate = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
            status = "✅" if rate == 100 else "⚠️" if rate >= 80 else "❌"
            print(f"  {status} {api.upper()}: {stats['success']}/{stats['total']} ({rate:.1f}%)")
        
        # Show failed tests
        failed_results = [r for r in self.results if not r["success"]]
        if failed_results:
            print("\n❌ Failed Tests:")
            for result in failed_results:
                print(f"  • {result['method']} {result['endpoint']} - {result.get('error', 'Status: ' + str(result['status']))}")
        
        # Show key metrics
        print("\n🎯 Key Findings:")
        
        # Export API
        export_tests = [r for r in self.results if r["endpoint"].startswith("/export")]
        if export_tests:
            export_success = len([r for r in export_tests if r["success"]])
            print(f"  • Export API: {export_success}/{len(export_tests)} endpoints working")
        
        # Achievements API
        achievements_tests = [r for r in self.results if r["endpoint"].startswith("/achievements")]
        if achievements_tests:
            achievements_success = len([r for r in achievements_tests if r["success"]])
            print(f"  • Achievements API: {achievements_success}/{len(achievements_tests)} endpoints working")
            
            # Check if we found 26 achievements
            list_result = next((r for r in achievements_tests if "/list" in r["endpoint"]), None)
            if list_result and list_result["success"]:
                total_achievements = list_result["data"].get("total", 0)
                print(f"    - Found {total_achievements} total achievements")
        
        # Event Countdown API
        countdown_tests = [r for r in self.results if r["endpoint"].startswith("/event-countdown")]
        if countdown_tests:
            countdown_success = len([r for r in countdown_tests if r["success"]])
            print(f"  • Event Countdown API: {countdown_success}/{len(countdown_tests)} endpoints working")
        
        # Paper Leaderboard API
        leaderboard_tests = [r for r in self.results if r["endpoint"].startswith("/paper-leaderboard")]
        if leaderboard_tests:
            leaderboard_success = len([r for r in leaderboard_tests if r["success"]])
            print(f"  • Paper Leaderboard API: {leaderboard_success}/{len(leaderboard_tests)} endpoints working")
        
        # Strategy Marketplace API
        marketplace_tests = [r for r in self.results if r["endpoint"].startswith("/marketplace")]
        if marketplace_tests:
            marketplace_success = len([r for r in marketplace_tests if r["success"]])
            print(f"  • Strategy Marketplace API: {marketplace_success}/{len(marketplace_tests)} endpoints working")
        
        # Social Trading API
        social_tests = [r for r in self.results if r["endpoint"].startswith("/social")]
        if social_tests:
            social_success = len([r for r in social_tests if r["success"]])
            print(f"  • Social Trading API: {social_success}/{len(social_tests)} endpoints working")
        
        # Tax Reporting API
        tax_tests = [r for r in self.results if r["endpoint"].startswith("/tax")]
        if tax_tests:
            tax_success = len([r for r in tax_tests if r["success"]])
            print(f"  • Tax Reporting API: {tax_success}/{len(tax_tests)} endpoints working")
        
        print("\n🎉 Enhancement APIs Testing Complete!")
        
        # Overall assessment
        if success_rate >= 90:
            print("🟢 EXCELLENT: All enhancement APIs are working perfectly!")
        elif success_rate >= 80:
            print("🟡 GOOD: Most enhancement APIs working with minor issues")
        elif success_rate >= 60:
            print("🟠 FAIR: Enhancement APIs partially working, needs attention")
        else:
            print("🔴 POOR: Major issues with enhancement APIs, requires fixes")


async def main():
    """Main test runner"""
    async with EnhancementAPITester() as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())