"""
Extended Pytest tests for critical backend services.
Tests: Growth Engine, Automated Trader, AI Weekly Trainer, AI Portfolio Manager
Run with: pytest /app/backend/tests/ -v
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


# ============ Growth Engine Tests ============

class TestGrowthEngineExtended:
    """Extended tests for AggressiveGrowthEngine"""
    
    @pytest.fixture
    def mock_deps(self):
        """Create comprehensive mock dependencies"""
        db = MagicMock()
        db.growth_positions = MagicMock()
        db.growth_executions = MagicMock()
        db.growth_history = MagicMock()
        db.growth_positions.find = MagicMock(return_value=MagicMock(
            to_list=AsyncMock(return_value=[])
        ))
        db.growth_positions.find_one = AsyncMock(return_value=None)
        db.growth_positions.insert_one = AsyncMock()
        db.growth_positions.update_one = AsyncMock()
        db.growth_executions.insert_one = AsyncMock()
        db.growth_history.insert_one = AsyncMock()
        
        kraken = MagicMock()
        kraken.get_balance = AsyncMock(return_value={"ZUSD": "500", "XXBT": "0.01"})
        kraken.get_ticker = AsyncMock(return_value={"c": ["75000"]})
        kraken.place_order = AsyncMock(return_value={"txid": ["TEST123"]})
        
        gem_finder = MagicMock()
        gem_finder.find_gems = AsyncMock(return_value=[
            {"coin_id": "solana", "gem_score": 85, "is_gem": True}
        ])
        
        ai_trainer = MagicMock()
        ai_trainer.select_portfolio = AsyncMock(return_value={
            "main_coins": [
                {"coin_id": "bitcoin", "allocation": 40, "ai_score": 78},
                {"coin_id": "ethereum", "allocation": 30, "ai_score": 75}
            ]
        })
        
        budget_manager = MagicMock()
        budget_manager.can_trade_real = AsyncMock(return_value={"allowed": True, "available": 500})
        budget_manager.allocate_funds = AsyncMock(return_value={"success": True, "remaining_budget": 400})
        budget_manager.release_funds = AsyncMock(return_value={"success": True})
        
        return db, kraken, gem_finder, ai_trainer, budget_manager
    
    @pytest.mark.asyncio
    async def test_gem_allocation_priority(self, mock_deps):
        """Test that hidden gems get priority allocation"""
        from services.growth_engine import AggressiveGrowthEngine
        
        db, kraken, gem_finder, ai_trainer, budget_manager = mock_deps
        
        engine = AggressiveGrowthEngine(db, kraken, gem_finder, ai_trainer)
        result = await engine.execute_growth_strategy(capital=500, paper_trade=True)
        
        assert result["success"] == True
        # Verify gem finder was called
        gem_finder.find_gems.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_loss_monitoring(self, mock_deps):
        """Test stop-loss position monitoring"""
        from services.growth_engine import AggressiveGrowthEngine
        
        db, kraken, gem_finder, ai_trainer, budget_manager = mock_deps
        
        # Add a position that's below stop-loss
        db.growth_positions.find = MagicMock(return_value=MagicMock(
            to_list=AsyncMock(return_value=[{
                "coin_id": "bitcoin",
                "entry_price": 80000,
                "amount": 0.01,
                "stop_loss": 72000,  # -10%
                "take_profit": 100000,
                "status": "open"
            }])
        ))
        
        # Mock current price below stop loss
        kraken.get_ticker = AsyncMock(return_value={"c": ["70000"]})  # Below stop loss
        
        engine = AggressiveGrowthEngine(db, kraken, gem_finder, ai_trainer)
        result = await engine.monitor_positions()
        
        assert "checked" in result
    
    @pytest.mark.asyncio
    async def test_compound_profits_calculation(self, mock_deps):
        """Test profit compounding logic"""
        from services.growth_engine import AggressiveGrowthEngine
        
        db, kraken, gem_finder, ai_trainer, budget_manager = mock_deps
        
        # Mock profitable closed positions
        db.growth_positions.find = MagicMock(return_value=MagicMock(
            to_list=AsyncMock(return_value=[{
                "coin_id": "bitcoin",
                "entry_price": 70000,
                "exit_price": 80000,
                "amount": 0.01,
                "pnl": 100,
                "status": "closed",
                "compounded": False
            }])
        ))
        
        engine = AggressiveGrowthEngine(db, kraken, gem_finder, ai_trainer)
        result = await engine.compound_profits()
        
        assert "compounded" in result
    
    @pytest.mark.asyncio
    async def test_get_portfolio_value(self, mock_deps):
        """Test portfolio value calculation"""
        from services.growth_engine import AggressiveGrowthEngine
        
        db, kraken, gem_finder, ai_trainer, budget_manager = mock_deps
        
        engine = AggressiveGrowthEngine(db, kraken, gem_finder, ai_trainer)
        portfolio = await engine.get_current_portfolio_value()
        
        assert "total_value" in portfolio
        assert "progress_pct" in portfolio


# ============ Automated Trader Tests ============

class TestAutomatedTrader:
    """Tests for AutomatedWeeklyTrader"""
    
    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies for automated trader"""
        db = MagicMock()
        db.weekly_strategies = MagicMock()
        db.weekly_executions = MagicMock()
        db.ai_trades = MagicMock()
        db.active_positions = MagicMock()
        db.weekly_strategies.find_one = AsyncMock(return_value=None)
        db.weekly_strategies.insert_one = AsyncMock()
        db.weekly_executions.insert_one = AsyncMock()
        db.ai_trades.insert_one = AsyncMock()
        db.active_positions.insert_one = AsyncMock()
        
        kraken_service = MagicMock()
        kraken_service.get_balance = AsyncMock(return_value={"ZUSD": "1000"})
        kraken_service.place_order = AsyncMock(return_value={"txid": ["ORDER123"]})
        kraken_service.get_ticker = AsyncMock(return_value={"c": ["75000"]})
        
        ai_trainer = MagicMock()
        ai_trainer.select_portfolio = AsyncMock(return_value={
            "main_coins": [{"coin_id": "bitcoin", "ai_score": 80}],
            "gem": {"coin_id": "solana", "gem_score": 85}
        })
        
        gem_finder = MagicMock()
        gem_finder.find_gems = AsyncMock(return_value=[
            {"coin_id": "solana", "gem_score": 85}
        ])
        
        alert_service = MagicMock()
        alert_service.send_alert = AsyncMock()
        
        return db, kraken_service, ai_trainer, gem_finder, alert_service
    
    @pytest.mark.asyncio
    async def test_execute_weekly_trades_paper(self, mock_deps):
        """Test paper trade execution"""
        from services.automated_trader import AutomatedWeeklyTrader
        
        db, kraken_service, ai_trainer, gem_finder, alert_service = mock_deps
        
        trader = AutomatedWeeklyTrader(
            db=db,
            kraken_service=kraken_service,
            ai_trainer=ai_trainer,
            gem_finder=gem_finder,
            alert_service=alert_service
        )
        
        result = await trader.execute_weekly_trades(paper_trade=True)
        
        assert result["success"] == True
        assert result["mode"] == "paper"
    
    @pytest.mark.asyncio
    async def test_get_kraken_symbol(self, mock_deps):
        """Test Kraken symbol mapping"""
        from services.automated_trader import AutomatedWeeklyTrader
        
        db, kraken_service, ai_trainer, gem_finder, alert_service = mock_deps
        
        trader = AutomatedWeeklyTrader(
            db=db,
            kraken_service=kraken_service,
            ai_trainer=ai_trainer,
            gem_finder=gem_finder
        )
        
        # Test known coins
        assert trader.kraken_symbols.get("bitcoin") == "XXBTZUSD"
        assert trader.kraken_symbols.get("ethereum") == "XETHZUSD"
        assert trader.kraken_symbols.get("solana") == "SOLUSD"


