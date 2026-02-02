"""
Pytest tests for critical backend services.
Run with: pytest /app/backend/tests/ -v
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch


# ============ Budget Manager Tests ============

class TestBudgetManager:
    """Test Budget Manager service"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database"""
        db = MagicMock()
        db.trading_budgets = MagicMock()
        db.budget_allocations = MagicMock()
        db.budget_releases = MagicMock()
        return db
    
    @pytest.mark.asyncio
    async def test_get_budget_default(self, mock_db):
        """Test getting default budget when none exists"""
        from services.budget_manager import BudgetManager
        
        mock_db.trading_budgets.find_one = AsyncMock(return_value=None)
        
        manager = BudgetManager(mock_db)
        budget = await manager.get_budget()
        
        assert budget["allocated_budget"] == 0
        assert budget["real_trading_enabled"] == False
        assert budget["paper_budget"] == 500
    
    @pytest.mark.asyncio
    async def test_set_budget(self, mock_db):
        """Test setting a budget"""
        from services.budget_manager import BudgetManager
        
        mock_db.trading_budgets.find_one = AsyncMock(return_value=None)
        mock_db.trading_budgets.update_one = AsyncMock()
        
        manager = BudgetManager(mock_db)
        budget = await manager.set_budget(500, enable_real_trading=True)
        
        assert budget["allocated_budget"] == 500
        assert budget["available_budget"] == 500
        assert budget["real_trading_enabled"] == True
    
    @pytest.mark.asyncio
    async def test_cannot_trade_without_budget(self, mock_db):
        """Test that real trading is blocked without budget"""
        from services.budget_manager import BudgetManager
        
        mock_db.trading_budgets.find_one = AsyncMock(return_value={
            "user_id": "default",
            "allocated_budget": 0,
            "available_budget": 0,
            "real_trading_enabled": False
        })
        
        manager = BudgetManager(mock_db)
        result = await manager.can_trade_real(100)
        
        assert result["allowed"] == False
        assert "not enabled" in result["reason"]
    
    @pytest.mark.asyncio
    async def test_allocate_funds_success(self, mock_db):
        """Test successful fund allocation"""
        from services.budget_manager import BudgetManager
        
        mock_db.trading_budgets.find_one = AsyncMock(return_value={
            "user_id": "default",
            "allocated_budget": 500,
            "available_budget": 500,
            "used_budget": 0,
            "real_trading_enabled": True
        })
        mock_db.trading_budgets.update_one = AsyncMock()
        mock_db.budget_allocations.insert_one = AsyncMock()
        
        manager = BudgetManager(mock_db)
        result = await manager.allocate_funds(100, "test trade")
        
        assert result["success"] == True
        assert result["allocated"] == 100
        assert result["remaining_budget"] == 400
    
    @pytest.mark.asyncio
    async def test_allocate_funds_insufficient(self, mock_db):
        """Test allocation fails with insufficient funds"""
        from services.budget_manager import BudgetManager
        
        mock_db.trading_budgets.find_one = AsyncMock(return_value={
            "user_id": "default",
            "allocated_budget": 100,
            "available_budget": 50,
            "used_budget": 50,
            "real_trading_enabled": True
        })
        
        manager = BudgetManager(mock_db)
        result = await manager.allocate_funds(100, "test trade")
        
        assert result["success"] == False
        assert "Insufficient" in result["error"]


# ============ Scheduler Service Tests ============

