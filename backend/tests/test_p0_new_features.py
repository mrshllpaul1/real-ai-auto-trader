"""
P0 New Features Test Suite
===========================
Tests for 5 new P0 features:
1. Advanced Orders (Trailing Stop, DCA Bot, OCO)
2. DeFi Wallet Integration
3. Yield Farming Dashboard
4. Perpetual Futures Trading
5. News Sentiment Engine
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAdvancedOrders:
    """Test Advanced Order Types API endpoints"""
    
    def test_get_orders_summary(self):
        """GET /api/advanced-orders/summary - Get summary of all advanced orders"""
        response = requests.get(f"{BASE_URL}/api/advanced-orders/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert "active_orders" in data
        assert "total_active" in data
        assert "trailing_stops" in data["active_orders"]
        assert "dca_bots" in data["active_orders"]
        assert "oco_orders" in data["active_orders"]
        assert "iceberg_orders" in data["active_orders"]
    
    def test_create_trailing_stop(self):
        """POST /api/advanced-orders/trailing-stop/create - Create trailing stop order"""
        payload = {
            "symbol": "ETH/USD",
            "side": "sell",
            "quantity": 0.5,
            "trail_percent": 3.0
        }
        response = requests.post(
            f"{BASE_URL}/api/advanced-orders/trailing-stop/create",
            json=payload
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "created"
        assert "order" in data
        assert data["order"]["symbol"] == "ETH/USD"
        assert data["order"]["trail_percent"] == 3.0
        assert data["order"]["status"] == "active"
        assert "current_stop_price" in data["order"]
        assert "order_id" in data["order"]
    
    def test_list_trailing_stops(self):
        """GET /api/advanced-orders/trailing-stop/list - List trailing stop orders"""
        response = requests.get(f"{BASE_URL}/api/advanced-orders/trailing-stop/list")
        assert response.status_code == 200
        
        data = response.json()
        assert "orders" in data
        assert "total" in data
        assert isinstance(data["orders"], list)
    
    def test_create_dca_bot(self):
        """POST /api/advanced-orders/dca/create - Create DCA bot"""
        payload = {
            "name": f"TEST_DCA_Bot_{uuid.uuid4().hex[:8]}",
            "symbol": "SOL/USD",
            "amount_per_order": 50.0,
            "frequency": "daily",
            "start_immediately": True
        }
        response = requests.post(
            f"{BASE_URL}/api/advanced-orders/dca/create",
            json=payload
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "created"
        assert "bot" in data
        assert data["bot"]["symbol"] == "SOL/USD"
        assert data["bot"]["amount_per_order"] == 50.0
        assert data["bot"]["frequency"] == "daily"
        assert data["bot"]["status"] == "active"
        assert "bot_id" in data["bot"]
    
    def test_list_dca_bots(self):
        """GET /api/advanced-orders/dca/list - List DCA bots"""
        response = requests.get(f"{BASE_URL}/api/advanced-orders/dca/list")
        assert response.status_code == 200
        
        data = response.json()
        assert "bots" in data
        assert "summary" in data
        assert "total_bots" in data["summary"]
        assert "active_bots" in data["summary"]
    
    def test_create_oco_order(self):
        """POST /api/advanced-orders/oco/create - Create OCO order"""
        payload = {
            "symbol": "BTC/USD",
            "quantity": 0.01,
            "take_profit_price": 50000,
            "stop_loss_price": 40000
        }
        response = requests.post(
            f"{BASE_URL}/api/advanced-orders/oco/create",
            json=payload
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "created"
        assert "order" in data
        assert data["order"]["take_profit_price"] == 50000
        assert data["order"]["stop_loss_price"] == 40000
    
    def test_list_oco_orders(self):
        """GET /api/advanced-orders/oco/list - List OCO orders"""
        response = requests.get(f"{BASE_URL}/api/advanced-orders/oco/list")
        assert response.status_code == 200
        
        data = response.json()
        assert "orders" in data
        assert "total" in data


class TestDeFiWallet:
    """Test DeFi Wallet Integration API endpoints"""
    
    def test_get_supported_chains_protocols(self):
        """GET /api/defi-wallet/supported - Get supported chains and protocols"""
        response = requests.get(f"{BASE_URL}/api/defi-wallet/supported")
        assert response.status_code == 200
        
        data = response.json()
        assert "chains" in data
        assert "protocols" in data
        assert "wallet_types" in data
        
        # Verify chains
        assert len(data["chains"]) > 0
        chain_ids = [c["id"] for c in data["chains"]]
        assert "ethereum" in chain_ids
        assert "polygon" in chain_ids
        
        # Verify protocols
        assert len(data["protocols"]) > 0
        protocol_ids = [p["id"] for p in data["protocols"]]
        assert "uniswap" in protocol_ids
        assert "aave" in protocol_ids
        
        # Verify wallet types
        assert "metamask" in data["wallet_types"]
    
    def test_connect_wallet(self):
        """POST /api/defi-wallet/connect - Connect a Web3 wallet"""
        test_address = f"0x{'a' * 40}"  # Valid format address
        payload = {
            "wallet_address": test_address,
            "wallet_type": "metamask",
            "chain": "ethereum"
        }
        response = requests.post(
            f"{BASE_URL}/api/defi-wallet/connect",
            json=payload
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["connected", "already_connected"]
        assert "wallet_id" in data or data["status"] == "already_connected"
    
    def test_connect_wallet_invalid_address(self):
        """POST /api/defi-wallet/connect - Reject invalid wallet address"""
        payload = {
            "wallet_address": "invalid_address",
            "wallet_type": "metamask",
            "chain": "ethereum"
        }
        response = requests.post(
            f"{BASE_URL}/api/defi-wallet/connect",
            json=payload
        )
        assert response.status_code == 400
    
    def test_list_connected_wallets(self):
        """GET /api/defi-wallet/wallets - List connected wallets"""
        response = requests.get(f"{BASE_URL}/api/defi-wallet/wallets")
        assert response.status_code == 200
        
        data = response.json()
        assert "wallets" in data
        assert "total" in data
    
    def test_get_token_balances(self):
        """GET /api/defi-wallet/balances/{wallet_address} - Get token balances"""
        test_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f8fE00"
        response = requests.get(f"{BASE_URL}/api/defi-wallet/balances/{test_address}")
        assert response.status_code == 200
        
        data = response.json()
        assert "wallet_address" in data
        assert "balances" in data
        assert "total_value_usd" in data
        assert len(data["balances"]) > 0
        
        # Verify balance structure
        balance = data["balances"][0]
        assert "symbol" in balance
        assert "balance" in balance
        assert "value_usd" in balance
    
    def test_get_defi_positions(self):
        """GET /api/defi-wallet/positions/{wallet_address} - Get DeFi positions"""
        test_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f8fE00"
        response = requests.get(f"{BASE_URL}/api/defi-wallet/positions/{test_address}")
        assert response.status_code == 200
        
        data = response.json()
        assert "positions" in data
        assert "summary" in data
        assert len(data["positions"]) > 0
        
        # Verify position structure
        position = data["positions"][0]
        assert "protocol" in position
        assert "position_type" in position
        assert "current_value_usd" in position
    
    def test_get_portfolio_summary(self):
        """GET /api/defi-wallet/portfolio/{wallet_address} - Get full portfolio"""
        test_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f8fE00"
        response = requests.get(f"{BASE_URL}/api/defi-wallet/portfolio/{test_address}")
        assert response.status_code == 200
        
        data = response.json()
        assert "portfolio" in data
        assert "total_value_usd" in data
        assert "tokens" in data["portfolio"]
        assert "defi_positions" in data["portfolio"]


class TestYieldFarming:
    """Test Yield Farming Dashboard API endpoints"""
    
    def test_get_yield_opportunities(self):
        """GET /api/yield-farming/opportunities - Get yield farming opportunities"""
        response = requests.get(f"{BASE_URL}/api/yield-farming/opportunities")
        assert response.status_code == 200
        
        data = response.json()
        assert "opportunities" in data
        assert "total" in data
        assert len(data["opportunities"]) > 0
        
        # Verify opportunity structure
        opp = data["opportunities"][0]
        assert "vault_id" in opp
        assert "name" in opp
        assert "protocol" in opp
        assert "apy" in opp
        assert "risk_level" in opp
        assert "tvl" in opp
    
    def test_get_opportunities_filtered_by_chain(self):
        """GET /api/yield-farming/opportunities?chain=ethereum - Filter by chain"""
        response = requests.get(f"{BASE_URL}/api/yield-farming/opportunities?chain=ethereum")
        assert response.status_code == 200
        
        data = response.json()
        for opp in data["opportunities"]:
            assert opp["chain"] == "ethereum"
    
    def test_get_opportunities_filtered_by_risk(self):
        """GET /api/yield-farming/opportunities?risk_level=low - Filter by risk"""
        response = requests.get(f"{BASE_URL}/api/yield-farming/opportunities?risk_level=low")
        assert response.status_code == 200
        
        data = response.json()
        for opp in data["opportunities"]:
            assert opp["risk_level"] == "low"
    
    def test_deposit_to_vault(self):
        """POST /api/yield-farming/deposit - Deposit to yield vault"""
        payload = {
            "vault_id": "aave-usdc-eth",
            "amount_usd": 500,
            "token": "USDC",
            "auto_compound": True
        }
        response = requests.post(
            f"{BASE_URL}/api/yield-farming/deposit",
            json=payload
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "deposited"
        assert "position" in data
        assert data["position"]["vault_id"] == "aave-usdc-eth"
        assert data["position"]["deposited_usd"] == 500
    
    def test_get_user_positions(self):
        """GET /api/yield-farming/positions - Get user yield positions"""
        response = requests.get(f"{BASE_URL}/api/yield-farming/positions")
        assert response.status_code == 200
        
        data = response.json()
        assert "positions" in data
        assert "summary" in data
    
    def test_get_vault_details(self):
        """GET /api/yield-farming/vault/{vault_id} - Get vault details"""
        response = requests.get(f"{BASE_URL}/api/yield-farming/vault/aave-usdc-eth")
        assert response.status_code == 200
        
        data = response.json()
        assert data["vault_id"] == "aave-usdc-eth"
        assert "apy" in data
        assert "apy_history" in data


class TestPerpetualFutures:
    """Test Perpetual Futures Trading API endpoints"""
    
    def test_get_perpetual_markets(self):
        """GET /api/perpetuals/markets - Get perpetual futures markets"""
        response = requests.get(f"{BASE_URL}/api/perpetuals/markets")
        assert response.status_code == 200
        
        data = response.json()
        assert "markets" in data
        assert "total" in data
        assert len(data["markets"]) > 0
        
        # Verify market structure
        market = data["markets"][0]
        assert "symbol" in market
        assert "mark_price" in market
        assert "funding_rate" in market
        assert "max_leverage" in market
        assert "open_interest" in market
    
    def test_open_long_position(self):
        """POST /api/perpetuals/position/open - Open long position"""
        payload = {
            "symbol": "ETH-PERP",
            "side": "long",
            "size_usd": 500,
            "leverage": 3
        }
        response = requests.post(
            f"{BASE_URL}/api/perpetuals/position/open",
            json=payload
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "opened"
        assert "position" in data
        assert data["position"]["symbol"] == "ETH-PERP"
        assert data["position"]["side"] == "long"
        assert data["position"]["leverage"] == 3
        assert "liquidation_price" in data["position"]
        assert "entry_price" in data["position"]
    
    def test_open_short_position(self):
        """POST /api/perpetuals/position/open - Open short position"""
        payload = {
            "symbol": "BTC-PERP",
            "side": "short",
            "size_usd": 1000,
            "leverage": 5
        }
        response = requests.post(
            f"{BASE_URL}/api/perpetuals/position/open",
            json=payload
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "opened"
        assert data["position"]["side"] == "short"
    
    def test_get_user_positions(self):
        """GET /api/perpetuals/positions - Get user perpetual positions"""
        response = requests.get(f"{BASE_URL}/api/perpetuals/positions")
        assert response.status_code == 200
        
        data = response.json()
        assert "positions" in data
        assert "summary" in data
    
    def test_get_funding_rates(self):
        """GET /api/perpetuals/funding-rates - Get funding rates"""
        response = requests.get(f"{BASE_URL}/api/perpetuals/funding-rates")
        assert response.status_code == 200
        
        data = response.json()
        assert "funding_rates" in data
        assert len(data["funding_rates"]) > 0
        
        rate = data["funding_rates"][0]
        assert "symbol" in rate
        assert "current_rate" in rate
    
    def test_get_account_info(self):
        """GET /api/perpetuals/account - Get account info"""
        response = requests.get(f"{BASE_URL}/api/perpetuals/account")
        assert response.status_code == 200
        
        data = response.json()
        assert "account_balance" in data
        assert "available_balance" in data
        assert "margin_used" in data


class TestNewsSentiment:
    """Test News Sentiment Engine API endpoints"""
    
    def test_get_market_sentiment(self):
        """GET /api/sentiment/market - Get overall market sentiment"""
        response = requests.get(f"{BASE_URL}/api/sentiment/market")
        assert response.status_code == 200
        
        data = response.json()
        assert "market_score" in data
        assert "market_label" in data
        assert "confidence" in data
        assert "coin_sentiments" in data
        
        # Verify score is in valid range
        assert 0 <= data["market_score"] <= 100
        assert data["market_label"] in ["very_bearish", "bearish", "neutral", "bullish", "very_bullish"]
    
    def test_get_coin_sentiment_bitcoin(self):
        """GET /api/sentiment/coin/bitcoin - Get Bitcoin sentiment"""
        response = requests.get(f"{BASE_URL}/api/sentiment/coin/bitcoin")
        assert response.status_code == 200
        
        data = response.json()
        assert "coin_id" in data
        assert data["coin_id"] == "bitcoin"
        assert "score" in data
        assert "label" in data
        assert "confidence" in data
        assert "summary" in data
    
    def test_get_coin_sentiment_ethereum(self):
        """GET /api/sentiment/coin/ethereum - Get Ethereum sentiment"""
        response = requests.get(f"{BASE_URL}/api/sentiment/coin/ethereum")
        assert response.status_code == 200
        
        data = response.json()
        assert data["coin_id"] == "ethereum"
        assert "score" in data
    
    def test_get_coin_sentiment_with_analysis(self):
        """GET /api/sentiment/coin/{coin_id} - Verify analysis fields"""
        response = requests.get(f"{BASE_URL}/api/sentiment/coin/binancecoin")
        assert response.status_code == 200
        
        data = response.json()
        # These fields should be present even if empty
        assert "key_factors" in data
        assert "recent_headlines" in data
        assert "bullish_signals" in data
        assert "bearish_signals" in data


class TestNavigationSidebar:
    """Test that all new navigation links are present"""
    
    def test_frontend_loads(self):
        """Verify frontend loads successfully"""
        response = requests.get(BASE_URL)
        assert response.status_code == 200
    
    def test_advanced_orders_page_loads(self):
        """Verify Advanced Orders page loads"""
        response = requests.get(f"{BASE_URL}/advanced-orders")
        assert response.status_code == 200
    
    def test_defi_wallet_page_loads(self):
        """Verify DeFi Wallet page loads"""
        response = requests.get(f"{BASE_URL}/defi-wallet")
        assert response.status_code == 200
    
    def test_yield_farming_page_loads(self):
        """Verify Yield Farming page loads"""
        response = requests.get(f"{BASE_URL}/yield-farming")
        assert response.status_code == 200
    
    def test_perpetuals_page_loads(self):
        """Verify Perpetuals page loads"""
        response = requests.get(f"{BASE_URL}/perpetuals")
        assert response.status_code == 200
    
    def test_news_sentiment_page_loads(self):
        """Verify News Sentiment page loads"""
        response = requests.get(f"{BASE_URL}/news-sentiment")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