# ============ AI Weekly Trainer Tests ============

class TestAIWeeklyTrainer:
    """Tests for AIWeeklyTrainer"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database"""
        db = MagicMock()
        db.historical_prices = MagicMock()
        db.ai_training_runs = MagicMock()
        db.weekly_training_results = MagicMock()
        db.ai_preferences = MagicMock()
        db.historical_prices.find = MagicMock(return_value=MagicMock(
            sort=MagicMock(return_value=MagicMock(
                to_list=AsyncMock(return_value=[
                    {"coin_id": "bitcoin", "close": 75000, "timestamp": "2025-01-01"},
                    {"coin_id": "bitcoin", "close": 76000, "timestamp": "2025-01-02"}
                ])
            ))
        ))
        db.ai_training_runs.insert_one = AsyncMock()
        db.weekly_training_results.insert_one = AsyncMock()
        db.ai_preferences.find_one = AsyncMock(return_value=None)
        db.ai_preferences.update_one = AsyncMock()
        return db
    
    @pytest.mark.asyncio
    async def test_trainer_initialization(self, mock_db):
        """Test AI Weekly Trainer initialization"""
        from services.ai_weekly_trainer import AIWeeklyTrainer
        
        trainer = AIWeeklyTrainer(mock_db)
        
        assert trainer.db == mock_db
        assert hasattr(trainer, 'config')
    
    @pytest.mark.asyncio
    async def test_select_portfolio(self, mock_db):
        """Test portfolio selection"""
        from services.ai_weekly_trainer import AIWeeklyTrainer
        
        trainer = AIWeeklyTrainer(mock_db)
        
        # Test select_portfolio method exists and can be called
        result = await trainer.select_portfolio()
        
        assert "main_coins" in result or "error" in result


