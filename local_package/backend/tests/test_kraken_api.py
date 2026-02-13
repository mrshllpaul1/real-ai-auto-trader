"""
Kraken API Integration Tests
Tests for Kraken exchange connectivity, balance, ticker, and auto-trader functionality.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestKrakenStatus:
    """Tests for /api/kraken/status endpoint - Kraken connection and authentication"""
    
    def test_kraken_status_connected(self):
        """Verify Kraken API is connected"""
        response = requests.get(f"{BASE_URL}/api/kraken/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("connected") == True, f"Expected connected=True, got {data.get('connected')}"
    
    def test_kraken_status_authenticated(self):
        """Verify Kraken API keys are valid and authenticated"""
        response = requests.get(f"{BASE_URL}/api/kraken/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("authenticated") == True, f"Expected authenticated=True, got {data.get('authenticated')}"
    
    def test_kraken_status_trading_enabled(self):
        """Verify trading is enabled"""
        response = requests.get(f"{BASE_URL}/api/kraken/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("trading_enabled") == True, f"Expected trading_enabled=True, got {data.get('trading_enabled')}"
    
    def test_kraken_status_has_btc_price(self):
        """Verify BTC price is returned"""
        response = requests.get(f"{BASE_URL}/api/kraken/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "btc_price" in data, "Expected btc_price in response"
        assert data["btc_price"] > 0, f"Expected positive BTC price, got {data['btc_price']}"
    
    def test_kraken_status_has_isolated_budget(self):
        """Verify isolated budget is returned"""
        response = requests.get(f"{BASE_URL}/api/kraken/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "isolated_budget" in data, "Expected isolated_budget in response"
        assert data["isolated_budget"] == 500.0, f"Expected isolated_budget=500, got {data['isolated_budget']}"


class TestKrakenBalance:
    """Tests for /api/kraken/balance endpoint - Real Kraken account balances"""
    
    def test_kraken_balance_returns_200(self):
        """Verify balance endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/kraken/balance")
        assert response.status_code == 200
    
    def test_kraken_balance_has_balances(self):
        """Verify balances object is returned"""
        response = requests.get(f"{BASE_URL}/api/kraken/balance")
        assert response.status_code == 200
        
        data = response.json()
        assert "balances" in data, "Expected balances in response"
        assert isinstance(data["balances"], dict), "Expected balances to be a dict"
    
    def test_kraken_balance_has_btc(self):
        """Verify BTC balance exists (XXBT)"""
        response = requests.get(f"{BASE_URL}/api/kraken/balance")
        assert response.status_code == 200
        
        data = response.json()
        balances = data.get("balances", {})
        assert "XXBT" in balances, "Expected XXBT (Bitcoin) in balances"
        assert balances["XXBT"]["amount"] > 0, "Expected positive BTC balance"
    
    def test_kraken_balance_has_eth(self):
        """Verify ETH balance exists (XETH)"""
        response = requests.get(f"{BASE_URL}/api/kraken/balance")
        assert response.status_code == 200
        
        data = response.json()
        balances = data.get("balances", {})
        assert "XETH" in balances, "Expected XETH (Ethereum) in balances"
        assert balances["XETH"]["amount"] > 0, "Expected positive ETH balance"
    
    def test_kraken_balance_has_sol(self):
        """Verify SOL balance exists"""
        response = requests.get(f"{BASE_URL}/api/kraken/balance")
        assert response.status_code == 200
        
        data = response.json()
        balances = data.get("balances", {})
        assert "SOL" in balances, "Expected SOL (Solana) in balances"
        assert balances["SOL"]["amount"] > 0, "Expected positive SOL balance"
    
    def test_kraken_balance_has_dot(self):
        """Verify DOT balance exists"""
        response = requests.get(f"{BASE_URL}/api/kraken/balance")
        assert response.status_code == 200
        
        data = response.json()
        balances = data.get("balances", {})
        assert "DOT" in balances, "Expected DOT (Polkadot) in balances"
        assert balances["DOT"]["amount"] > 0, "Expected positive DOT balance"
    
    def test_kraken_balance_has_xrp(self):
        """Verify XRP balance exists (XXRP)"""
        response = requests.get(f"{BASE_URL}/api/kraken/balance")
        assert response.status_code == 200
        
        data = response.json()
        balances = data.get("balances", {})
        assert "XXRP" in balances, "Expected XXRP (Ripple) in balances"
        assert balances["XXRP"]["amount"] > 0, "Expected positive XRP balance"
    
    def test_kraken_balance_total_currencies(self):
        """Verify total_currencies count is returned"""
        response = requests.get(f"{BASE_URL}/api/kraken/balance")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_currencies" in data, "Expected total_currencies in response"
        assert data["total_currencies"] >= 10, f"Expected at least 10 currencies, got {data['total_currencies']}"


