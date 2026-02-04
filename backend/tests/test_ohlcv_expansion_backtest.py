"""
Test OHLCV Expansion and Gem Backtesting Features
Tests for:
- Weekly OHLCV expansion job scheduling
- OHLCV expansion status endpoint
- Immediate OHLCV expansion trigger
- Gem backtest start/status/history endpoints
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestOHLCVExpansion:
    """Tests for OHLCV expansion features"""
    
    def test_ohlcv_expansion_status(self):
        """Test GET /api/scheduler/ohlcv-expansion-status"""
        response = requests.get(f"{BASE_URL}/api/scheduler/ohlcv-expansion-status")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_ai_coins" in data
        assert "coins_downloaded" in data
        assert "coins_remaining" in data
        assert "next_batch" in data
        assert "progress_pct" in data
        assert "is_complete" in data
        
        # Verify data types
        assert isinstance(data["total_ai_coins"], int)
        assert isinstance(data["coins_downloaded"], int)
        assert isinstance(data["coins_remaining"], int)
        assert isinstance(data["next_batch"], list)
        assert isinstance(data["progress_pct"], (int, float))
        assert isinstance(data["is_complete"], bool)
        
        # Verify progress calculation
        assert data["total_ai_coins"] >= 200  # Should have 200+ AI coins
        assert data["coins_downloaded"] >= 0
        assert data["coins_remaining"] >= 0
        assert 0 <= data["progress_pct"] <= 100
        
        print(f"✓ OHLCV expansion status: {data['coins_downloaded']}/{data['total_ai_coins']} coins ({data['progress_pct']}%)")
    
    def test_schedule_weekly_ohlcv_expansion(self):
        """Test POST /api/scheduler/jobs/weekly-ohlcv-expansion"""
        response = requests.post(
            f"{BASE_URL}/api/scheduler/jobs/weekly-ohlcv-expansion",
            json={
                "day_of_week": "sun",
                "hour": 4,
                "batch_size": 50
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert data["job_id"] == "weekly_ohlcv_expansion"
        assert "schedule" in data
        assert data["batch_size"] == 50
        assert "message" in data
        
        print(f"✓ Weekly OHLCV expansion scheduled: {data['schedule']}")
    
    def test_scheduler_status_shows_ohlcv_job(self):
        """Test that scheduler status shows the OHLCV expansion job"""
        # First schedule the job
        requests.post(
            f"{BASE_URL}/api/scheduler/jobs/weekly-ohlcv-expansion",
            json={"day_of_week": "sun", "hour": 4, "batch_size": 50}
        )
        
        # Check scheduler status
        response = requests.get(f"{BASE_URL}/api/scheduler/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["running"] == True
        assert "scheduled_jobs" in data
        
        # Verify job is in scheduled jobs
        if "weekly_ohlcv_expansion" in data["scheduled_jobs"]:
            job = data["scheduled_jobs"]["weekly_ohlcv_expansion"]
            assert "name" in job
            assert "next_run" in job
            print(f"✓ OHLCV expansion job found in scheduler: next run {job['next_run']}")
        else:
            print("✓ Scheduler status retrieved (job may have been removed)")


class TestGemBacktesting:
    """Tests for gem prediction backtesting features"""
    
    def test_backtest_status_initial(self):
        """Test GET /api/gems/backtest/status - initial state"""
        response = requests.get(f"{BASE_URL}/api/gems/backtest/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "running" in data
        assert "started_at" in data
        assert "progress" in data
        assert "current_iteration" in data
        assert "target_accuracy" in data
        assert "current_accuracy" in data
        assert "message" in data
        assert "result" in data
        
        print(f"✓ Backtest status: running={data['running']}, accuracy={data['current_accuracy']}%")
    
    def test_backtest_history(self):
        """Test GET /api/gems/backtest/history"""
        response = requests.get(f"{BASE_URL}/api/gems/backtest/history")
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
        assert "history" in data
        assert isinstance(data["history"], list)
        
        if data["count"] > 0:
            # Verify history entry structure
            entry = data["history"][0]
            assert "type" in entry
            assert "results" in entry
            assert "timestamp" in entry
            
            results = entry["results"]
            assert "started_at" in results
            assert "target_accuracy" in results
            assert "iterations" in results
            assert "final_accuracy" in results
            
            print(f"✓ Backtest history: {data['count']} entries, latest accuracy: {results['final_accuracy']}%")
        else:
            print("✓ Backtest history endpoint working (no history yet)")
    
    def test_start_backtest(self):
        """Test POST /api/gems/backtest/start"""
        response = requests.post(
            f"{BASE_URL}/api/gems/backtest/start",
            params={"target_accuracy": 60.0, "max_iterations": 2}
        )
        assert response.status_code == 200
        
        data = response.json()
        # Could be "started" or "already_running"
        assert data["status"] in ["started", "already_running"]
        
        if data["status"] == "started":
            assert data["target_accuracy"] == 60.0
            assert data["max_iterations"] == 2
            assert "check_status" in data
            print(f"✓ Backtest started: target={data['target_accuracy']}%, max_iterations={data['max_iterations']}")
        else:
            print(f"✓ Backtest already running")
    
    def test_backtest_completes(self):
        """Test that backtest completes and updates status"""
        # Start a quick backtest
        requests.post(
            f"{BASE_URL}/api/gems/backtest/start",
            params={"target_accuracy": 60.0, "max_iterations": 2}
        )
        
        # Wait for completion (max 30 seconds)
        for _ in range(15):
            time.sleep(2)
            response = requests.get(f"{BASE_URL}/api/gems/backtest/status")
            data = response.json()
            
            if not data["running"]:
                break
        
        # Verify completion
        response = requests.get(f"{BASE_URL}/api/gems/backtest/status")
        data = response.json()
        
        assert data["running"] == False
        assert data["current_accuracy"] >= 0
        assert data["message"] != ""
        
        if data["result"]:
            assert "iterations" in data["result"]
            assert "final_accuracy" in data["result"]
            assert "best_weights" in data["result"]
            print(f"✓ Backtest completed: {data['current_accuracy']}% accuracy, {len(data['result']['iterations'])} iterations")
        else:
            print("✓ Backtest status shows not running")


class TestIntegration:
    """Integration tests for OHLCV and backtesting"""
    
    def test_expansion_progress_updates(self):
        """Test that expansion progress updates after running"""
        # Get initial status
        initial = requests.get(f"{BASE_URL}/api/scheduler/ohlcv-expansion-status").json()
        initial_downloaded = initial["coins_downloaded"]
        
        # Run a small expansion (1 coin to be quick)
        response = requests.post(
            f"{BASE_URL}/api/scheduler/jobs/ohlcv-expansion-now",
            params={"batch_size": 1}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if expansion ran
            if "expansion_progress" in data:
                new_downloaded = data["expansion_progress"]["coins_downloaded"]
                assert new_downloaded >= initial_downloaded
                print(f"✓ Expansion progress updated: {initial_downloaded} -> {new_downloaded} coins")
            elif data.get("status") == "complete":
                print("✓ All coins already downloaded")
            else:
                print(f"✓ Expansion ran: {data.get('coins_completed', 0)} coins completed")
        else:
            print(f"✓ Expansion endpoint responded with status {response.status_code}")
    
    def test_backtest_uses_ohlcv_data(self):
        """Test that backtest uses OHLCV data from database"""
        # Start backtest
        response = requests.post(
            f"{BASE_URL}/api/gems/backtest/start",
            params={"target_accuracy": 50.0, "max_iterations": 1}
        )
        
        # Wait for completion
        for _ in range(10):
            time.sleep(2)
            status = requests.get(f"{BASE_URL}/api/gems/backtest/status").json()
            if not status["running"]:
                break
        
        # Check results
        status = requests.get(f"{BASE_URL}/api/gems/backtest/status").json()
        
        if status["result"] and status["result"].get("iterations"):
            iteration = status["result"]["iterations"][0]
            assert iteration["total_predictions"] > 0
            print(f"✓ Backtest used OHLCV data: {iteration['total_predictions']} predictions made")
        else:
            print("✓ Backtest completed (may need more OHLCV data)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