class TestSchedulerService:
    """Test Scheduler Service"""
    
    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies"""
        db = MagicMock()
        db.scheduler_events = MagicMock()
        db.scheduler_executions = MagicMock()
        db.scheduler_events.insert_one = AsyncMock()
        db.scheduler_executions.insert_one = AsyncMock()
        db.scheduler_executions.find = MagicMock(return_value=MagicMock(
            sort=MagicMock(return_value=MagicMock(
                limit=MagicMock(return_value=MagicMock(
                    to_list=AsyncMock(return_value=[])
                ))
            ))
        ))
        
        growth_engine = MagicMock()
        growth_engine.monitor_positions = AsyncMock(return_value={"checked": 0})
        growth_engine.compound_profits = AsyncMock(return_value={"compounded": False})
        
        automated_trader = MagicMock()
        automated_trader.execute_weekly_trades = AsyncMock(return_value={"success": True, "trades": []})
        
        return db, growth_engine, automated_trader
    
    @pytest.mark.asyncio
    async def test_scheduler_status(self, mock_deps):
        """Test getting scheduler status"""
        from services.scheduler_service import SchedulerService
        
        db, growth_engine, automated_trader = mock_deps
        
        scheduler = SchedulerService(db, growth_engine, automated_trader)
        status = scheduler.get_status()
        
        assert "running" in status
        assert "jobs" in status
        assert "job_count" in status
    
    @pytest.mark.asyncio
    async def test_add_monitor_job(self, mock_deps):
        """Test adding growth monitor job"""
        from services.scheduler_service import SchedulerService
        
        db, growth_engine, automated_trader = mock_deps
        
        scheduler = SchedulerService(db, growth_engine, automated_trader)
        await scheduler.start()
        
        result = await scheduler.add_growth_monitor_job(interval_hours=1)
        
        assert result["success"] == True
        assert result["job_id"] == "growth_monitor"
        
        await scheduler.stop()
    
    @pytest.mark.asyncio
    async def test_setup_default_schedule(self, mock_deps):
        """Test setting up default schedule"""
        from services.scheduler_service import SchedulerService
        
        db, growth_engine, automated_trader = mock_deps
        
        scheduler = SchedulerService(db, growth_engine, automated_trader)
        await scheduler.start()
        
        result = await scheduler.setup_default_schedule(paper_trade=True)
        
        assert result["success"] == True
        assert result["jobs_configured"] == 3
        
        await scheduler.stop()


# ============ Growth Engine Tests ============

class TestGrowthEngine:
    """Test Growth Engine service"""
    
    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies"""
        db = MagicMock()
        db.growth_positions = MagicMock()
        db.growth_executions = MagicMock()
        db.growth_positions.find = MagicMock(return_value=MagicMock(
            to_list=AsyncMock(return_value=[])
        ))
        db.growth_positions.insert_one = AsyncMock()
        db.growth_executions.insert_one = AsyncMock()
        
        kraken = MagicMock()
        kraken.get_balance = AsyncMock(return_value={"ZUSD": "1000"})
        kraken.get_ticker = AsyncMock(return_value={"c": ["50000"]})
        
        gem_finder = MagicMock()
        gem_finder.find_gems = AsyncMock(return_value=[])
        
        ai_trainer = MagicMock()
        ai_trainer.select_portfolio = AsyncMock(return_value={"main_coins": []})
        
        budget_manager = MagicMock()
        budget_manager.can_trade_real = AsyncMock(return_value={"allowed": True, "available": 500})
        budget_manager.allocate_funds = AsyncMock(return_value={"success": True, "remaining_budget": 0})
        
        return db, kraken, gem_finder, ai_trainer, budget_manager
    
    @pytest.mark.asyncio
    async def test_get_portfolio_value(self, mock_deps):
        """Test getting portfolio value"""
        from services.growth_engine import AggressiveGrowthEngine
        
        db, kraken, gem_finder, ai_trainer, budget_manager = mock_deps
        
        engine = AggressiveGrowthEngine(db, kraken, gem_finder, ai_trainer)
        portfolio = await engine.get_current_portfolio_value()
        
        assert "total_value" in portfolio
        assert "progress_pct" in portfolio
        assert "current_multiplier" in portfolio
    
    @pytest.mark.asyncio
    async def test_paper_trade_execution(self, mock_deps):
        """Test paper trade execution"""
        from services.growth_engine import AggressiveGrowthEngine
        
        db, kraken, gem_finder, ai_trainer, budget_manager = mock_deps
        
        engine = AggressiveGrowthEngine(db, kraken, gem_finder, ai_trainer)
        result = await engine.execute_growth_strategy(capital=500, paper_trade=True)
        
        assert result["success"] == True
        assert "execution" in result
    
    @pytest.mark.asyncio
    async def test_real_trade_requires_budget(self, mock_deps):
        """Test real trade requires budget allocation"""
        from services.growth_engine import AggressiveGrowthEngine
        
        db, kraken, gem_finder, ai_trainer, budget_manager = mock_deps
        
        # Make budget check fail
        budget_manager.can_trade_real = AsyncMock(return_value={
            "allowed": False, 
            "reason": "No budget set"
        })
        
        engine = AggressiveGrowthEngine(
            db, kraken, gem_finder, ai_trainer, 
            budget_manager=budget_manager
        )
        result = await engine.execute_growth_strategy(capital=500, paper_trade=False)
        
        assert result["success"] == False
        assert "No budget" in result["error"]


# ============ API Endpoint Tests ============

class TestAPIEndpoints:
    """Test API endpoints"""
    
    @pytest.mark.asyncio
    async def test_growth_stats_endpoint(self):
        """Test /api/growth/stats endpoint"""
        import httpx
        import os
        
        api_url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_url}/api/growth/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert "portfolio" in data
            assert "statistics" in data
    
    @pytest.mark.asyncio
    async def test_scheduler_status_endpoint(self):
        """Test /api/scheduler/status endpoint"""
        import httpx
        import os
        
        api_url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_url}/api/scheduler/status")
            
            assert response.status_code == 200
            data = response.json()
            assert "running" in data
            assert "jobs" in data
    
    @pytest.mark.asyncio
    async def test_budget_endpoint(self):
        """Test /api/budget endpoint"""
        import httpx
        import os
        
        api_url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_url}/api/budget/")
            
            assert response.status_code == 200
            data = response.json()
            assert "allocated_budget" in data
            assert "real_trading_enabled" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