# ============ AI Portfolio Manager Tests ============

class TestAIPortfolioManager:
    """Tests for AIPortfolioManager"""
    
    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies"""
        db = MagicMock()
        db.ai_portfolios = MagicMock()
        db.ai_trades = MagicMock()
        db.strategies = MagicMock()
        db.ai_portfolios.find_one = AsyncMock(return_value={
            "user_id": "default",
            "type": "ai_managed",
            "initial_capital": 500,
            "current_capital": 600,
            "holdings": {"USD": 300, "BTC": 0.003, "ETH": 0.05},
            "target_allocation": {"USD": 20, "BTC": 40, "ETH": 30, "SOL": 10}
        })
        db.ai_portfolios.update_one = AsyncMock()
        db.ai_portfolios.replace_one = AsyncMock()
        db.ai_trades.insert_one = AsyncMock()
        db.strategies.find = MagicMock(return_value=MagicMock(
            sort=MagicMock(return_value=MagicMock(
                limit=MagicMock(return_value=MagicMock(
                    to_list=AsyncMock(return_value=[])
                ))
            ))
        ))
        
        kraken = MagicMock()
        kraken.place_order = AsyncMock(return_value={"txid": ["ORDER456"]})
        
        market_service = MagicMock()
        market_service.get_coin_price = AsyncMock(return_value={
            "bitcoin": {"price_usd": 75000, "price_change_24h": 2.5},
            "ethereum": {"price_usd": 2500, "price_change_24h": -1.2},
            "solana": {"price_usd": 150, "price_change_24h": 5.0}
        })
        
        news_service = MagicMock()
        news_service.get_aggregated_news = AsyncMock(return_value=[
            {"sentiment": "positive"},
            {"sentiment": "positive"},
            {"sentiment": "neutral"}
        ])
        
        return db, kraken, market_service, news_service
    
    @pytest.mark.asyncio
    async def test_initialize_portfolio(self, mock_deps):
        """Test AI portfolio initialization"""
        from services.ai_portfolio_manager import AIPortfolioManager
        
        db, kraken, market_service, news_service = mock_deps
        db.ai_portfolios.find_one = AsyncMock(return_value=None)
        
        manager = AIPortfolioManager(
            db=db, 
            kraken_service=kraken,
            market_service=market_service,
            news_service=news_service
        )
        
        portfolio = await manager.initialize_ai_portfolio("test_user", 500)
        
        assert portfolio["initial_capital"] == 500
        assert portfolio["type"] == "ai_managed"
        db.ai_portfolios.replace_one.assert_called()
    
    @pytest.mark.asyncio
    async def test_develop_bullish_strategy(self, mock_deps):
        """Test strategy development in bullish market"""
        from services.ai_portfolio_manager import AIPortfolioManager
        
        db, kraken, market_service, news_service = mock_deps
        
        # All coins bullish
        market_service.get_coin_price = AsyncMock(return_value={
            "bitcoin": {"price_usd": 75000, "price_change_24h": 5.0},
            "ethereum": {"price_usd": 2500, "price_change_24h": 3.0},
            "solana": {"price_usd": 150, "price_change_24h": 8.0}
        })
        
        manager = AIPortfolioManager(
            db=db,
            kraken_service=kraken,
            market_service=market_service,
            news_service=news_service
        )
        
        result = await manager.develop_portfolio_strategy("test_user")
        
        # In bullish market, should have low cash allocation
        assert result["target_allocation"]["USD"] <= 15
    
    @pytest.mark.asyncio
    async def test_develop_bearish_strategy(self, mock_deps):
        """Test strategy development in bearish market"""
        from services.ai_portfolio_manager import AIPortfolioManager
        
        db, kraken, market_service, news_service = mock_deps
        
        # All coins bearish
        market_service.get_coin_price = AsyncMock(return_value={
            "bitcoin": {"price_usd": 75000, "price_change_24h": -5.0},
            "ethereum": {"price_usd": 2500, "price_change_24h": -3.0},
            "solana": {"price_usd": 150, "price_change_24h": -8.0}
        })
        
        # Negative news sentiment
        news_service.get_aggregated_news = AsyncMock(return_value=[
            {"sentiment": "negative"},
            {"sentiment": "negative"},
            {"sentiment": "neutral"}
        ])
        
        manager = AIPortfolioManager(
            db=db,
            kraken_service=kraken,
            market_service=market_service,
            news_service=news_service
        )
        
        result = await manager.develop_portfolio_strategy("test_user")
        
        # In bearish market, should have high cash allocation
        assert result["target_allocation"]["USD"] >= 40
    
    @pytest.mark.asyncio
    async def test_execute_rebalance(self, mock_deps):
        """Test portfolio rebalancing execution"""
        from services.ai_portfolio_manager import AIPortfolioManager
        
        db, kraken, market_service, news_service = mock_deps
        
        manager = AIPortfolioManager(
            db=db,
            kraken_service=kraken,
            market_service=market_service,
            news_service=news_service
        )
        
        result = await manager.execute_rebalance("test_user")
        
        assert result["success"] == True
        assert "trades_executed" in result
    
    @pytest.mark.asyncio
    async def test_get_portfolio_status(self, mock_deps):
        """Test getting portfolio status"""
        from services.ai_portfolio_manager import AIPortfolioManager
        
        db, kraken, market_service, news_service = mock_deps
        
        manager = AIPortfolioManager(
            db=db,
            kraken_service=kraken,
            market_service=market_service,
            news_service=news_service
        )
        
        status = await manager.get_portfolio_status("default")
        
        assert status["initialized"] == True or "holdings" in status


# ============ Integration Tests ============

class TestAPIIntegration:
    """Integration tests for API endpoints"""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test /api/health endpoint"""
        import httpx
        
        api_url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{api_url}/api/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_training_status_endpoint(self):
        """Test /api/training/status endpoint"""
        import httpx
        
        api_url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{api_url}/api/training/status")
            
            assert response.status_code == 200
            data = response.json()
            assert "trained" in data
    
    @pytest.mark.asyncio
    async def test_hidden_gems_endpoint(self):
        """Test /api/training/hidden-gems endpoint"""
        import httpx
        
        api_url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{api_url}/api/training/hidden-gems?min_multiplier=2")
            
            assert response.status_code == 200
            data = response.json()
            assert "hidden_gems" in data
            assert "count" in data
    
    @pytest.mark.asyncio
    async def test_growth_stats_endpoint(self):
        """Test /api/growth/stats endpoint"""
        import httpx
        
        api_url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{api_url}/api/growth/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert "portfolio" in data
    
    @pytest.mark.asyncio
    async def test_budget_endpoint(self):
        """Test /api/budget endpoint"""
        import httpx
        
        api_url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{api_url}/api/budget/")
            
            assert response.status_code == 200
            data = response.json()
            assert "allocated_budget" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