class TestKrakenTicker:
    """Tests for /api/kraken/ticker/{pair} endpoint - Real-time price data"""
    
    def test_btc_ticker_returns_200(self):
        """Verify BTC ticker returns 200"""
        response = requests.get(f"{BASE_URL}/api/kraken/ticker/XXBTZUSD")
        assert response.status_code == 200
    
    def test_btc_ticker_has_price(self):
        """Verify BTC ticker has last price"""
        response = requests.get(f"{BASE_URL}/api/kraken/ticker/XXBTZUSD")
        assert response.status_code == 200
        
        data = response.json()
        assert "last" in data, "Expected last price in response"
        assert data["last"] > 50000, f"Expected BTC price > $50,000, got {data['last']}"
    
    def test_btc_ticker_has_bid_ask(self):
        """Verify BTC ticker has bid and ask prices"""
        response = requests.get(f"{BASE_URL}/api/kraken/ticker/XXBTZUSD")
        assert response.status_code == 200
        
        data = response.json()
        assert "bid" in data, "Expected bid price in response"
        assert "ask" in data, "Expected ask price in response"
        assert data["bid"] > 0, "Expected positive bid price"
        assert data["ask"] > 0, "Expected positive ask price"
        assert data["ask"] >= data["bid"], "Expected ask >= bid"
    
    def test_btc_ticker_has_volume(self):
        """Verify BTC ticker has 24h volume"""
        response = requests.get(f"{BASE_URL}/api/kraken/ticker/XXBTZUSD")
        assert response.status_code == 200
        
        data = response.json()
        assert "volume_24h" in data, "Expected volume_24h in response"
        assert data["volume_24h"] > 0, "Expected positive 24h volume"
    
    def test_eth_ticker_returns_200(self):
        """Verify ETH ticker returns 200"""
        response = requests.get(f"{BASE_URL}/api/kraken/ticker/XETHZUSD")
        assert response.status_code == 200
        
        data = response.json()
        assert "last" in data, "Expected last price in response"
        assert data["last"] > 1000, f"Expected ETH price > $1,000, got {data['last']}"


