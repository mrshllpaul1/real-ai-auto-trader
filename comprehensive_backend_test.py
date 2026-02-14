#!/usr/bin/env python3
"""
Comprehensive Backend API Testing
=================================
Testing ALL backend endpoints as requested in the review:
- Core Health & Infrastructure
- Enhanced Event Prediction Coverage 
- Hardened Hidden Gem Prediction
- Adaptive Strategy
- Whale Alerts & Backtesting
- On-Chain Data
- Tethys Trading Engine
- Event Triggers
- Ensemble AI
- Portfolio & Kraken
- Model Training
- MTF Training
- Market Data & Sentiment
- Auto Trading
- Security & Monitoring
- ML Optimization & A/B Testing
- Journal
- Cache

Total: 100+ endpoints to test comprehensively
"""

import requests
import json
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Use production URL from frontend .env
BACKEND_URL = "https://cryptodash-43.preview.emergentagent.com/api"
print(f"🔗 Testing Comprehensive Backend API at: {BACKEND_URL}")

class ComprehensiveBackendTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ComprehensiveBackendTester/1.0'
        })
        self.results = []
        self.failed_tests = []
        self.category_results = {}
        
    def log_result(self, category: str, test_name: str, success: bool, details: str = "", status_code: int = 0):
        """Log test result with category tracking"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} [{category}] {test_name}: {details}")
        
        result = {
            'category': category,
            'test': test_name,
            'success': success,
            'details': details,
            'status_code': status_code,
            'timestamp': datetime.now().isoformat()
        }
        
        self.results.append(result)
        
        # Track by category
        if category not in self.category_results:
            self.category_results[category] = {'passed': 0, 'failed': 0, 'total': 0}
        
        self.category_results[category]['total'] += 1
        if success:
            self.category_results[category]['passed'] += 1
        else:
            self.category_results[category]['failed'] += 1
            self.failed_tests.append(result)
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None, timeout: int = 15) -> tuple:
        """Make HTTP request and return (success, status_code, data)"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method == "GET":
                response = self.session.get(url, params=params, timeout=timeout)
            elif method == "POST":
                response = self.session.post(url, json=data, params=params, timeout=timeout)
            else:
                return False, 0, f"Unsupported method: {method}"
            
            if response.status_code in [200, 201]:
                try:
                    return True, response.status_code, response.json()
                except json.JSONDecodeError:
                    return True, response.status_code, response.text
            else:
                return False, response.status_code, response.text
                
        except requests.exceptions.RequestException as e:
            return False, 0, str(e)
    
    def test_category_1_core_health(self):
        """1. CORE HEALTH & INFRASTRUCTURE"""
        category = "Core Health"
        print(f"\n🏥 CATEGORY 1: {category.upper()}")
        
        # Test health endpoint
        success, status, data = self.make_request("GET", "/health")
        if success and isinstance(data, dict):
            self.log_result(category, "GET /api/health", True, f"Healthy: {data.get('status', 'unknown')}", status)
        else:
            self.log_result(category, "GET /api/health", False, f"HTTP {status}: {data}", status)
        
        # Test root endpoint
        success, status, data = self.make_request("GET", "/")
        if success:
            self.log_result(category, "GET /api/", True, f"Root endpoint working", status)
        else:
            self.log_result(category, "GET /api/", False, f"HTTP {status}: {data}", status)
    
    def test_category_2_enhanced_event_prediction(self):
        """2. ENHANCED EVENT PREDICTION COVERAGE (NEW)"""
        category = "Enhanced Events"
        print(f"\n🎯 CATEGORY 2: {category.upper()}")
        
        # POST predict events with 60 days
        success, status, data = self.make_request(
            "POST", "/adaptive-strategy/predict-events", 
            data={"days_ahead": 60}
        )
        if success and isinstance(data, dict):
            events = data.get("events", [])
            event_types = len(set(e.get("event_type") for e in events))
            details = f"{len(events)} events, {event_types} types, {data.get('high_probability_events', 0)} high-prob"
            meets_req = len(events) >= 20 and event_types >= 20
            self.log_result(category, "POST predict-events (60d)", meets_req, details, status)
        else:
            self.log_result(category, "POST predict-events (60d)", False, f"HTTP {status}: {data}", status)
        
        # GET event coverage stats
        success, status, data = self.make_request("GET", "/adaptive-strategy/event-coverage-stats")
        if success and isinstance(data, dict):
            coverage = data.get("coverage_percentage", 0)
            total_types = data.get("total_event_types_defined", 0)
            details = f"{coverage}% coverage, {total_types} types defined"
            meets_req = coverage >= 60 and total_types >= 20
            self.log_result(category, "GET event-coverage-stats", meets_req, details, status)
        else:
            self.log_result(category, "GET event-coverage-stats", False, f"HTTP {status}: {data}", status)
        
        # GET event calendar
        success, status, data = self.make_request("GET", "/adaptive-strategy/event-calendar", params={"days_ahead": 90})
        if success and isinstance(data, dict):
            calendar = data.get("calendar", {})
            categories = list(calendar.keys())
            scheduled = data.get("scheduled_events_raw", [])
            details = f"{len(scheduled)} scheduled events, categories: {len(categories)}"
            expected_cats = ["scheduled_certain", "highly_likely", "probable", "possible", "monitoring"]
            has_required_cats = all(cat in categories for cat in expected_cats)
            self.log_result(category, "GET event-calendar (90d)", has_required_cats, details, status)
        else:
            self.log_result(category, "GET event-calendar (90d)", False, f"HTTP {status}: {data}", status)
        
        # GET event types
        success, status, data = self.make_request("GET", "/adaptive-strategy/event-types")
        if success and isinstance(data, dict):
            total_types = data.get("total_types", 0)
            event_types = data.get("event_types", [])
            type_names = [et.get("type") for et in event_types]
            new_types = ["token_unlock", "quarterly_earnings", "governance_vote", "airdrop_event", 
                        "geopolitical_event", "protocol_launch", "futures_expiry", "tax_deadline"]
            found_new = [nt for nt in new_types if nt in type_names]
            details = f"{total_types} types, {len(found_new)}/8 new types: {found_new[:4]}..."
            meets_req = total_types >= 27 and len(found_new) >= 6
            self.log_result(category, "GET event-types", meets_req, details, status)
        else:
            self.log_result(category, "GET event-types", False, f"HTTP {status}: {data}", status)
        
        # GET scheduled events
        success, status, data = self.make_request("GET", "/adaptive-strategy/scheduled-events", params={"days_ahead": 90})
        if success and isinstance(data, dict):
            scheduled = data.get("scheduled_events", [])
            total = data.get("total", 0)
            details = f"{total} scheduled events with real dates"
            meets_req = total >= 10
            self.log_result(category, "GET scheduled-events (90d)", meets_req, details, status)
        else:
            self.log_result(category, "GET scheduled-events (90d)", False, f"HTTP {status}: {data}", status)
    
    def test_category_3_hardened_gem_prediction(self):
        """3. HARDENED HIDDEN GEM PREDICTION (NEW)"""
        category = "Hardened Gems"
        print(f"\n💎 CATEGORY 3: {category.upper()}")
        
        # POST gems predict with LLM fields
        success, status, data = self.make_request("POST", "/gems/predict", data={"days_ahead": 7})
        if success and isinstance(data, dict):
            required_fields = ["llm_enhanced", "llm_status", "model_version", "methodology", "generated_at"]
            has_fields = all(field in data for field in required_fields)
            llm_enhanced = data.get("llm_enhanced")
            llm_status = data.get("llm_status", "")
            details = f"llm_enhanced={llm_enhanced}, status={llm_status}, has_required_fields={has_fields}"
            self.log_result(category, "POST gems/predict (LLM fields)", has_fields, details, status)
        else:
            self.log_result(category, "POST gems/predict (LLM fields)", False, f"HTTP {status}: {data}", status)
        
        # POST gems scan
        success, status, data = self.make_request("POST", "/gems/scan", data={"limit": 10})
        if success and isinstance(data, dict):
            gems_found = data.get("gems_found", 0)
            scan_success = data.get("success", False)
            details = f"success={scan_success}, gems_found={gems_found}"
            self.log_result(category, "POST gems/scan", scan_success, details, status)
        else:
            self.log_result(category, "POST gems/scan", False, f"HTTP {status}: {data}", status)
        
        # Additional gem endpoints
        gem_endpoints = [
            "GET /gems/top",
            "GET /gems/history", 
            "GET /gems/training-status",
            "GET /gems/deep-training-status",
            "GET /gems/backtest/status"
        ]
        
        for endpoint_desc in gem_endpoints:
            method, path = endpoint_desc.split(" ", 1)
            success, status, data = self.make_request(method, path)
            self.log_result(category, endpoint_desc, success, f"Response received", status)
    
    def test_category_4_adaptive_strategy(self):
        """4. ADAPTIVE STRATEGY"""
        category = "Adaptive Strategy"
        print(f"\n🎛️ CATEGORY 4: {category.upper()}")
        
        endpoints = [
            "GET /adaptive-strategy/status",
            "GET /adaptive-strategy/regime/current", 
            "GET /adaptive-strategy/optimal-strategy",
            "GET /adaptive-strategy/variants"
        ]
        
        for endpoint_desc in endpoints:
            method, path = endpoint_desc.split(" ", 1)
            success, status, data = self.make_request(method, path)
            self.log_result(category, endpoint_desc, success, f"Response received", status)
        
        # Test predicted events with filter
        success, status, data = self.make_request("GET", "/adaptive-strategy/predicted-events", params={"min_probability": 0.3})
        if success and isinstance(data, dict):
            events = data.get("events", [])
            filtered_count = len([e for e in events if e.get("probability", 0) >= 0.3])
            details = f"{len(events)} events, {filtered_count} with prob ≥ 0.3"
            self.log_result(category, "GET predicted-events (filtered)", True, details, status)
        else:
            self.log_result(category, "GET predicted-events (filtered)", False, f"HTTP {status}: {data}", status)
        
        # Test specific event type endpoints
        event_type_endpoints = [
            "GET /adaptive-strategy/predicted-events/fomc_meeting",
            "GET /adaptive-strategy/predicted-events/token_unlock"
        ]
        
        for endpoint_desc in event_type_endpoints:
            method, path = endpoint_desc.split(" ", 1)
            success, status, data = self.make_request(method, path)
            self.log_result(category, endpoint_desc, success, f"Response received", status)
        
        # Test monitoring endpoints
        monitoring_endpoints = [
            "POST /adaptive-strategy/monitor/start",
            "POST /adaptive-strategy/monitor/stop"
        ]
        
        for endpoint_desc in monitoring_endpoints:
            method, path = endpoint_desc.split(" ", 1)
            success, status, data = self.make_request(method, path, data={})
            self.log_result(category, endpoint_desc, success, f"Response received", status)
    
    def test_category_5_whale_alerts_backtesting(self):
        """5. WHALE ALERTS & BACKTESTING"""
        category = "Whale Alerts"
        print(f"\n🐋 CATEGORY 5: {category.upper()}")
        
        # Whale alert endpoints
        whale_endpoints = [
            ("POST", "/alerts/whale/check", {}),
            ("GET", "/alerts/whale/active", None),
            ("GET", "/alerts/whale/thresholds", None),
            ("POST", "/alerts/whale/monitoring/start", {}),
            ("POST", "/alerts/whale/monitoring/stop", {})
        ]
        
        for method, path, data in whale_endpoints:
            success, status, response = self.make_request(method, path, data=data)
            endpoint_desc = f"{method} {path}"
            if success and isinstance(response, dict):
                if "active" in path and "alerts" in response:
                    alerts_count = len(response.get("alerts", []))
                    details = f"{alerts_count} active alerts found"
                elif "thresholds" in path and "thresholds" in response:
                    threshold_count = len(response.get("thresholds", []))
                    details = f"{threshold_count} thresholds configured"
                else:
                    details = "Response received"
                self.log_result(category, endpoint_desc, True, details, status)
            else:
                self.log_result(category, endpoint_desc, False, f"HTTP {status}: {response}", status)
        
        # Backtest endpoints
        success, status, data = self.make_request("POST", "/alerts/backtest/simulate", data={"n_predictions": 20})
        if success and isinstance(data, dict):
            predictions = data.get("predictions", 0)
            details = f"Simulated {predictions} predictions"
            self.log_result(category, "POST backtest/simulate", True, details, status)
        else:
            self.log_result(category, "POST backtest/simulate", False, f"HTTP {status}: {data}", status)
        
        backtest_endpoints = [
            "GET /alerts/backtest/historical-events",
            "GET /alerts/backtest/accuracy",
            "GET /alerts/backtest/event-types"
        ]
        
        for endpoint_desc in backtest_endpoints:
            method, path = endpoint_desc.split(" ", 1)
            success, status, data = self.make_request(method, path)
            self.log_result(category, endpoint_desc, success, f"Response received", status)
    
    def test_category_6_onchain_data(self):
        """6. ON-CHAIN DATA"""
        category = "On-Chain Data"
        print(f"\n⛓️ CATEGORY 6: {category.upper()}")
        
        onchain_endpoints = [
            "GET /on-chain/whale-activity",
            "GET /on-chain/exchange-flows", 
            "GET /on-chain/whale-transactions",
            "GET /on-chain/network-metrics",
            "GET /on-chain/whale-distribution",
            "GET /on-chain/summary"
        ]
        
        for endpoint_desc in onchain_endpoints:
            method, path = endpoint_desc.split(" ", 1)
            success, status, data = self.make_request(method, path)
            if success and isinstance(data, dict):
                # Check for expected fields based on endpoint
                if "whale-activity" in path:
                    expected_fields = ["whale_sentiment", "accumulation_score", "network_health"]
                elif "exchange-flows" in path:
                    expected_fields = ["inflow", "outflow", "net_flow"]
                elif "network-metrics" in path:
                    expected_fields = ["active_addresses", "hash_rate", "transaction_volume"]
                else:
                    expected_fields = []
                
                if expected_fields:
                    has_fields = all(field in data for field in expected_fields)
                    details = f"Has required fields: {has_fields}"
                else:
                    details = "Response received"
                
                self.log_result(category, endpoint_desc, True, details, status)
            else:
                self.log_result(category, endpoint_desc, False, f"HTTP {status}: {data}", status)
    
    def test_category_7_tethys_trading(self):
        """7. TETHYS TRADING ENGINE"""
        category = "Tethys Trading"
        print(f"\n🤖 CATEGORY 7: {category.upper()}")
        
        # Tethys status
        success, status, data = self.make_request("GET", "/tethys/status")
        self.log_result(category, "GET /tethys/status", success, f"Status check", status)
        
        # Tethys trading controls
        trading_endpoints = [
            ("POST", "/tethys-trading/start", {}),
            ("POST", "/tethys-trading/stop", {}),
            ("GET", "/tethys-trading/status", None),
            ("POST", "/tethys/evaluate", {})
        ]
        
        for method, path, data in trading_endpoints:
            success, status, response = self.make_request(method, path, data=data)
            endpoint_desc = f"{method} {path}"
            self.log_result(category, endpoint_desc, success, f"Response received", status)
    
    def test_category_8_event_triggers(self):
        """8. EVENT TRIGGERS"""
        category = "Event Triggers"
        print(f"\n⚡ CATEGORY 8: {category.upper()}")
        
        # List triggers
        success, status, data = self.make_request("GET", "/triggers/list")
        self.log_result(category, "GET /triggers/list", success, f"Response received", status)
        
        # Create trigger
        trigger_data = {
            "name": "test_trigger",
            "type": "price_alert", 
            "conditions": {
                "coin": "BTC",
                "threshold": 50000
            },
            "actions": ["notify"]
        }
        success, status, data = self.make_request("POST", "/triggers/create", data=trigger_data)
        self.log_result(category, "POST /triggers/create", success, f"Trigger creation", status)
        
        # Other trigger endpoints
        trigger_endpoints = [
            "GET /triggers/history/all",
            "GET /triggers/templates",
            "GET /triggers/status",
            "POST /triggers/check-now"
        ]
        
        for endpoint_desc in trigger_endpoints:
            method, path = endpoint_desc.split(" ", 1)
            data_payload = {} if method == "POST" else None
            success, status, data = self.make_request(method, path, data=data_payload)
            self.log_result(category, endpoint_desc, success, f"Response received", status)
    
    def test_category_9_ensemble_ai(self):
        """9. ENSEMBLE AI"""
        category = "Ensemble AI"
        print(f"\n🧠 CATEGORY 9: {category.upper()}")
        
        ensemble_endpoints = [
            "GET /ensemble/status",
            "GET /ensemble/weights",
            "GET /ensemble/build-status", 
            "GET /ensemble/optimal-universe"
        ]
        
        for endpoint_desc in ensemble_endpoints:
            method, path = endpoint_desc.split(" ", 1)
            success, status, data = self.make_request(method, path)
            if success and isinstance(data, dict):
                if "weights" in path and "weights" in data:
                    weights_count = len(data.get("weights", {}))
                    details = f"{weights_count} model weights"
                elif "status" in path and "status" in data:
                    ensemble_status = data.get("status", "unknown")
                    details = f"Status: {ensemble_status}"
                else:
                    details = "Response received"
                self.log_result(category, endpoint_desc, True, details, status)
            else:
                self.log_result(category, endpoint_desc, False, f"HTTP {status}: {data}", status)
    
    def test_category_10_portfolio_kraken(self):
        """10. PORTFOLIO & KRAKEN"""
        category = "Portfolio & Kraken"
        print(f"\n💰 CATEGORY 10: {category.upper()}")
        
        # Kraken integration
        kraken_endpoints = [
            "GET /kraken/status",
            "GET /kraken/balance"
        ]
        
        for endpoint_desc in kraken_endpoints:
            method, path = endpoint_desc.split(" ", 1)
            success, status, data = self.make_request(method, path)
            if success and isinstance(data, dict):
                if "balance" in path and "total_value" in data:
                    total_value = data.get("total_value", 0)
                    details = f"Total value: ${total_value}"
                elif "status" in path:
                    connected = data.get("connected", False)
                    details = f"Connected: {connected}"
                else:
                    details = "Response received"
                self.log_result(category, endpoint_desc, True, details, status)
            else:
                self.log_result(category, endpoint_desc, False, f"HTTP {status}: {data}", status)
    
    def test_category_11_model_training(self):
        """11. MODEL TRAINING"""
        category = "Model Training"
        print(f"\n🎓 CATEGORY 11: {category.upper()}")
        
        # Enhanced AI training
        success, status, data = self.make_request("POST", "/enhanced-ai/train", data={})
        self.log_result(category, "POST /enhanced-ai/train", success, f"Training initiated", status)
        
        success, status, data = self.make_request("GET", "/enhanced-ai/status")
        self.log_result(category, "GET /enhanced-ai/status", success, f"Status check", status)
        
        # General training
        success, status, data = self.make_request("POST", "/training/train", data={})
        self.log_result(category, "POST /training/train", success, f"Training initiated", status)
        
        success, status, data = self.make_request("GET", "/training/status")
        self.log_result(category, "GET /training/status", success, f"Status check", status)
    
    def test_category_12_mtf_training(self):
        """12. MTF TRAINING"""
        category = "MTF Training"
        print(f"\n📈 CATEGORY 12: {category.upper()}")
        
        # MTF status
        success, status, data = self.make_request("GET", "/mtf-training/status")
        if success and isinstance(data, dict):
            model_status = data.get("status", "unknown")
            details = f"MTF Status: {model_status}"
            self.log_result(category, "GET /mtf-training/status", True, details, status)
        else:
            self.log_result(category, "GET /mtf-training/status", False, f"HTTP {status}: {data}", status)
        
        # MTF prediction for BTC
        success, status, data = self.make_request("POST", "/mtf-training/predict/BTC", data={})
        self.log_result(category, "POST /mtf-training/predict/BTC", success, f"BTC prediction", status)
        
        # Fear & Greed index
        success, status, data = self.make_request("GET", "/mtf-training/fear-greed")
        if success and isinstance(data, dict):
            fear_greed_value = data.get("value", "unknown")
            fear_greed_label = data.get("classification", "unknown")
            details = f"Fear & Greed: {fear_greed_value} ({fear_greed_label})"
            self.log_result(category, "GET /mtf-training/fear-greed", True, details, status)
        else:
            self.log_result(category, "GET /mtf-training/fear-greed", False, f"HTTP {status}: {data}", status)
    
    def test_category_13_market_sentiment(self):
        """13. MARKET DATA & SENTIMENT"""
        category = "Market & Sentiment"
        print(f"\n📊 CATEGORY 13: {category.upper()}")
        
        # Market sentiment
        success, status, data = self.make_request("GET", "/sentiment/market")
        if success and isinstance(data, dict):
            overall_sentiment = data.get("overall_sentiment", "unknown")
            details = f"Market sentiment: {overall_sentiment}"
            self.log_result(category, "GET /sentiment/market", True, details, status)
        else:
            self.log_result(category, "GET /sentiment/market", False, f"HTTP {status}: {data}", status)
        
        # Market prices with coin_ids parameter
        success, status, data = self.make_request("GET", "/market/prices", params={"coin_ids": "bitcoin,ethereum"})
        if success and isinstance(data, dict):
            prices = data.get("prices", {})
            details = f"Prices for {len(prices)} coins"
            self.log_result(category, "GET /market/prices", True, details, status)
        else:
            self.log_result(category, "GET /market/prices", False, f"HTTP {status}: {data}", status)
    
    def test_category_14_auto_trading(self):
        """14. AUTO TRADING"""
        category = "Auto Trading"
        print(f"\n🔄 CATEGORY 14: {category.upper()}")
        
        success, status, data = self.make_request("GET", "/auto-trading/status")
        if success and isinstance(data, dict):
            auto_status = data.get("status", "unknown")
            is_active = data.get("active", False)
            details = f"Status: {auto_status}, Active: {is_active}"
            self.log_result(category, "GET /auto-trading/status", True, details, status)
        else:
            self.log_result(category, "GET /auto-trading/status", False, f"HTTP {status}: {data}", status)
    
    def test_category_15_security_monitoring(self):
        """15. SECURITY & MONITORING"""
        category = "Security & Monitoring"
        print(f"\n🔒 CATEGORY 15: {category.upper()}")
        
        # Error monitoring
        monitoring_endpoints = [
            "GET /monitoring/errors",
            "GET /monitoring/errors/stats", 
            "GET /monitoring/health/detailed"
        ]
        
        for endpoint_desc in monitoring_endpoints:
            method, path = endpoint_desc.split(" ", 1)
            success, status, data = self.make_request(method, path)
            if success and isinstance(data, dict):
                if "errors/stats" in path:
                    total_errors = data.get("total_errors", 0)
                    details = f"{total_errors} errors tracked"
                elif "health/detailed" in path:
                    status_val = data.get("status", "unknown")
                    details = f"Health status: {status_val}"
                else:
                    details = "Response received"
                self.log_result(category, endpoint_desc, True, details, status)
            else:
                self.log_result(category, endpoint_desc, False, f"HTTP {status}: {data}", status)
        
        # Check security headers on health endpoint
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            security_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options",
                "X-XSS-Protection",
                "Strict-Transport-Security"
            ]
            found_headers = [h for h in security_headers if h in response.headers]
            details = f"{len(found_headers)}/4 security headers found: {found_headers}"
            self.log_result(category, "Security Headers Check", len(found_headers) >= 2, details, response.status_code)
        except Exception as e:
            self.log_result(category, "Security Headers Check", False, f"Error: {str(e)}", 0)
    
    def test_category_16_ml_optimization(self):
        """16. ML OPTIMIZATION & A/B TESTING"""
        category = "ML Optimization"
        print(f"\n🧪 CATEGORY 16: {category.upper()}")
        
        # ML optimization status
        success, status, data = self.make_request("GET", "/ml/optimization/status")
        self.log_result(category, "GET /ml/optimization/status", success, f"Response received", status)
        
        # A/B testing
        success, status, data = self.make_request("POST", "/ml/optimization/ab-test/init", data={})
        self.log_result(category, "POST /ml/optimization/ab-test/init", success, f"A/B test init", status)
        
        success, status, data = self.make_request("GET", "/ml/ab-test/variants")
        self.log_result(category, "GET /ml/ab-test/variants", success, f"Response received", status)
    
    def test_category_17_journal(self):
        """17. JOURNAL"""
        category = "Journal"
        print(f"\n📝 CATEGORY 17: {category.upper()}")
        
        success, status, data = self.make_request("GET", "/journal/entries")
        if success and isinstance(data, dict):
            entries = data.get("entries", [])
            details = f"{len(entries)} journal entries"
            self.log_result(category, "GET /journal/entries", True, details, status)
        else:
            self.log_result(category, "GET /journal/entries", False, f"HTTP {status}: {data}", status)
    
    def test_category_18_cache(self):
        """18. CACHE"""
        category = "Cache"
        print(f"\n💾 CATEGORY 18: {category.upper()}")
        
        success, status, data = self.make_request("GET", "/cache/stats")
        if success and isinstance(data, dict):
            cache_hits = data.get("cache_hits", 0)
            cache_misses = data.get("cache_misses", 0)
            details = f"Hits: {cache_hits}, Misses: {cache_misses}"
            self.log_result(category, "GET /cache/stats", True, details, status)
        else:
            self.log_result(category, "GET /cache/stats", False, f"HTTP {status}: {data}", status)
    
    def run_comprehensive_tests(self):
        """Run all comprehensive backend tests"""
        print("=" * 100)
        print("🚀 COMPREHENSIVE BACKEND API TESTING - ALL SYSTEMS")
        print("=" * 100)
        
        start_time = time.time()
        
        # Run all test categories
        test_categories = [
            self.test_category_1_core_health,
            self.test_category_2_enhanced_event_prediction,
            self.test_category_3_hardened_gem_prediction,
            self.test_category_4_adaptive_strategy,
            self.test_category_5_whale_alerts_backtesting,
            self.test_category_6_onchain_data,
            self.test_category_7_tethys_trading,
            self.test_category_8_event_triggers,
            self.test_category_9_ensemble_ai,
            self.test_category_10_portfolio_kraken,
            self.test_category_11_model_training,
            self.test_category_12_mtf_training,
            self.test_category_13_market_sentiment,
            self.test_category_14_auto_trading,
            self.test_category_15_security_monitoring,
            self.test_category_16_ml_optimization,
            self.test_category_17_journal,
            self.test_category_18_cache
        ]
        
        for test_func in test_categories:
            try:
                test_func()
                time.sleep(0.5)  # Brief pause between categories
            except Exception as e:
                category_name = test_func.__doc__.split('.')[1].split('(')[0].strip()
                self.log_result("ERROR", f"Category {category_name}", False, f"Exception: {str(e)}", 0)
        
        end_time = time.time()
        test_duration = end_time - start_time
        
        # Generate comprehensive results summary
        self.generate_comprehensive_summary(test_duration)
        
        return len(self.failed_tests) == 0
    
    def generate_comprehensive_summary(self, test_duration: float):
        """Generate comprehensive test results summary"""
        print("\n" + "=" * 100)
        print("📊 COMPREHENSIVE BACKEND API TEST RESULTS")
        print("=" * 100)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 OVERALL RESULTS:")
        print(f"   ✅ Total Tests: {total_tests}")
        print(f"   🎯 Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   ⏱️  Duration: {test_duration:.1f}s")
        
        print(f"\n📋 PER-CATEGORY BREAKDOWN:")
        for category, stats in self.category_results.items():
            category_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            status_emoji = "✅" if category_rate >= 80 else "⚠️" if category_rate >= 60 else "❌"
            print(f"   {status_emoji} {category:<20}: {category_rate:5.1f}% ({stats['passed']}/{stats['total']})")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS DETAILS:")
            for i, failure in enumerate(self.failed_tests[:10], 1):  # Show first 10 failures
                print(f"   {i}. [{failure['category']}] {failure['test']}")
                print(f"      └─ {failure['details']}")
            
            if len(self.failed_tests) > 10:
                print(f"   ... and {len(self.failed_tests) - 10} more failures")
        
        # System assessment
        print(f"\n🎯 SYSTEM ASSESSMENT:")
        if success_rate >= 90:
            print("   🎉 EXCELLENT: Backend API is production-ready!")
        elif success_rate >= 80:
            print("   ✅ GOOD: Backend API is mostly functional with minor issues")
        elif success_rate >= 70:
            print("   ⚠️  MODERATE: Backend API needs some fixes")
        elif success_rate >= 50:
            print("   🔧 NEEDS WORK: Backend API has significant issues")
        else:
            print("   ❌ CRITICAL: Backend API requires major fixes")
        
        # Critical systems check
        critical_categories = ["Core Health", "Tethys Trading", "Portfolio & Kraken", "Event Triggers"]
        critical_status = []
        for cat in critical_categories:
            if cat in self.category_results:
                stats = self.category_results[cat]
                rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
                critical_status.append((cat, rate >= 80))
        
        all_critical_working = all(status for _, status in critical_status)
        critical_emoji = "🟢" if all_critical_working else "🔴"
        print(f"   {critical_emoji} Critical Systems: {'All Working' if all_critical_working else 'Issues Found'}")
        
        print("=" * 100)


if __name__ == "__main__":
    tester = ComprehensiveBackendTester()
    success = tester.run_comprehensive_tests()
    
    if success:
        print("🎯 Comprehensive backend testing completed successfully!")
        sys.exit(0)
    else:
        print("⚠️ Comprehensive backend testing completed with issues.")
        sys.exit(1)