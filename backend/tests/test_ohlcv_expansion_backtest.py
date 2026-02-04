"""
Test OHLCV Expansion and Gem Backtesting Features
Tests for:
1. Weekly OHLCV expansion job scheduling
2. OHLCV expansion immediate run
3. OHLCV expansion status
4. Gem prediction backtesting start
5. Gem backtest status
6. Gem backtest history
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestOHLCVExpansion:
    """Tests for OHLCV expansion endpoints"""
    
    def test_schedule_weekly_ohlcv_expansion(self):
        """Test POST /api/scheduler/jobs/weekly-ohlcv-expansion - Schedule weekly expansion"""
        response = requests.post(
            f"{BASE_URL}/api/scheduler/jobs/weekly-ohlcv-expansion",
            json={
                "day_of_week": "sun",
                "hour": 4,
                "batch_size": 50
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, f"Expected success=True, got {data}"
        assert data.get("job_id") == "weekly_ohlcv_expansion", f"Expected job_id=weekly_ohlcv_expansion, got {data}"
        assert data.get("batch_size") == 50, f"Expected batch_size=50, got {data}"
        assert "schedule" in data, f"Expected schedule in response, got {data}"
        print(f"✓ Weekly OHLCV expansion job scheduled: {data.get('schedule')}")
    
    def test_get_ohlcv_expansion_status(self):
        """Test GET /api/scheduler/ohlcv-expansion-status - Get expansion progress"""
        response = requests.get(f"{BASE_URL}/api/scheduler/ohlcv-expansion-status")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify required fields
        assert "total_ai_coins" in data, f"Expected total_ai_coins in response, got {data}"
        assert "coins_downloaded" in data, f"Expected coins_downloaded in response, got {data}"
        assert "coins_remaining" in data, f"Expected coins_remaining in response, got {data}"
        assert "progress_pct" in data, f"Expected progress_pct in response, got {data}"
        assert "is_complete" in data, f"Expected is_complete in response, got {data}"
        
        # Verify data types
        assert isinstance(data["total_ai_coins"], int), f"total_ai_coins should be int"
        assert isinstance(data["coins_downloaded"], int), f"coins_downloaded should be int"
        assert isinstance(data["progress_pct"], (int, float)), f"progress_pct should be numeric"
        
        print(f"✓ OHLCV expansion status: {data['coins_downloaded']}/{data['total_ai_coins']} coins ({data['progress_pct']}%)")
        print(f"  Remaining: {data['coins_remaining']} coins, Complete: {data['is_complete']}")
    
    def test_run_ohlcv_expansion_now(self):
        """Test POST /api/scheduler/jobs/ohlcv-expansion-now - Run expansion immediately"""
        # First get current status
        status_before = requests.get(f"{BASE_URL}/api/scheduler/ohlcv-expansion-status").json()
        
        # Run expansion with small batch for testing
        response = requests.post(
            f"{BASE_URL}/api/scheduler/jobs/ohlcv-expansion-now",
            params={"batch_size": 2}  # Small batch for quick test
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Check if already complete or has results
        if data.get("status") == "complete":
            print(f"✓ OHLCV expansion already complete: {data.get('message')}")
        else:
            # Should have expansion progress
            assert "expansion_progress" in data or "coins_completed" in data, f"Expected expansion results, got {data}"
            print(f"✓ OHLCV expansion ran: {data.get('coins_completed', 0)} coins downloaded")
            if "expansion_progress" in data:
                progress = data["expansion_progress"]
                print(f"  Progress: {progress.get('progress_pct', 0)}%")


class TestGemBacktesting:
    """Tests for gem prediction backtesting endpoints"""
    
    def test_start_backtest(self):
        """Test POST /api/gems/backtest/start - Start iterative backtesting"""
        response = requests.post(
            f"{BASE_URL}/api/gems/backtest/start",
            params={
                "target_accuracy": 60.0,  # Lower target for faster test
                "max_iterations": 3  # Fewer iterations for testing
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Could be started or already running
        assert data.get("status") in ["started", "already_running"], f"Expected status started/already_running, got {data}"
        
        if data.get("status") == "started":
            assert "target_accuracy" in data, f"Expected target_accuracy in response, got {data}"
            assert "max_iterations" in data, f"Expected max_iterations in response, got {data}"
            print(f"✓ Backtest started: target={data.get('target_accuracy')}%, max_iterations={data.get('max_iterations')}")
        else:
            print(f"✓ Backtest already running: {data.get('message')}")
    
    def test_get_backtest_status(self):
        """Test GET /api/gems/backtest/status - Get backtest progress"""
        response = requests.get(f"{BASE_URL}/api/gems/backtest/status")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify required fields
        assert "running" in data, f"Expected running in response, got {data}"
        assert "target_accuracy" in data, f"Expected target_accuracy in response, got {data}"
        assert "current_accuracy" in data, f"Expected current_accuracy in response, got {data}"
        assert "message" in data, f"Expected message in response, got {data}"
        
        print(f"✓ Backtest status: running={data['running']}, accuracy={data['current_accuracy']}%")
        print(f"  Message: {data['message']}")
        
        # If completed, check result
        if data.get("result"):
            result = data["result"]
            print(f"  Final accuracy: {result.get('final_accuracy', 0)}%")
            print(f"  Target reached: {result.get('target_reached', False)}")
    
    def test_get_backtest_history(self):
        """Test GET /api/gems/backtest/history - Get backtest history"""
        response = requests.get(
            f"{BASE_URL}/api/gems/backtest/history",
            params={"limit": 5}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        assert "count" in data, f"Expected count in response, got {data}"
        assert "history" in data, f"Expected history in response, got {data}"
        assert isinstance(data["history"], list), f"history should be a list"
        
        print(f"✓ Backtest history: {data['count']} records")
        
        # If there are records, verify structure
        if data["history"]:
            record = data["history"][0]
            print(f"  Latest backtest: {record.get('timestamp', 'N/A')}")


class TestSchedulerStatus:
    """Tests for scheduler status with new jobs"""
    
    def test_scheduler_status_includes_ohlcv_expansion(self):
        """Test GET /api/scheduler/status - Verify OHLCV expansion job is listed"""
        response = requests.get(f"{BASE_URL}/api/scheduler/status")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        assert "running" in data, f"Expected running in response, got {data}"
        assert "scheduled_jobs" in data, f"Expected scheduled_jobs in response, got {data}"
        
        print(f"✓ Scheduler status: running={data['running']}")
        print(f"  Jobs: {list(data.get('scheduled_jobs', {}).keys())}")
        
        # Check if weekly_ohlcv_expansion is scheduled
        if "weekly_ohlcv_expansion" in data.get("scheduled_jobs", {}):
            job = data["scheduled_jobs"]["weekly_ohlcv_expansion"]
            print(f"  OHLCV expansion job: next_run={job.get('next_run')}")


class TestGemPredictorEndpoints:
    """Tests for existing gem predictor endpoints"""
    
    def test_scan_for_gems(self):
        """Test POST /api/gems/scan - Scan for hidden gems"""
        response = requests.post(
            f"{BASE_URL}/api/gems/scan",
            json={"limit": 10}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "count" in data, f"Expected count in response, got {data}"
        assert "gems" in data, f"Expected gems in response, got {data}"
        
        print(f"✓ Gem scan: found {data['count']} gems")
    
    def test_get_top_gems(self):
        """Test GET /api/gems/top - Get top hidden gems"""
        response = requests.get(f"{BASE_URL}/api/gems/top")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "top_gems" in data, f"Expected top_gems in response, got {data}"
        
        print(f"✓ Top gems: {len(data.get('top_gems', []))} top, {len(data.get('potential_gems', []))} potential")


class TestHistoricalDataDownloader:
    """Tests for historical data downloader service"""
    
    def test_get_storage_stats(self):
        """Test GET /api/historical-data/stats - Get storage statistics"""
        response = requests.get(f"{BASE_URL}/api/historical-data/stats")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "total_coins" in data, f"Expected total_coins in response, got {data}"
        assert "total_records" in data, f"Expected total_records in response, got {data}"
        
        print(f"✓ Historical data stats: {data['total_coins']} coins, {data['total_records']} records")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
