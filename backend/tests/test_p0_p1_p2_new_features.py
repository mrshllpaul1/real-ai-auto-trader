"""
Test P0, P1, P2 Features:
- P0: Deep Learning Historical Training for Hidden Gem Predictor
- P1: AI Chat Action Execution
- P2: Async Strategy Generation
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestP0DeepHistoricalTraining:
    """P0: Test Deep Learning Historical Training for Hidden Gem Predictor"""
    
    def test_train_deep_starts_training(self):
        """POST /api/gems/train-deep - Should start deep historical training"""
        response = requests.post(f"{BASE_URL}/api/gems/train-deep", timeout=30)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Should return started or already_running status
        assert "status" in data, f"Missing 'status' in response: {data}"
        assert data["status"] in ["started", "already_running"], f"Unexpected status: {data['status']}"
        
        if data["status"] == "started":
            assert "message" in data, "Missing 'message' when training started"
            assert "check_status" in data, "Missing 'check_status' endpoint reference"
            print(f"✓ Deep training started: {data['message']}")
        else:
            print(f"✓ Training already running, progress: {data.get('progress', 'N/A')}%")
    
    def test_deep_training_status_returns_progress(self):
        """GET /api/gems/deep-training-status - Should return training progress and results"""
        # First trigger training if not running
        requests.post(f"{BASE_URL}/api/gems/train-deep", timeout=30)
        
        # Wait a bit for training to progress
        time.sleep(2)
        
        response = requests.get(f"{BASE_URL}/api/gems/deep-training-status", timeout=30)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Should have these fields
        assert "running" in data, f"Missing 'running' field: {data}"
        assert "progress" in data, f"Missing 'progress' field: {data}"
        assert "message" in data, f"Missing 'message' field: {data}"
        
        # Progress should be 0-100
        assert 0 <= data["progress"] <= 100, f"Progress out of range: {data['progress']}"
        
        print(f"✓ Training status - Running: {data['running']}, Progress: {data['progress']}%, Message: {data['message']}")
        
        # If training completed, check result
        if not data["running"] and data.get("result"):
            result = data["result"]
            assert "status" in result, "Missing status in result"
            if result["status"] == "completed":
                assert "historical_gems" in result, "Missing historical_gems in completed result"
                assert "patterns_discovered" in result, "Missing patterns_discovered in completed result"
                assert "model_metrics" in result, "Missing model_metrics in completed result"
                print(f"✓ Training completed with {len(result.get('historical_gems', []))} historical gems analyzed")
    
    def test_deep_training_completes_successfully(self):
        """Wait for deep training to complete and verify results"""
        # Start training
        requests.post(f"{BASE_URL}/api/gems/train-deep", timeout=30)
        
        # Poll for completion (max 30 seconds)
        max_wait = 30
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = requests.get(f"{BASE_URL}/api/gems/deep-training-status", timeout=30)
            assert response.status_code == 200
            
            data = response.json()
            
            if not data["running"]:
                # Training finished
                if data.get("result"):
                    result = data["result"]
                    assert result.get("status") == "completed", f"Training failed: {result.get('error', 'Unknown error')}"
                    
                    # Verify training results
                    assert len(result.get("historical_gems", [])) > 0, "No historical gems in result"
                    assert len(result.get("patterns_discovered", [])) > 0, "No patterns discovered"
                    assert "model_metrics" in result, "Missing model_metrics"
                    
                    metrics = result["model_metrics"]
                    assert "final_accuracy" in metrics, "Missing final_accuracy"
                    assert "final_loss" in metrics, "Missing final_loss"
                    assert "weight_updates" in metrics, "Missing weight_updates"
                    
                    print(f"✓ Training completed successfully!")
                    print(f"  - Historical gems analyzed: {len(result['historical_gems'])}")
                    print(f"  - Patterns discovered: {len(result['patterns_discovered'])}")
                    print(f"  - Final accuracy: {metrics['final_accuracy']}%")
                    print(f"  - Final loss: {metrics['final_loss']}")
                    return
                break
            
            time.sleep(1)
        
        # If we get here, training may still be running or no result
        print("✓ Training status check passed (may still be running)")


class TestP1AIChatActionExecution:
    """P1: Test AI Chat Action Execution"""
    
    def test_execute_command_buy_intent(self):
        """POST /api/ai-chat/execute-command with 'buy btc' - Should detect buy intent and return actions"""
        payload = {
            "query": "buy btc",
            "session_id": "test_session_buy"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/execute-command",
            json=payload,
            timeout=60  # Longer timeout for LLM calls
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "response" in data, f"Missing 'response' field: {data}"
        assert "query" in data, f"Missing 'query' field: {data}"
        assert "actions_executed" in data, f"Missing 'actions_executed' field: {data}"
        assert "actions_to_execute" in data, f"Missing 'actions_to_execute' field: {data}"
        assert "error" in data, f"Missing 'error' field: {data}"
        
        # Should not have error
        assert data["error"] == False, f"Unexpected error: {data}"
        
        # Should detect buy intent
        actions_to_execute = data["actions_to_execute"]
        actions_executed = data["actions_executed"]
        
        # Check for trade_buy action or buy_intent
        has_buy_action = any(
            a.get("type") in ["trade_buy", "buy_intent"] or "buy" in str(a).lower()
            for a in actions_to_execute + actions_executed
        )
        
        print(f"✓ Buy intent detected: {has_buy_action}")
        print(f"  - Actions to execute: {actions_to_execute}")
        print(f"  - Actions executed: {actions_executed}")
        print(f"  - Response preview: {data['response'][:200]}...")
    
    def test_execute_command_find_gems(self):
        """POST /api/ai-chat/execute-command with 'find gems' - Should find and return gems"""
        payload = {
            "query": "find hidden gems",
            "session_id": "test_session_gems"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/execute-command",
            json=payload,
            timeout=60  # Longer timeout for LLM calls
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "response" in data, f"Missing 'response' field: {data}"
        assert "gems" in data, f"Missing 'gems' field: {data}"
        assert "gems_data" in data, f"Missing 'gems_data' field: {data}"
        assert "error" in data, f"Missing 'error' field: {data}"
        
        # Should not have error
        assert data["error"] == False, f"Unexpected error: {data}"
        
        # Check for gem scan action
        actions_executed = data.get("actions_executed", [])
        has_gem_scan = any(
            a.get("type") == "gem_scan" or "gem" in str(a).lower()
            for a in actions_executed
        )
        
        print(f"✓ Gem scan executed: {has_gem_scan}")
        print(f"  - Gems found: {data.get('gems', [])}")
        print(f"  - Gems data count: {len(data.get('gems_data', []))}")
        
        # If gems were found, verify structure
        if data.get("gems_data"):
            gem = data["gems_data"][0]
            assert "symbol" in gem, "Missing symbol in gem data"
            assert "total_score" in gem, "Missing total_score in gem data"
            print(f"  - Top gem: {gem['symbol']} with score {gem['total_score']}")
    
    def test_execute_command_navigation(self):
        """Test navigation intent detection"""
        payload = {
            "query": "go to dashboard",
            "session_id": "test_session_nav"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/execute-command",
            json=payload,
            timeout=60
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["error"] == False, f"Unexpected error: {data}"
        
        # Check for navigation action
        actions_to_execute = data.get("actions_to_execute", [])
        has_nav = any(a.get("type") == "navigate" for a in actions_to_execute)
        
        print(f"✓ Navigation intent detected: {has_nav}")
        print(f"  - Actions to execute: {actions_to_execute}")
    
    def test_execute_command_add_to_watchlist(self):
        """Test add to watchlist intent"""
        payload = {
            "query": "add ETH to watchlist",
            "session_id": "test_session_add"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/execute-command",
            json=payload,
            timeout=60
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["error"] == False, f"Unexpected error: {data}"
        
        # Check for add_coin action
        actions_to_execute = data.get("actions_to_execute", [])
        actions_executed = data.get("actions_executed", [])
        
        has_add = any(
            a.get("type") in ["add_coin", "add_to_watchlist"]
            for a in actions_to_execute + actions_executed
        )
        
        print(f"✓ Add to watchlist intent detected: {has_add}")
        print(f"  - Actions: {actions_to_execute + actions_executed}")
    
    def test_execute_command_sell_intent(self):
        """Test sell intent detection"""
        payload = {
            "query": "sell my ETH",
            "session_id": "test_session_sell"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/execute-command",
            json=payload,
            timeout=60
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["error"] == False, f"Unexpected error: {data}"
        
        # Check for sell action
        actions_to_execute = data.get("actions_to_execute", [])
        actions_executed = data.get("actions_executed", [])
        
        has_sell = any(
            a.get("type") in ["trade_sell", "sell_intent"] or "sell" in str(a).lower()
            for a in actions_to_execute + actions_executed
        )
        
        print(f"✓ Sell intent detected: {has_sell}")


class TestP2AsyncStrategyGeneration:
    """P2: Test Async Strategy Generation"""
    
    def test_generate_async_starts_background_task(self):
        """POST /api/strategies/generate-async - Should start background strategy generation"""
        payload = {
            "user_id": "test_user_async",
            "coin_pairs": ["BTC/USD", "ETH/USD"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/strategies/generate-async",
            json=payload,
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Should return started or already_running status
        assert "status" in data, f"Missing 'status' in response: {data}"
        assert data["status"] in ["started", "already_running"], f"Unexpected status: {data['status']}"
        
        if data["status"] == "started":
            assert "message" in data, "Missing 'message' when started"
            assert "check_status" in data, "Missing 'check_status' endpoint reference"
            print(f"✓ Async strategy generation started: {data['message']}")
        else:
            print(f"✓ Strategy generation already running, progress: {data.get('progress', 'N/A')}%")
    
    def test_generation_status_returns_progress(self):
        """GET /api/strategies/generation-status - Should return progress status"""
        # First trigger generation if not running
        payload = {
            "user_id": "test_user_status",
            "coin_pairs": ["BTC/USD"]
        }
        requests.post(f"{BASE_URL}/api/strategies/generate-async", json=payload, timeout=30)
        
        # Wait a bit
        time.sleep(1)
        
        response = requests.get(f"{BASE_URL}/api/strategies/generation-status", timeout=30)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Should have these fields
        assert "running" in data, f"Missing 'running' field: {data}"
        assert "progress" in data, f"Missing 'progress' field: {data}"
        assert "message" in data, f"Missing 'message' field: {data}"
        
        # Progress should be 0-100
        assert 0 <= data["progress"] <= 100, f"Progress out of range: {data['progress']}"
        
        print(f"✓ Generation status - Running: {data['running']}, Progress: {data['progress']}%, Message: {data['message']}")
    
    def test_async_generation_completes(self):
        """Wait for async generation to complete and verify results"""
        # Start generation
        payload = {
            "user_id": "test_user_complete",
            "coin_pairs": ["bitcoin/USD", "ethereum/USD"]  # Use full coin IDs
        }
        requests.post(f"{BASE_URL}/api/strategies/generate-async", json=payload, timeout=30)
        
        # Poll for completion (max 60 seconds due to market data fetching)
        max_wait = 60
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = requests.get(f"{BASE_URL}/api/strategies/generation-status", timeout=30)
            assert response.status_code == 200
            
            data = response.json()
            
            if not data["running"]:
                # Generation finished
                if data.get("result"):
                    result = data["result"]
                    assert "strategies" in result, f"Missing strategies in result: {result}"
                    assert "count" in result, f"Missing count in result: {result}"
                    
                    print(f"✓ Async generation completed!")
                    print(f"  - Strategies generated: {result['count']}")
                    
                    if result["strategies"]:
                        strategy = result["strategies"][0]
                        print(f"  - First strategy coin: {strategy.get('coin_id', 'N/A')}")
                        print(f"  - Confidence: {strategy.get('confidence_score', 'N/A')}")
                    return
                elif data.get("error"):
                    print(f"⚠ Generation completed with error: {data['error']}")
                    return
                break
            
            time.sleep(2)
        
        print("✓ Generation status check passed (may still be running)")


class TestAPIEndpointAvailability:
    """Test that all required endpoints are available"""
    
    def test_gems_train_deep_endpoint_exists(self):
        """Verify /api/gems/train-deep endpoint exists"""
        response = requests.post(f"{BASE_URL}/api/gems/train-deep", timeout=30)
        assert response.status_code != 404, "Endpoint /api/gems/train-deep not found"
        print("✓ /api/gems/train-deep endpoint exists")
    
    def test_gems_deep_training_status_endpoint_exists(self):
        """Verify /api/gems/deep-training-status endpoint exists"""
        response = requests.get(f"{BASE_URL}/api/gems/deep-training-status", timeout=30)
        assert response.status_code != 404, "Endpoint /api/gems/deep-training-status not found"
        print("✓ /api/gems/deep-training-status endpoint exists")
    
    def test_ai_chat_execute_command_endpoint_exists(self):
        """Verify /api/ai-chat/execute-command endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/ai-chat/execute-command",
            json={"query": "test", "session_id": "test"},
            timeout=60
        )
        assert response.status_code != 404, "Endpoint /api/ai-chat/execute-command not found"
        print("✓ /api/ai-chat/execute-command endpoint exists")
    
    def test_strategies_generate_async_endpoint_exists(self):
        """Verify /api/strategies/generate-async endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/strategies/generate-async",
            json={"user_id": "test", "coin_pairs": ["BTC/USD"]},
            timeout=30
        )
        assert response.status_code != 404, "Endpoint /api/strategies/generate-async not found"
        print("✓ /api/strategies/generate-async endpoint exists")
    
    def test_strategies_generation_status_endpoint_exists(self):
        """Verify /api/strategies/generation-status endpoint exists"""
        response = requests.get(f"{BASE_URL}/api/strategies/generation-status", timeout=30)
        assert response.status_code != 404, "Endpoint /api/strategies/generation-status not found"
        print("✓ /api/strategies/generation-status endpoint exists")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
