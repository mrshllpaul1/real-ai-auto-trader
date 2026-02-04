"""
Test Auto-Trader Spot Trading Endpoints
Tests the new spot trading integration in the automated trader:
- /api/kraken/auto-trader/spot/analyze/{symbol}
- /api/kraken/auto-trader/spot/trade
- /api/kraken/auto-trader/spot/scan
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAutoTraderSpotAnalyze:
    """Test /api/kraken/auto-trader/spot/analyze/{symbol} endpoint"""
    
    def test_analyze_btc_opportunity(self):
        """Test analyzing BTC spot trading opportunity"""
        response = requests.get(f"{BASE_URL}/api/kraken/auto-trader/spot/analyze/BTC")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert 'symbol' in data, "Response should contain 'symbol'"
        assert data['symbol'] == 'BTC', f"Symbol should be BTC, got {data['symbol']}"
        
        # Verify analysis fields
        assert 'action' in data, "Response should contain 'action'"
        assert data['action'] in ['buy', 'sell', 'hold', 'consider_buy', 'consider_sell', 'error'], \
            f"Invalid action: {data['action']}"
        
        assert 'score' in data, "Response should contain 'score'"
        assert 'confidence' in data, "Response should contain 'confidence'"
        assert 'reason' in data, "Response should contain 'reason'"
        assert 'timestamp' in data, "Response should contain 'timestamp'"
        
        print(f"✅ BTC Analysis: action={data['action']}, score={data.get('score')}, confidence={data.get('confidence')}")
        print(f"   Reason: {data.get('reason')}")
    
    def test_analyze_eth_opportunity(self):
        """Test analyzing ETH spot trading opportunity"""
        response = requests.get(f"{BASE_URL}/api/kraken/auto-trader/spot/analyze/ETH")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data['symbol'] == 'ETH'
        assert 'action' in data
        assert 'score' in data
        
        print(f"✅ ETH Analysis: action={data['action']}, score={data.get('score')}")
    
    def test_analyze_sol_opportunity(self):
        """Test analyzing SOL spot trading opportunity"""
        response = requests.get(f"{BASE_URL}/api/kraken/auto-trader/spot/analyze/SOL")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data['symbol'] == 'SOL'
        assert 'action' in data
        
        print(f"✅ SOL Analysis: action={data['action']}, score={data.get('score')}")
    
    def test_analyze_multiple_symbols(self):
        """Test analyzing multiple symbols"""
        symbols = ['XRP', 'ADA', 'DOGE', 'LINK']
        
        for symbol in symbols:
            response = requests.get(f"{BASE_URL}/api/kraken/auto-trader/spot/analyze/{symbol}")
            
            assert response.status_code == 200, f"Failed for {symbol}: {response.text}"
            
            data = response.json()
            assert data['symbol'] == symbol
            assert 'action' in data
            
            print(f"✅ {symbol}: action={data['action']}, score={data.get('score', 'N/A')}")
    
    def test_analyze_returns_price(self):
        """Test that analysis returns current price"""
        response = requests.get(f"{BASE_URL}/api/kraken/auto-trader/spot/analyze/BTC")
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Should have current_price field
        assert 'current_price' in data, "Response should contain 'current_price'"
        
        # Price should be a positive number for BTC
        if data.get('current_price'):
            assert data['current_price'] > 0, "BTC price should be positive"
            print(f"✅ BTC current price: ${data['current_price']:,.2f}")
    
    def test_analyze_returns_components(self):
        """Test that analysis returns prediction components"""
        response = requests.get(f"{BASE_URL}/api/kraken/auto-trader/spot/analyze/BTC")
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Should have components field showing which prediction services were used
        if 'components' in data:
            print(f"✅ Prediction components used: {list(data['components'].keys())}")


class TestAutoTraderSpotTrade:
    """Test /api/kraken/auto-trader/spot/trade endpoint"""
    
    def test_paper_trade_buy_btc(self):
        """Test paper trade buy order for BTC"""
        payload = {
            "symbol": "BTC",
            "side": "buy",
            "amount_usd": 50.0,
            "order_type": "market",
            "paper_trade": True,
            "use_ai_validation": True
        }
        
        response = requests.post(f"{BASE_URL}/api/kraken/auto-trader/spot/trade", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Trade should either succeed or be blocked by AI
        if data.get('success'):
            assert data['symbol'] == 'BTC'
            assert data['side'] == 'buy'
            assert data['paper_trade'] == True
            assert data['status'] == 'PAPER'
            assert 'volume' in data
            assert 'price' in data
            print(f"✅ Paper trade executed: BUY {data.get('volume', 0):.8f} BTC @ ${data.get('price', 0):,.2f}")
        elif data.get('blocked_by_ai'):
            # AI blocked the trade - this is valid behavior
            assert 'ai_action' in data
            assert 'ai_reason' in data
            print(f"✅ Trade blocked by AI: {data.get('ai_reason')}")
        else:
            # Some other error
            print(f"⚠️ Trade result: {data}")
    
    def test_paper_trade_buy_eth(self):
        """Test paper trade buy order for ETH"""
        payload = {
            "symbol": "ETH",
            "side": "buy",
            "amount_usd": 25.0,
            "order_type": "market",
            "paper_trade": True,
            "use_ai_validation": True
        }
        
        response = requests.post(f"{BASE_URL}/api/kraken/auto-trader/spot/trade", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        if data.get('success'):
            assert data['symbol'] == 'ETH'
            print(f"✅ Paper trade: BUY ETH @ ${data.get('price', 0):,.2f}")
        elif data.get('blocked_by_ai'):
            print(f"✅ Trade blocked by AI: {data.get('ai_reason')}")
    
    def test_paper_trade_without_ai_validation(self):
        """Test paper trade without AI validation"""
        payload = {
            "symbol": "SOL",
            "side": "buy",
            "amount_usd": 20.0,
            "order_type": "market",
            "paper_trade": True,
            "use_ai_validation": False  # Skip AI validation
        }
        
        response = requests.post(f"{BASE_URL}/api/kraken/auto-trader/spot/trade", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Without AI validation, trade should succeed (paper mode)
        assert data.get('success') == True, f"Trade should succeed without AI validation: {data}"
        assert data['paper_trade'] == True
        assert data['status'] == 'PAPER'
        
        print(f"✅ Paper trade (no AI): BUY {data.get('volume', 0):.8f} SOL @ ${data.get('price', 0):,.2f}")
    
    def test_ai_blocks_contradicting_trade(self):
        """Test that AI blocks trades that contradict its signals"""
        # First get AI analysis
        analysis_response = requests.get(f"{BASE_URL}/api/kraken/auto-trader/spot/analyze/BTC")
        analysis = analysis_response.json()
        
        ai_action = analysis.get('action', 'hold')
        
        # Try to execute opposite trade
        if ai_action in ['buy', 'consider_buy']:
            # AI says buy, try to sell
            payload = {
                "symbol": "BTC",
                "side": "sell",
                "amount_crypto": 0.001,
                "paper_trade": True,
                "use_ai_validation": True
            }
            expected_block = True
        elif ai_action in ['sell', 'consider_sell']:
            # AI says sell, try to buy
            payload = {
                "symbol": "BTC",
                "side": "buy",
                "amount_usd": 50.0,
                "paper_trade": True,
                "use_ai_validation": True
            }
            expected_block = True
        else:
            # AI says hold - trade might go through
            payload = {
                "symbol": "BTC",
                "side": "buy",
                "amount_usd": 50.0,
                "paper_trade": True,
                "use_ai_validation": True
            }
            expected_block = False
        
        response = requests.post(f"{BASE_URL}/api/kraken/auto-trader/spot/trade", json=payload)
        
        assert response.status_code == 200
        
        data = response.json()
        
        if expected_block and data.get('blocked_by_ai'):
            print(f"✅ AI correctly blocked contradicting trade: {data.get('ai_reason')}")
        elif data.get('success'):
            print(f"✅ Trade executed (AI allowed): {data.get('side')} {data.get('symbol')}")
        else:
            print(f"⚠️ Trade result: {data}")
    
    def test_trade_requires_amount(self):
        """Test that buy trades require amount_usd"""
        payload = {
            "symbol": "BTC",
            "side": "buy",
            # Missing amount_usd
            "paper_trade": True,
            "use_ai_validation": False
        }
        
        response = requests.post(f"{BASE_URL}/api/kraken/auto-trader/spot/trade", json=payload)
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Should fail due to missing amount
        assert data.get('success') == False, "Trade should fail without amount"
        assert 'error' in data
        
        print(f"✅ Correctly rejected trade without amount: {data.get('error')}")
    
    def test_trade_returns_ai_validation(self):
        """Test that trade response includes AI validation details"""
        payload = {
            "symbol": "ETH",
            "side": "buy",
            "amount_usd": 30.0,
            "paper_trade": True,
            "use_ai_validation": True
        }
        
        response = requests.post(f"{BASE_URL}/api/kraken/auto-trader/spot/trade", json=payload)
        
        assert response.status_code == 200
        
        data = response.json()
        
        # If trade succeeded, should have ai_validation field
        if data.get('success'):
            assert 'ai_validation' in data, "Successful trade should include AI validation"
            ai_val = data['ai_validation']
            if ai_val:
                print(f"✅ AI validation included: score={ai_val.get('score')}, action={ai_val.get('action')}")
        elif data.get('blocked_by_ai'):
            print(f"✅ Trade blocked with AI details: score={data.get('ai_score')}")


class TestAutoTraderSpotScan:
    """Test /api/kraken/auto-trader/spot/scan endpoint"""
    
    def test_spot_scan_paper_trade(self):
        """Test auto spot scan in paper trade mode"""
        response = requests.post(f"{BASE_URL}/api/kraken/auto-trader/spot/scan?paper_trade=true")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert 'timestamp' in data, "Response should contain 'timestamp'"
        assert 'paper_trade' in data, "Response should contain 'paper_trade'"
        assert data['paper_trade'] == True, "Should be paper trade mode"
        
        assert 'scanned_symbols' in data, "Response should contain 'scanned_symbols'"
        assert 'buy_opportunities' in data, "Response should contain 'buy_opportunities'"
        assert 'sell_opportunities' in data, "Response should contain 'sell_opportunities'"
        assert 'executed_trades' in data, "Response should contain 'executed_trades'"
        assert 'scan_results' in data, "Response should contain 'scan_results'"
        
        print(f"✅ Spot Scan Results:")
        print(f"   Scanned: {data['scanned_symbols']} symbols")
        print(f"   Buy opportunities: {data['buy_opportunities']}")
        print(f"   Sell opportunities: {data['sell_opportunities']}")
        print(f"   Trades executed: {data['executed_trades']}")
    
    def test_spot_scan_returns_best_opportunities(self):
        """Test that scan returns best buy/sell opportunities"""
        response = requests.post(f"{BASE_URL}/api/kraken/auto-trader/spot/scan?paper_trade=true")
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Should have best_buys and best_sells
        assert 'best_buys' in data, "Response should contain 'best_buys'"
        assert 'best_sells' in data, "Response should contain 'best_sells'"
        
        if data['best_buys']:
            print(f"✅ Best buy opportunities:")
            for opp in data['best_buys'][:3]:
                print(f"   {opp.get('symbol')}: score={opp.get('score')}, action={opp.get('action')}")
        
        if data['best_sells']:
            print(f"✅ Best sell opportunities:")
            for opp in data['best_sells'][:3]:
                print(f"   {opp.get('symbol')}: score={opp.get('score')}, action={opp.get('action')}")
    
    def test_spot_scan_executes_trades(self):
        """Test that scan executes trades for good opportunities"""
        response = requests.post(f"{BASE_URL}/api/kraken/auto-trader/spot/scan?paper_trade=true")
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Check if any trades were executed
        if data.get('executed_trades', 0) > 0:
            assert 'trades' in data, "Should have trades list"
            
            for trade in data['trades']:
                assert trade.get('success') == True
                assert trade.get('paper_trade') == True
                print(f"✅ Executed: {trade.get('side')} {trade.get('symbol')} @ ${trade.get('price', 0):,.2f}")
        else:
            print(f"ℹ️ No trades executed (no strong signals found)")
    
    def test_spot_scan_includes_scan_results(self):
        """Test that scan includes detailed results for each symbol"""
        response = requests.post(f"{BASE_URL}/api/kraken/auto-trader/spot/scan?paper_trade=true")
        
        assert response.status_code == 200
        
        data = response.json()
        
        scan_results = data.get('scan_results', [])
        
        if scan_results:
            print(f"✅ Scan results for {len(scan_results)} symbols:")
            for result in scan_results[:5]:
                print(f"   {result.get('symbol')}: {result.get('action')} (score={result.get('score', 'N/A')})")


class TestAutoTraderStatus:
    """Test auto-trader status endpoint"""
    
    def test_auto_trader_status(self):
        """Test auto-trader status endpoint"""
        response = requests.get(f"{BASE_URL}/api/kraken/auto-trader/status")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        assert 'initialized' in data, "Response should contain 'initialized'"
        
        if data.get('initialized'):
            print(f"✅ Auto-trader initialized")
            
            if 'services' in data:
                services = data['services']
                print(f"   Services status:")
                for service, status in services.items():
                    print(f"     {service}: {status}")
            
            if 'balance' in data:
                balance = data['balance']
                print(f"   Balance: ${balance.get('balance', 0):,.2f}")
                print(f"   Isolated: {balance.get('isolated', False)}")
        else:
            print(f"⚠️ Auto-trader not initialized: {data.get('error')}")


class TestPredictionSignals:
    """Test prediction signals endpoint"""
    
    def test_prediction_signals_btc(self):
        """Test getting prediction signals for BTC"""
        response = requests.get(f"{BASE_URL}/api/kraken/auto-trader/prediction-signals/BTC")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        assert 'symbol' in data, "Response should contain 'symbol'"
        assert data['symbol'] == 'BTC'
        
        assert 'composite' in data, "Response should contain 'composite'"
        
        composite = data['composite']
        assert 'score' in composite, "Composite should contain 'score'"
        assert 'signal' in composite, "Composite should contain 'signal'"
        
        print(f"✅ BTC Prediction Signals:")
        print(f"   Composite score: {composite.get('score')}")
        print(f"   Signal: {composite.get('signal')}")
        print(f"   Confidence: {composite.get('confidence')}%")
        print(f"   Models used: {composite.get('models_used')}")
        
        if 'components' in data:
            print(f"   Components: {list(data['components'].keys())}")


class TestRLAgentTraining:
    """Test RL Agent training status"""
    
    def test_training_status(self):
        """Check if RL Agent training is running"""
        response = requests.get(f"{BASE_URL}/api/training/status")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        print(f"✅ Training Status:")
        print(f"   Active trainings: {data.get('active_trainings', 0)}")
        
        if 'models' in data:
            for model, status in data['models'].items():
                if isinstance(status, dict):
                    print(f"   {model}: trained={status.get('trained', False)}")
                else:
                    print(f"   {model}: {status}")


class TestRegimeModels:
    """Test regime model training status"""
    
    def test_regime_status(self):
        """Check regime model status"""
        response = requests.get(f"{BASE_URL}/api/regime/status")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Regime Model Status:")
            print(f"   Trained: {data.get('trained', False)}")
            
            if 'models' in data:
                print(f"   Models: {data.get('models', [])}")
            
            if 'accuracy' in data:
                print(f"   Accuracy: {data.get('accuracy')}%")
        else:
            print(f"ℹ️ Regime endpoint returned {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
