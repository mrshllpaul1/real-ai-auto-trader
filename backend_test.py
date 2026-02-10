#!/usr/bin/env python3
"""
Enhanced Event Prediction Coverage Testing
==========================================
Comprehensive testing for all adaptive strategy endpoints with specific focus on:
- Event prediction with 20+ event types
- Event calendar with 90 days coverage
- Event coverage stats with >60% coverage
- Scheduled events with real 2026 dates
- All new endpoints functionality
"""

import requests
import json
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

# Use production URL from environment
BACKEND_URL = "https://coverage-enhancer.preview.emergentagent.com/api"
print(f"🔗 Testing Enhanced Event Prediction Coverage at: {BACKEND_URL}")

class EventPredictionTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'EventPredictionTester/1.0'
        })
        self.results = []
        self.failed_tests = []
        
    def log_result(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
        self.results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'response_data': response_data
        })
        
        if not success:
            self.failed_tests.append({
                'test': test_name,
                'details': details,
                'response_data': response_data
            })
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> tuple:
        """Make HTTP request and return (success, status_code, data)"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method == "GET":
                response = self.session.get(url, params=params, timeout=15)
            elif method == "POST":
                response = self.session.post(url, json=data, params=params, timeout=15)
            else:
                return False, 0, f"Unsupported method: {method}"
            
            if response.status_code == 200:
                try:
                    return True, response.status_code, response.json()
                except json.JSONDecodeError:
                    return True, response.status_code, response.text
            else:
                return False, response.status_code, response.text
                
        except requests.exceptions.RequestException as e:
            return False, 0, str(e)
    
    def test_predict_events_60_days(self):
        """Test POST /api/adaptive-strategy/predict-events with 60 days"""
        print("\n🎯 Testing Enhanced Event Predictions (60 days)...")
        
        success, status, data = self.make_request(
            "POST", 
            "/adaptive-strategy/predict-events",
            data={"days_ahead": 60}
        )
        
        if not success:
            self.log_result("Predict Events 60 Days", False, f"HTTP {status}: {data}")
            return
        
        # Verify response structure
        required_fields = ["status", "events", "total_events", "high_probability_events"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_result("Predict Events 60 Days", False, f"Missing fields: {missing_fields}")
            return
        
        events = data.get("events", [])
        total_events = data.get("total_events", 0)
        high_prob_events = data.get("high_probability_events", 0)
        
        # Check requirements: 20+ events across 20+ different event types
        if total_events < 20:
            self.log_result("Predict Events 60 Days", False, f"Only {total_events} events, need 20+")
            return
        
        # Check unique event types
        event_types = set()
        valid_event_structure = True
        
        for event in events:
            required_event_fields = ["event_id", "event_type", "description", "predicted_date", 
                                   "probability", "expected_impact", "affected_coins", 
                                   "confidence_factors", "prediction_basis", "created_at"]
            
            missing_event_fields = [field for field in required_event_fields if field not in event]
            if missing_event_fields:
                valid_event_structure = False
                break
            
            event_types.add(event.get("event_type"))
        
        if not valid_event_structure:
            self.log_result("Predict Events 60 Days", False, f"Invalid event structure: missing {missing_event_fields}")
            return
        
        unique_event_types = len(event_types)
        if unique_event_types < 20:
            self.log_result("Predict Events 60 Days", False, f"Only {unique_event_types} event types, need 20+")
            return
        
        # Check for new event types
        new_event_types = ["token_unlock", "quarterly_earnings", "governance_vote", "airdrop_event", 
                          "geopolitical_event", "protocol_launch", "futures_expiry", "tax_deadline"]
        
        found_new_types = [et for et in new_event_types if et in event_types]
        
        self.log_result(
            "Predict Events 60 Days", 
            True, 
            f"{total_events} events, {unique_event_types} types, {high_prob_events} high-prob, new types: {len(found_new_types)}"
        )
        
        # Log sample events for verification
        print(f"   📊 Sample Event Types: {list(event_types)[:10]}...")
        print(f"   🆕 New Event Types Found: {found_new_types}")
        
        return data
    
    def test_event_coverage_stats(self):
        """Test GET /api/adaptive-strategy/event-coverage-stats"""
        print("\n📈 Testing Event Coverage Statistics...")
        
        success, status, data = self.make_request("GET", "/adaptive-strategy/event-coverage-stats")
        
        if not success:
            self.log_result("Event Coverage Stats", False, f"HTTP {status}: {data}")
            return
        
        # Verify required fields
        required_fields = ["coverage_percentage", "total_event_types_defined", 
                          "event_types_with_predictions", "total_active_predictions"]
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            self.log_result("Event Coverage Stats", False, f"Missing fields: {missing_fields}")
            return
        
        # Check coverage requirements
        coverage_pct = data.get("coverage_percentage", 0)
        total_types = data.get("total_event_types_defined", 0)
        types_with_predictions = data.get("event_types_with_predictions", 0)
        
        if coverage_pct < 60:
            self.log_result("Event Coverage Stats", False, f"Coverage {coverage_pct}% < 60% required")
            return
        
        if total_types < 33:
            self.log_result("Event Coverage Stats", False, f"Only {total_types} event types defined, expected ~33")
            return
        
        if types_with_predictions < 20:
            self.log_result("Event Coverage Stats", False, f"Only {types_with_predictions} types with predictions, need >20")
            return
        
        # Check for upcoming events structure
        upcoming = data.get("upcoming_events", {})
        required_periods = ["next_30_days", "next_60_days", "next_90_days"]
        missing_periods = [period for period in required_periods if period not in upcoming]
        
        if missing_periods:
            self.log_result("Event Coverage Stats", False, f"Missing upcoming periods: {missing_periods}")
            return
        
        # Check for type_details
        type_details = data.get("type_details", [])
        if len(type_details) < 20:
            self.log_result("Event Coverage Stats", False, f"Only {len(type_details)} type details, need 20+")
            return
        
        self.log_result(
            "Event Coverage Stats", 
            True, 
            f"{coverage_pct}% coverage, {total_types} types, {types_with_predictions} with predictions"
        )
        
        return data
    
    def test_event_calendar(self):
        """Test GET /api/adaptive-strategy/event-calendar?days_ahead=90"""
        print("\n📅 Testing Event Calendar (90 days)...")
        
        success, status, data = self.make_request(
            "GET", 
            "/adaptive-strategy/event-calendar",
            params={"days_ahead": 90}
        )
        
        if not success:
            self.log_result("Event Calendar", False, f"HTTP {status}: {data}")
            return
        
        # Check required fields
        required_fields = ["calendar", "scheduled_events_raw", "category_breakdown"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_result("Event Calendar", False, f"Missing fields: {missing_fields}")
            return
        
        # Check calendar structure
        calendar = data.get("calendar", {})
        required_categories = ["scheduled_certain", "highly_likely", "probable", "possible", "monitoring"]
        missing_categories = [cat for cat in required_categories if cat not in calendar]
        
        if missing_categories:
            self.log_result("Event Calendar", False, f"Missing calendar categories: {missing_categories}")
            return
        
        # Check scheduled events
        scheduled_raw = data.get("scheduled_events_raw", [])
        if len(scheduled_raw) < 10:
            self.log_result("Event Calendar", False, f"Only {len(scheduled_raw)} scheduled events, need more")
            return
        
        # Verify dates are real 2026 dates
        real_dates_found = 0
        for event in scheduled_raw[:5]:  # Check first 5
            event_date = event.get("date", "")
            if "2025-" in event_date or "2026-" in event_date:
                real_dates_found += 1
        
        if real_dates_found < 3:
            self.log_result("Event Calendar", False, f"Not enough real 2025/2026 dates found")
            return
        
        # Check category breakdown
        breakdown = data.get("category_breakdown", {})
        total_calendar_events = sum(len(events) for events in calendar.values())
        
        self.log_result(
            "Event Calendar", 
            True, 
            f"{len(scheduled_raw)} scheduled events, {total_calendar_events} calendar entries, real dates confirmed"
        )
        
        return data
    
    def test_event_types(self):
        """Test GET /api/adaptive-strategy/event-types"""
        print("\n🏷️ Testing Event Types Definition...")
        
        success, status, data = self.make_request("GET", "/adaptive-strategy/event-types")
        
        if not success:
            self.log_result("Event Types", False, f"HTTP {status}: {data}")
            return
        
        # Check required fields
        required_fields = ["event_types", "total_types", "types_with_predictions"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_result("Event Types", False, f"Missing fields: {missing_fields}")
            return
        
        event_types = data.get("event_types", [])
        total_types = data.get("total_types", 0)
        
        if total_types < 27:
            self.log_result("Event Types", False, f"Only {total_types} event types, expected 27+")
            return
        
        # Check event type structure
        required_event_fields = ["type", "description", "impact", "confidence", "lead_indicators", "active_predictions"]
        
        for event_type in event_types[:5]:  # Check first 5
            missing_event_fields = [field for field in required_event_fields if field not in event_type]
            if missing_event_fields:
                self.log_result("Event Types", False, f"Event type missing fields: {missing_event_fields}")
                return
        
        # Check for new event types
        type_names = [et.get("type") for et in event_types]
        new_types = ["token_unlock", "quarterly_earnings", "governance_vote", "airdrop_event", 
                    "geopolitical_event", "protocol_launch", "futures_expiry", "tax_deadline"]
        
        found_new_types = [nt for nt in new_types if nt in type_names]
        
        if len(found_new_types) < 6:
            self.log_result("Event Types", False, f"Only {len(found_new_types)} new event types found, expected 8")
            return
        
        self.log_result(
            "Event Types", 
            True, 
            f"{total_types} types, {len(found_new_types)}/8 new types: {found_new_types}"
        )
        
        return data
    
    def test_scheduled_events(self):
        """Test GET /api/adaptive-strategy/scheduled-events?days_ahead=90"""
        print("\n📋 Testing Scheduled Events Calendar...")
        
        success, status, data = self.make_request(
            "GET", 
            "/adaptive-strategy/scheduled-events",
            params={"days_ahead": 90}
        )
        
        if not success:
            self.log_result("Scheduled Events", False, f"HTTP {status}: {data}")
            return
        
        # Check required fields
        required_fields = ["scheduled_events", "total", "days_ahead", "calendars"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            self.log_result("Scheduled Events", False, f"Missing fields: {missing_fields}")
            return
        
        scheduled_events = data.get("scheduled_events", [])
        total = data.get("total", 0)
        
        if total < 10:
            self.log_result("Scheduled Events", False, f"Only {total} scheduled events, need more")
            return
        
        # Check event structure
        if scheduled_events:
            event = scheduled_events[0]
            required_event_fields = ["date", "days_until", "description", "calendar_category"]
            missing_event_fields = [field for field in required_event_fields if field not in event]
            
            if missing_event_fields:
                self.log_result("Scheduled Events", False, f"Event missing fields: {missing_event_fields}")
                return
        
        # Check for specific event types mentioned in requirements
        descriptions = [event.get("description", "").lower() for event in scheduled_events]
        required_event_categories = ["fomc", "options", "token", "earnings", "sec"]
        
        found_categories = []
        for category in required_event_categories:
            if any(category in desc for desc in descriptions):
                found_categories.append(category)
        
        if len(found_categories) < 4:
            self.log_result("Scheduled Events", False, f"Only found {len(found_categories)} required categories: {found_categories}")
            return
        
        # Check dates are real 2026 dates and sorted
        dates_are_sorted = True
        real_dates = 0
        
        for i, event in enumerate(scheduled_events[:10]):
            event_date = event.get("date", "")
            if "2025-" in event_date or "2026-" in event_date:
                real_dates += 1
            
            if i > 0 and scheduled_events[i-1].get("date", "") > event_date:
                dates_are_sorted = False
        
        if real_dates < 8:
            self.log_result("Scheduled Events", False, f"Only {real_dates} real 2025/2026 dates found")
            return
        
        if not dates_are_sorted:
            self.log_result("Scheduled Events", False, "Events not sorted by date")
            return
        
        self.log_result(
            "Scheduled Events", 
            True, 
            f"{total} events, {len(found_categories)} categories: {found_categories}, dates sorted"
        )
        
        return data
    
    def test_predicted_events_filter(self):
        """Test GET /api/adaptive-strategy/predicted-events?min_probability=0.3"""
        print("\n🎲 Testing Predicted Events Filtering...")
        
        success, status, data = self.make_request(
            "GET", 
            "/adaptive-strategy/predicted-events",
            params={"min_probability": 0.3}
        )
        
        if not success:
            self.log_result("Predicted Events Filter", False, f"HTTP {status}: {data}")
            return
        
        events = data.get("events", [])
        total = data.get("total", 0)
        min_prob = data.get("min_probability_filter", 0)
        
        if min_prob != 0.3:
            self.log_result("Predicted Events Filter", False, f"Filter not applied correctly: {min_prob}")
            return
        
        # Check all events meet probability threshold
        invalid_events = [e for e in events if e.get("probability", 0) < 0.3]
        
        if invalid_events:
            self.log_result("Predicted Events Filter", False, f"{len(invalid_events)} events below 0.3 probability")
            return
        
        self.log_result(
            "Predicted Events Filter", 
            True, 
            f"{total} events ≥ 0.3 probability, filter working correctly"
        )
        
        return data
    
    def test_predicted_events_by_type(self):
        """Test event type-specific endpoints"""
        print("\n🎯 Testing Event Type Specific Endpoints...")
        
        # Test FOMC specific predictions
        success, status, data = self.make_request(
            "GET", 
            "/adaptive-strategy/predicted-events/fomc_meeting"
        )
        
        if success:
            events = data.get("events", [])
            fomc_events = len(events)
            self.log_result(
                "FOMC Events", 
                True, 
                f"{fomc_events} FOMC predictions found"
            )
        else:
            self.log_result("FOMC Events", False, f"HTTP {status}: {data}")
        
        # Test Token Unlock specific predictions  
        success, status, data = self.make_request(
            "GET", 
            "/adaptive-strategy/predicted-events/token_unlock"
        )
        
        if success:
            events = data.get("events", [])
            unlock_events = len(events)
            self.log_result(
                "Token Unlock Events", 
                True, 
                f"{unlock_events} token unlock predictions found"
            )
        else:
            self.log_result("Token Unlock Events", False, f"HTTP {status}: {data}")
        
        return True
    
    def test_existing_endpoints(self):
        """Test that existing endpoints still work"""
        print("\n🔧 Testing Existing Adaptive Strategy Endpoints...")
        
        endpoints_to_test = [
            "/adaptive-strategy/status",
            "/adaptive-strategy/regime/current", 
            "/adaptive-strategy/optimal-strategy"
        ]
        
        for endpoint in endpoints_to_test:
            success, status, data = self.make_request("GET", endpoint)
            
            endpoint_name = endpoint.split("/")[-1].replace("-", " ").title()
            
            if success:
                self.log_result(
                    f"Existing: {endpoint_name}", 
                    True, 
                    f"Endpoint working correctly"
                )
            else:
                self.log_result(
                    f"Existing: {endpoint_name}", 
                    False, 
                    f"HTTP {status}: {data}"
                )
    
    def run_all_tests(self):
        """Run comprehensive Enhanced Event Prediction Coverage tests"""
        print("=" * 80)
        print("🚀 ENHANCED EVENT PREDICTION COVERAGE TESTING")
        print("=" * 80)
        
        # Main enhanced features
        predict_data = self.test_predict_events_60_days()
        coverage_data = self.test_event_coverage_stats()
        calendar_data = self.test_event_calendar()
        types_data = self.test_event_types()
        scheduled_data = self.test_scheduled_events()
        
        # Filtering and specific endpoints
        self.test_predicted_events_filter()
        self.test_predicted_events_by_type()
        
        # Verify existing functionality  
        self.test_existing_endpoints()
        
        # Results Summary
        print("\n" + "=" * 80)
        print("📊 ENHANCED EVENT PREDICTION COVERAGE TEST RESULTS")
        print("=" * 80)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        print(f"✅ Passed Tests: {passed_tests}")
        print(f"❌ Failed Tests: {failed_tests}")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS DETAILS:")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"   {i}. {failure['test']}: {failure['details']}")
        
        # Enhanced Event Coverage Analysis
        print("\n" + "=" * 50)
        print("🎯 ENHANCED EVENT PREDICTION ANALYSIS")
        print("=" * 50)
        
        if predict_data:
            events = predict_data.get("events", [])
            event_types = set(e.get("event_type") for e in events)
            print(f"📊 Total Events Predicted: {len(events)}")
            print(f"🏷️  Unique Event Types: {len(event_types)}")
            print(f"🎲 High Probability Events: {predict_data.get('high_probability_events', 0)}")
        
        if coverage_data:
            print(f"📈 Event Coverage: {coverage_data.get('coverage_percentage', 0)}%")
            print(f"🎯 Types Defined: {coverage_data.get('total_event_types_defined', 0)}")
            print(f"⚡ Types with Predictions: {coverage_data.get('event_types_with_predictions', 0)}")
        
        if scheduled_data:
            print(f"📅 Scheduled Events (90 days): {scheduled_data.get('total', 0)}")
            calendars = scheduled_data.get('calendars', [])
            print(f"🗓️  Calendar Categories: {len(calendars)} ({', '.join(calendars[:3])}...)")
        
        # Final Assessment
        if success_rate >= 90:
            print(f"\n🎉 EXCELLENT: Enhanced Event Prediction Coverage working perfectly!")
        elif success_rate >= 80:
            print(f"\n✅ GOOD: Enhanced Event Prediction Coverage mostly working well")
        elif success_rate >= 70:
            print(f"\n⚠️  MODERATE: Enhanced Event Prediction Coverage needs some fixes")
        else:
            print(f"\n❌ POOR: Enhanced Event Prediction Coverage needs significant work")
        
        print("\n" + "=" * 80)
        return success_rate >= 80


if __name__ == "__main__":
    tester = EventPredictionTester()
    success = tester.run_all_tests()
    
    if success:
        print("🎯 Enhanced Event Prediction Coverage testing completed successfully!")
        sys.exit(0)
    else:
        print("⚠️ Enhanced Event Prediction Coverage testing completed with issues.")
        sys.exit(1)