class TestKrakenAutoTrader:
    """Tests for /api/kraken/auto-trader/status endpoint - Auto trader services"""
    
    def test_auto_trader_initialized(self):
        """Verify auto trader is initialized"""
        response = requests.get(f"{BASE_URL}/api/kraken/auto-trader/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("initialized") == True, f"Expected initialized=True, got {data.get('initialized')}"
    
    def test_auto_trader_kraken_connected(self):
        """Verify Kraken is connected to auto trader"""
        response = requests.get(f"{BASE_URL}/api/kraken/auto-trader/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("kraken_connected") == True, f"Expected kraken_connected=True, got {data.get('kraken_connected')}"
    
    def test_auto_trader_ai_trainer_connected(self):
        """Verify AI trainer service is connected"""
        response = requests.get(f"{BASE_URL}/api/kraken/auto-trader/status")
        assert response.status_code == 200
        
        data = response.json()
        services = data.get("services", {})
        assert services.get("ai_trainer") == True, f"Expected ai_trainer=True, got {services.get('ai_trainer')}"
    
    def test_auto_trader_gem_finder_connected(self):
        """Verify gem finder service is connected"""
        response = requests.get(f"{BASE_URL}/api/kraken/auto-trader/status")
        assert response.status_code == 200
        
        data = response.json()
        services = data.get("services", {})
        assert services.get("gem_finder") == True, f"Expected gem_finder=True, got {services.get('gem_finder')}"
    
    def test_auto_trader_adaptive_strategy_connected(self):
        """Verify adaptive strategy service is connected"""
        response = requests.get(f"{BASE_URL}/api/kraken/auto-trader/status")
        assert response.status_code == 200
        
        data = response.json()
        services = data.get("services", {})
        assert services.get("adaptive_strategy") == True, f"Expected adaptive_strategy=True, got {services.get('adaptive_strategy')}"
    
    def test_auto_trader_regime_predictor_connected(self):
        """Verify ML regime predictor service is connected"""
        response = requests.get(f"{BASE_URL}/api/kraken/auto-trader/status")
        assert response.status_code == 200
        
        data = response.json()
        services = data.get("services", {})
        assert services.get("regime_predictor") == True, f"Expected regime_predictor=True, got {services.get('regime_predictor')}"
    
    def test_auto_trader_isolated_portfolio_connected(self):
        """Verify isolated portfolio service is connected"""
        response = requests.get(f"{BASE_URL}/api/kraken/auto-trader/status")
        assert response.status_code == 200
        
        data = response.json()
        services = data.get("services", {})
        assert services.get("isolated_portfolio") == True, f"Expected isolated_portfolio=True, got {services.get('isolated_portfolio')}"
    
    def test_auto_trader_balance_isolated(self):
        """Verify auto trader uses isolated budget"""
        response = requests.get(f"{BASE_URL}/api/kraken/auto-trader/status")
        assert response.status_code == 200
        
        data = response.json()
        balance = data.get("balance", {})
        assert balance.get("isolated") == True, f"Expected isolated=True, got {balance.get('isolated')}"
        assert balance.get("allocated") == True, f"Expected allocated=True, got {balance.get('allocated')}"
    
    def test_auto_trader_balance_500_budget(self):
        """Verify auto trader has $500 isolated budget"""
        response = requests.get(f"{BASE_URL}/api/kraken/auto-trader/status")
        assert response.status_code == 200
        
        data = response.json()
        balance = data.get("balance", {})
        assert balance.get("balance") == 500.0, f"Expected balance=500, got {balance.get('balance')}"
        assert balance.get("initial_budget") == 500.0, f"Expected initial_budget=500, got {balance.get('initial_budget')}"
    
    def test_auto_trader_real_trading_enabled(self):
        """Verify real trading is enabled"""
        response = requests.get(f"{BASE_URL}/api/kraken/auto-trader/status")
        assert response.status_code == 200
        
        data = response.json()
        balance = data.get("balance", {})
        assert balance.get("real_trading_enabled") == True, f"Expected real_trading_enabled=True, got {balance.get('real_trading_enabled')}"
    
    def test_auto_trader_ml_prediction(self):
        """Verify ML regime prediction is working"""
        response = requests.get(f"{BASE_URL}/api/kraken/auto-trader/status")
        assert response.status_code == 200
        
        data = response.json()
        adaptive_params = data.get("adaptive_params", {})
        ml_prediction = adaptive_params.get("ml_prediction", {})
        
        assert ml_prediction is not None, "Expected ml_prediction in response"
        assert "predicted_regime" in ml_prediction, "Expected predicted_regime in ml_prediction"
        assert "confidence" in ml_prediction, "Expected confidence in ml_prediction"
        assert ml_prediction.get("confidence", 0) > 50, f"Expected confidence > 50%, got {ml_prediction.get('confidence')}"


class TestKrakenSupportedPairs:
    """Tests for /api/kraken/supported-pairs endpoint - Trading pairs"""
    
    def test_supported_pairs_returns_200(self):
        """Verify supported pairs returns 200"""
        response = requests.get(f"{BASE_URL}/api/kraken/supported-pairs")
        assert response.status_code == 200
    
    def test_supported_pairs_count_30(self):
        """Verify 30 trading pairs are supported"""
        response = requests.get(f"{BASE_URL}/api/kraken/supported-pairs")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("count") == 30, f"Expected count=30, got {data.get('count')}"
    
    def test_supported_pairs_has_bitcoin(self):
        """Verify Bitcoin pair is supported"""
        response = requests.get(f"{BASE_URL}/api/kraken/supported-pairs")
        assert response.status_code == 200
        
        data = response.json()
        pairs = data.get("pairs", {})
        assert "bitcoin" in pairs, "Expected bitcoin in pairs"
        assert pairs["bitcoin"] == "XXBTZUSD", f"Expected XXBTZUSD, got {pairs['bitcoin']}"
    
    def test_supported_pairs_has_ethereum(self):
        """Verify Ethereum pair is supported"""
        response = requests.get(f"{BASE_URL}/api/kraken/supported-pairs")
        assert response.status_code == 200
        
        data = response.json()
        pairs = data.get("pairs", {})
        assert "ethereum" in pairs, "Expected ethereum in pairs"
        assert pairs["ethereum"] == "XETHZUSD", f"Expected XETHZUSD, got {pairs['ethereum']}"
    
    def test_supported_pairs_has_solana(self):
        """Verify Solana pair is supported"""
        response = requests.get(f"{BASE_URL}/api/kraken/supported-pairs")
        assert response.status_code == 200
        
        data = response.json()
        pairs = data.get("pairs", {})
        assert "solana" in pairs, "Expected solana in pairs"
        assert pairs["solana"] == "SOLUSD", f"Expected SOLUSD, got {pairs['solana']}"


class TestKrakenOpenOrders:
    """Tests for /api/kraken/open-orders endpoint - Open orders list"""
    
    def test_open_orders_returns_200(self):
        """Verify open orders returns 200"""
        response = requests.get(f"{BASE_URL}/api/kraken/open-orders")
        assert response.status_code == 200
    
    def test_open_orders_has_orders_field(self):
        """Verify orders field is returned"""
        response = requests.get(f"{BASE_URL}/api/kraken/open-orders")
        assert response.status_code == 200
        
        data = response.json()
        assert "orders" in data, "Expected orders in response"
        assert isinstance(data["orders"], dict), "Expected orders to be a dict"
    
    def test_open_orders_has_count(self):
        """Verify count field is returned"""
        response = requests.get(f"{BASE_URL}/api/kraken/open-orders")
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data, "Expected count in response"
        assert isinstance(data["count"], int), "Expected count to be an integer"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
