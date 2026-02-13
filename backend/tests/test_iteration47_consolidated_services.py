"""
Iteration 47 Tests - Consolidated Services & AI Confidence Explanation
======================================================================
Tests for:
1. Consolidated Services API at /api/services/status (10 services from 141)
2. AI Confidence Explanation at /api/confidence-explain/BTC
3. AI Confidence Explanation feature-importance endpoint
4. ML frameworks availability check
5. Kraken portfolio data loads
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestConsolidatedServicesAPI:
    """Test consolidated services API - reduced from 141 to 10 services"""
    
    def test_services_status_endpoint(self):
        """Test /api/services/status returns all 10 consolidated services"""
        response = requests.get(f"{BASE_URL}/api/services/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify consolidation info
        assert "consolidation" in data
        assert data["consolidation"]["original_services"] == 141
        assert data["consolidation"]["consolidated_services"] == 10
        assert data["consolidation"]["reduction"] == "93%"
        
        # Verify all 10 services are present
        services = data.get("services", {})
        expected_services = [
            "exchange", "ai", "analysis", "sentiment", "trading",
            "ml", "data", "strategy", "notification", "system"
        ]
        for service in expected_services:
            assert service in services, f"Missing service: {service}"
            assert "service" in services[service], f"Service {service} missing 'service' field"
        
        print(f"✓ All 10 consolidated services present")
        print(f"✓ Consolidation: {data['consolidation']}")
    
    def test_ml_status_endpoint(self):
        """Test /api/services/ml/status returns ML frameworks"""
        response = requests.get(f"{BASE_URL}/api/services/ml/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify ML frameworks
        assert "status" in data
        assert "available_models" in data
        
        expected_frameworks = ["tensorflow", "pytorch", "sb3", "sklearn", "xgboost", "lightgbm"]
        available = data.get("available_models", [])
        
        for framework in expected_frameworks:
            assert framework in available, f"Missing ML framework: {framework}"
        
        print(f"✓ ML frameworks available: {available}")


class TestAIConfidenceExplanation:
    """Test AI Confidence Explanation feature"""
    
    def test_confidence_explain_btc(self):
        """Test /api/confidence-explain/BTC returns explanation"""
        response = requests.get(f"{BASE_URL}/api/confidence-explain/BTC")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify required fields
        required_fields = [
            "symbol", "confidence", "signal", "explanation", "summary",
            "key_drivers", "breakdown", "contributions", "agreement_score",
            "confidence_level", "timestamp"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify data types
        assert data["symbol"] == "BTC"
        assert 0 <= data["confidence"] <= 1
        assert data["signal"] in ["buy", "sell", "hold", "strong_buy", "strong_sell"]
        assert isinstance(data["explanation"], str)
        assert isinstance(data["key_drivers"], list)
        assert len(data["key_drivers"]) > 0
        
        # Verify key drivers structure
        for driver in data["key_drivers"]:
            assert "category" in driver
            assert "feature" in driver
            assert "contribution" in driver
            assert "direction" in driver
            assert "explanation" in driver
        
        print(f"✓ BTC confidence explanation: {data['signal']} ({data['confidence']*100:.0f}%)")
        print(f"✓ Key drivers: {len(data['key_drivers'])}")
        print(f"✓ Agreement score: {data['agreement_score']}%")
    
    def test_confidence_explain_eth(self):
        """Test /api/confidence-explain/ETH returns explanation"""
        response = requests.get(f"{BASE_URL}/api/confidence-explain/ETH")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["symbol"] == "ETH"
        assert "explanation" in data
        print(f"✓ ETH confidence explanation: {data['signal']} ({data['confidence']*100:.0f}%)")
    
    def test_feature_importance_endpoint(self):
        """Test /api/confidence-explain/feature-importance returns weights"""
        response = requests.get(f"{BASE_URL}/api/confidence-explain/feature-importance")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify structure
        assert "by_category" in data
        assert "ranked" in data
        assert "total_features" in data
        
        # Verify categories
        categories = data["by_category"]
        expected_categories = ["technical", "sentiment", "on_chain", "market_structure"]
        for cat in expected_categories:
            assert cat in categories, f"Missing category: {cat}"
        
        # Verify ranked features
        ranked = data["ranked"]
        assert len(ranked) > 0
        assert ranked[0]["importance"] >= ranked[-1]["importance"]  # Sorted descending
        
        print(f"✓ Total features: {data['total_features']}")
        print(f"✓ Top feature: {ranked[0]['feature']} ({ranked[0]['importance_pct']})")
    
    def test_confidence_explain_status(self):
        """Test /api/confidence-explain/ status endpoint"""
        response = requests.get(f"{BASE_URL}/api/confidence-explain/")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "status" in data
        assert "features" in data
        assert "supported_categories" in data
        
        print(f"✓ Explanation service status: {data['status']}")


class TestKrakenPortfolioData:
    """Test Kraken portfolio data loading"""
    
    def test_spot_balance_endpoint(self):
        """Test /api/spot/balance returns real Kraken data"""
        response = requests.get(f"{BASE_URL}/api/spot/balance")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify required fields
        required_fields = [
            "holdings", "usd_balance", "total_crypto_value",
            "total_portfolio_value", "holdings_count"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify holdings structure
        holdings = data.get("holdings", [])
        assert len(holdings) > 0, "No holdings found"
        
        for holding in holdings:
            assert "symbol" in holding
            assert "amount" in holding
            assert "usd_value" in holding
        
        print(f"✓ USD Balance: ${data['usd_balance']:.2f}")
        print(f"✓ Crypto Value: ${data['total_crypto_value']:.2f}")
        print(f"✓ Portfolio Total: ${data['total_portfolio_value']:.2f}")
        print(f"✓ Holdings count: {data['holdings_count']}")
    
    def test_spot_pairs_endpoint(self):
        """Test /api/spot/pairs returns trading pairs"""
        response = requests.get(f"{BASE_URL}/api/spot/pairs")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "pairs" in data
        
        pairs = data["pairs"]
        assert len(pairs) > 0, "No trading pairs found"
        
        # Verify pair structure
        for pair in pairs[:3]:  # Check first 3
            assert "symbol" in pair
            assert "price" in pair
        
        print(f"✓ Trading pairs available: {len(pairs)}")
    
    def test_spot_pair_btc_details(self):
        """Test /api/spot/pair/BTC returns BTC details with AI signal"""
        response = requests.get(f"{BASE_URL}/api/spot/pair/BTC")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        assert "symbol" in data
        assert data["symbol"] == "BTC"
        assert "price" in data
        
        # Check for AI signal
        if "ai_signal" in data:
            ai_signal = data["ai_signal"]
            print(f"✓ BTC AI Signal: {ai_signal.get('signal', 'N/A')}")
            print(f"✓ BTC Confidence: {ai_signal.get('confidence', 0):.0f}%")
        
        print(f"✓ BTC Price: ${data['price'].get('last', 0):,.2f}")


class TestHealthAndBasicEndpoints:
    """Test basic health and status endpoints"""
    
    def test_health_endpoint(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("status") == "healthy"
        assert data.get("database") == "connected"
        
        print(f"✓ Health status: {data['status']}")
    
    def test_spot_status_endpoint(self):
        """Test /api/spot/status returns trading status"""
        response = requests.get(f"{BASE_URL}/api/spot/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "budget" in data or "status" in data
        
        print(f"✓ Spot trading status retrieved")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
