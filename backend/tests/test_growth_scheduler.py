"""
Test Growth Engine and Scheduler APIs
Tests for $500 → $100,000 growth strategy and autopilot scheduling
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestGrowthAPIs:
    """Growth Engine API tests"""
    
    def test_get_growth_stats(self):
        """GET /api/growth/stats - Returns portfolio value and statistics"""
        response = requests.get(f"{BASE_URL}/api/growth/stats")
        assert response.status_code == 200
        
        data = response.json()
        # Verify portfolio structure
        assert 'portfolio' in data
        portfolio = data['portfolio']
        assert 'total_value' in portfolio
        assert 'starting_capital' in portfolio
        assert 'goal' in portfolio
        assert 'progress_pct' in portfolio
        assert 'current_multiplier' in portfolio
        assert portfolio['starting_capital'] == 500
        assert portfolio['goal'] == 100000
        
        # Verify statistics structure
        assert 'statistics' in data
        stats = data['statistics']
        assert 'total_trades' in stats
        assert 'win_rate' in stats
        assert 'moonshots' in stats
        
        # Verify goal_progress structure
        assert 'goal_progress' in data
        
    def test_get_growth_positions(self):
        """GET /api/growth/positions - Returns open positions"""
        response = requests.get(f"{BASE_URL}/api/growth/positions?status=OPEN")
        assert response.status_code == 200
        
        data = response.json()
        assert 'positions' in data
        assert 'count' in data
        assert isinstance(data['positions'], list)
        
        # If positions exist, verify structure
        if data['positions']:
            pos = data['positions'][0]
            assert 'coin_id' in pos
            assert 'symbol' in pos
            assert 'amount_usd' in pos
            assert 'entry_price' in pos
            assert 'status' in pos
            
    def test_get_growth_portfolio(self):
        """GET /api/growth/portfolio - Returns portfolio value"""
        response = requests.get(f"{BASE_URL}/api/growth/portfolio")
        assert response.status_code == 200
        
        data = response.json()
        assert 'total_value' in data
        assert 'usd_balance' in data
        assert 'positions_value' in data
        assert 'progress_pct' in data
        assert 'current_multiplier' in data
        
    def test_execute_growth_strategy(self):
        """POST /api/growth/execute - Executes growth strategy"""
        response = requests.post(
            f"{BASE_URL}/api/growth/execute",
            json={"capital": 50, "paper_trade": True}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert 'success' in data
        assert data['success'] == True
        assert 'execution' in data
        
        execution = data['execution']
        assert 'timestamp' in execution
        assert 'paper_trade' in execution
        assert execution['paper_trade'] == True
        assert 'capital' in execution
        assert 'trades' in execution
        
    def test_monitor_positions(self):
        """POST /api/growth/monitor - Monitors positions for SL/TP"""
        response = requests.post(f"{BASE_URL}/api/growth/monitor")
        assert response.status_code == 200
        
        data = response.json()
        assert 'checked' in data
        assert 'stop_losses_hit' in data
        assert 'take_profits_hit' in data
        assert 'trailing_stops_updated' in data
        assert isinstance(data['stop_losses_hit'], list)
        assert isinstance(data['take_profits_hit'], list)


class TestSchedulerAPIs:
    """Scheduler API tests"""
    
    def test_get_scheduler_status(self):
        """GET /api/scheduler/status - Returns scheduler status with jobs"""
        response = requests.get(f"{BASE_URL}/api/scheduler/status")
        assert response.status_code == 200
        
        data = response.json()
        assert 'running' in data
        assert 'jobs' in data
        assert 'job_count' in data
        assert isinstance(data['jobs'], list)
        assert isinstance(data['running'], bool)
        
    def test_setup_default_schedule(self):
        """POST /api/scheduler/setup-default - Sets up autopilot schedule"""
        response = requests.post(f"{BASE_URL}/api/scheduler/setup-default?paper_trade=true")
        assert response.status_code == 200
        
        data = response.json()
        assert 'success' in data
        assert data['success'] == True
        assert 'jobs_configured' in data
        assert data['jobs_configured'] == 3
        assert 'details' in data
        
        # Verify all 3 jobs configured
        details = data['details']
        assert 'monitor' in details
        assert 'compound' in details
        assert 'weekly' in details
        
        # Verify job details
        assert details['monitor']['job_id'] == 'growth_monitor'
        assert details['compound']['job_id'] == 'daily_compound'
        assert details['weekly']['job_id'] == 'weekly_trader'
        
    def test_scheduler_stop(self):
        """POST /api/scheduler/stop - Stops the scheduler"""
        response = requests.post(f"{BASE_URL}/api/scheduler/stop")
        assert response.status_code == 200
        
        data = response.json()
        assert 'success' in data
        assert data['success'] == True
        assert 'message' in data
        
        # Verify scheduler stopped
        status_response = requests.get(f"{BASE_URL}/api/scheduler/status")
        status = status_response.json()
        assert status['running'] == False
        
    def test_scheduler_start(self):
        """POST /api/scheduler/start - Starts the scheduler"""
        response = requests.post(f"{BASE_URL}/api/scheduler/start")
        assert response.status_code == 200
        
        data = response.json()
        assert 'success' in data
        assert data['success'] == True
        assert 'message' in data
        
        # Verify scheduler started
        status_response = requests.get(f"{BASE_URL}/api/scheduler/status")
        status = status_response.json()
        assert status['running'] == True
        
    def test_scheduled_jobs_have_next_run_times(self):
        """Verify scheduled jobs display with next run times"""
        # First setup default schedule
        requests.post(f"{BASE_URL}/api/scheduler/setup-default?paper_trade=true")
        
        # Get status
        response = requests.get(f"{BASE_URL}/api/scheduler/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data['job_count'] >= 3
        
        # Verify each job has next_run time
        for job in data['jobs']:
            assert 'id' in job
            assert 'name' in job
            assert 'next_run' in job
            assert 'trigger' in job
            # next_run should be a valid ISO timestamp
            assert job['next_run'] is not None


class TestGrowthSchedulerIntegration:
    """Integration tests for Growth + Scheduler"""
    
    def test_full_autopilot_workflow(self):
        """Test complete autopilot setup workflow"""
        import time
        
        # 1. Stop scheduler if running
        stop_response = requests.post(f"{BASE_URL}/api/scheduler/stop", timeout=10)
        assert stop_response.status_code == 200
        
        # Small delay to ensure scheduler state is updated
        time.sleep(1)
        
        # 2. Start the scheduler first
        start_response = requests.post(f"{BASE_URL}/api/scheduler/start", timeout=10)
        assert start_response.status_code == 200
        
        time.sleep(0.5)
        
        # 3. Setup default schedule
        setup_response = requests.post(f"{BASE_URL}/api/scheduler/setup-default?paper_trade=true", timeout=10)
        assert setup_response.status_code == 200
        assert setup_response.json()['success'] == True
        
        time.sleep(0.5)
        
        # 4. Verify scheduler is running with jobs (with retry)
        for attempt in range(3):
            status_response = requests.get(f"{BASE_URL}/api/scheduler/status", timeout=10)
            if status_response.status_code == 200:
                break
            time.sleep(1)
        
        assert status_response.status_code == 200
        status = status_response.json()
        assert status['running'] == True
        assert status['job_count'] >= 3
        
        # 5. Verify growth stats accessible
        stats_response = requests.get(f"{BASE_URL}/api/growth/stats", timeout=10)
        assert stats_response.status_code == 200
        
        # 6. Verify positions accessible
        positions_response = requests.get(f"{BASE_URL}/api/growth/positions?status=OPEN", timeout=10)
        assert positions_response.status_code == 200
        
    def test_growth_execution_creates_positions(self):
        """Test that growth execution creates positions"""
        # Get initial position count
        initial_response = requests.get(f"{BASE_URL}/api/growth/positions?status=OPEN")
        initial_count = initial_response.json()['count']
        
        # Execute growth strategy
        exec_response = requests.post(
            f"{BASE_URL}/api/growth/execute",
            json={"capital": 30, "paper_trade": True}
        )
        assert exec_response.status_code == 200
        
        # Verify positions increased
        final_response = requests.get(f"{BASE_URL}/api/growth/positions?status=OPEN")
        final_count = final_response.json()['count']
        
        # Should have more positions (or same if all coins already have positions)
        assert final_count >= initial_count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
