"""
Test Portfolio Visualization and Background Tasks APIs
Tests for:
- /api/portfolio/visualization/summary
- /api/portfolio/visualization/composition
- /api/portfolio/visualization/performance-history
- /api/tasks/timeout-config
- /api/tasks/active
- /api/tasks/history
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestPortfolioVisualizationAPIs:
    """Tests for Portfolio Visualization endpoints"""
    
    def test_portfolio_summary_endpoint(self):
        """Test /api/portfolio/visualization/summary returns portfolio metrics"""
        response = requests.get(f"{BASE_URL}/api/portfolio/visualization/summary")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Should have either allocated=True with metrics or allocated=False
        assert "allocated" in data, "Response should contain 'allocated' field"
        
        if data.get("allocated"):
            # Verify all expected fields are present
            assert "initial_budget" in data, "Should have initial_budget"
            assert "current_value" in data, "Should have current_value"
            assert "cash_available" in data, "Should have cash_available"
            assert "total_pnl" in data, "Should have total_pnl"
            assert "total_pnl_pct" in data, "Should have total_pnl_pct"
            assert "positions_count" in data, "Should have positions_count"
            assert "gems_count" in data, "Should have gems_count"
            assert "trades_executed" in data, "Should have trades_executed"
            assert "avg_position_size" in data, "Should have avg_position_size"
            assert "real_trading_enabled" in data, "Should have real_trading_enabled"
            
            # Verify data types
            assert isinstance(data["initial_budget"], (int, float))
            assert isinstance(data["current_value"], (int, float))
            assert isinstance(data["positions_count"], int)
        else:
            # Not allocated - should have message
            assert "message" in data or data.get("allocated") == False
        
        print(f"✓ Portfolio summary: allocated={data.get('allocated')}, positions={data.get('positions_count', 0)}")
    
    def test_portfolio_composition_endpoint(self):
        """Test /api/portfolio/visualization/composition returns allocation data"""
        response = requests.get(f"{BASE_URL}/api/portfolio/visualization/composition")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Should have composition array
        assert "composition" in data, "Response should contain 'composition' field"
        assert isinstance(data["composition"], list), "composition should be a list"
        
        # Should have percentage fields
        assert "cash_pct" in data, "Should have cash_pct"
        assert "invested_pct" in data, "Should have invested_pct"
        assert "total_value" in data, "Should have total_value"
        
        # Verify composition items structure if any exist
        if data["composition"]:
            item = data["composition"][0]
            assert "name" in item, "Composition item should have name"
            assert "value" in item, "Composition item should have value"
            assert "percentage" in item, "Composition item should have percentage"
        
        print(f"✓ Portfolio composition: {len(data['composition'])} items, cash={data.get('cash_pct', 0)}%, invested={data.get('invested_pct', 0)}%")
    
    def test_portfolio_performance_history_default(self):
        """Test /api/portfolio/visualization/performance-history returns chart data"""
        response = requests.get(f"{BASE_URL}/api/portfolio/visualization/performance-history")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Should have history array
        assert "history" in data, "Response should contain 'history' field"
        assert isinstance(data["history"], list), "history should be a list"
        
        # Should have range
        assert "range" in data, "Should have range field"
        
        # Should have stats
        assert "stats" in data, "Should have stats field"
        stats = data["stats"]
        assert "period_return" in stats, "Stats should have period_return"
        assert "high" in stats, "Stats should have high"
        assert "low" in stats, "Stats should have low"
        assert "data_points" in stats, "Stats should have data_points"
        
        # Verify history items structure if any exist
        if data["history"]:
            item = data["history"][0]
            assert "date" in item, "History item should have date"
            assert "value" in item, "History item should have value"
        
        print(f"✓ Performance history: range={data.get('range')}, data_points={stats.get('data_points', 0)}")
    
    def test_portfolio_performance_history_time_ranges(self):
        """Test performance history with different time ranges"""
        ranges = ['1d', '7d', '30d', '90d', 'all']
        
        for time_range in ranges:
            response = requests.get(f"{BASE_URL}/api/portfolio/visualization/performance-history?range={time_range}")
            assert response.status_code == 200, f"Expected 200 for range={time_range}, got {response.status_code}"
            
            data = response.json()
            assert data.get("range") == time_range, f"Expected range={time_range}, got {data.get('range')}"
            print(f"  ✓ Range {time_range}: {data['stats'].get('data_points', 0)} data points")
        
        print(f"✓ All time ranges work correctly")
    
    def test_portfolio_top_performers(self):
        """Test /api/portfolio/visualization/top-performers endpoint"""
        response = requests.get(f"{BASE_URL}/api/portfolio/visualization/top-performers?limit=5")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "top_performers" in data, "Response should contain 'top_performers' field"
        assert isinstance(data["top_performers"], list), "top_performers should be a list"
        
        # Verify structure if any exist
        if data["top_performers"]:
            item = data["top_performers"][0]
            assert "coin_id" in item, "Should have coin_id"
            assert "pnl_pct" in item, "Should have pnl_pct"
            assert "current_value" in item, "Should have current_value"
        
        print(f"✓ Top performers: {len(data['top_performers'])} positions")
    
    def test_portfolio_worst_performers(self):
        """Test /api/portfolio/visualization/worst-performers endpoint"""
        response = requests.get(f"{BASE_URL}/api/portfolio/visualization/worst-performers?limit=5")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "worst_performers" in data, "Response should contain 'worst_performers' field"
        assert isinstance(data["worst_performers"], list), "worst_performers should be a list"
        
        print(f"✓ Worst performers: {len(data['worst_performers'])} positions")


class TestBackgroundTasksAPIs:
    """Tests for Background Tasks endpoints"""
    
    def test_timeout_config_endpoint(self):
        """Test /api/tasks/timeout-config returns timeout settings"""
        response = requests.get(f"{BASE_URL}/api/tasks/timeout-config")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Should have timeouts object
        assert "timeouts" in data, "Response should contain 'timeouts' field"
        timeouts = data["timeouts"]
        
        # Verify expected task types are present
        expected_task_types = [
            "model_training",
            "backtesting",
            "data_download",
            "universe_expansion",
            "gem_scan",
            "regime_prediction",
            "custom"
        ]
        
        for task_type in expected_task_types:
            assert task_type in timeouts, f"Should have timeout for {task_type}"
            assert isinstance(timeouts[task_type], int), f"Timeout for {task_type} should be int"
            assert timeouts[task_type] > 0, f"Timeout for {task_type} should be positive"
        
        # Verify specific timeout values
        assert timeouts["model_training"] == 600, "model_training should be 600s (10 min)"
        assert timeouts["backtesting"] == 900, "backtesting should be 900s (15 min)"
        assert timeouts["data_download"] == 300, "data_download should be 300s (5 min)"
        
        # Should have note
        assert "note" in data, "Should have note field"
        
        print(f"✓ Timeout config: {len(timeouts)} task types configured")
        for task_type, timeout in timeouts.items():
            print(f"  - {task_type}: {timeout}s")
    
    def test_active_tasks_endpoint(self):
        """Test /api/tasks/active returns active task list"""
        response = requests.get(f"{BASE_URL}/api/tasks/active")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Should have count and tasks
        assert "count" in data, "Response should contain 'count' field"
        assert "tasks" in data, "Response should contain 'tasks' field"
        assert isinstance(data["tasks"], list), "tasks should be a list"
        assert data["count"] == len(data["tasks"]), "count should match tasks length"
        
        # Verify task structure if any exist
        if data["tasks"]:
            task = data["tasks"][0]
            assert "task_id" in task, "Task should have task_id"
            assert "task_type" in task, "Task should have task_type"
            assert "status" in task, "Task should have status"
            assert "progress" in task, "Task should have progress"
        
        print(f"✓ Active tasks: {data['count']} tasks running")
    
    def test_task_history_endpoint(self):
        """Test /api/tasks/history returns task history"""
        response = requests.get(f"{BASE_URL}/api/tasks/history")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Should have count and history
        assert "count" in data, "Response should contain 'count' field"
        assert "history" in data, "Response should contain 'history' field"
        assert isinstance(data["history"], list), "history should be a list"
        
        # Verify history item structure if any exist
        if data["history"]:
            item = data["history"][0]
            assert "task_id" in item, "History item should have task_id"
            assert "task_type" in item, "History item should have task_type"
            assert "status" in item, "History item should have status"
            assert "created_at" in item, "History item should have created_at"
        
        print(f"✓ Task history: {data['count']} tasks in history")
    
    def test_task_history_with_limit(self):
        """Test /api/tasks/history with limit parameter"""
        response = requests.get(f"{BASE_URL}/api/tasks/history?limit=5")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert len(data["history"]) <= 5, "Should respect limit parameter"
        
        print(f"✓ Task history with limit: {len(data['history'])} tasks (limit=5)")
    
    def test_task_history_with_type_filter(self):
        """Test /api/tasks/history with task_type filter"""
        response = requests.get(f"{BASE_URL}/api/tasks/history?task_type=model_training")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # All returned tasks should be of the specified type
        for task in data["history"]:
            assert task["task_type"] == "model_training", f"Expected model_training, got {task['task_type']}"
        
        print(f"✓ Task history filtered by type: {data['count']} model_training tasks")
    
    def test_task_history_invalid_type(self):
        """Test /api/tasks/history with invalid task_type"""
        response = requests.get(f"{BASE_URL}/api/tasks/history?task_type=invalid_type")
        assert response.status_code == 400, f"Expected 400 for invalid type, got {response.status_code}"
        
        print(f"✓ Invalid task type correctly rejected with 400")


class TestPortfolioSnapshotAPI:
    """Tests for Portfolio Snapshot endpoint"""
    
    def test_create_snapshot(self):
        """Test POST /api/portfolio/visualization/snapshot"""
        response = requests.post(f"{BASE_URL}/api/portfolio/visualization/snapshot")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "success" in data, "Response should contain 'success' field"
        
        if data.get("success"):
            assert "snapshot" in data, "Should have snapshot data"
            snapshot = data["snapshot"]
            assert "timestamp" in snapshot, "Snapshot should have timestamp"
            assert "total_value" in snapshot, "Snapshot should have total_value"
        
        print(f"✓ Snapshot creation: success={data.get('success')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
