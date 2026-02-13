"""
Tethys Trading API Routes
==========================
Endpoints for integrated trading loop, explainability, and hyperparameter evolution.
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import numpy as np

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tethys-trading", tags=["Tethys Trading"])

# Global references
_db = None
_trading_loop = None
_evolver = None


def set_db(db):
    """Set database reference"""
    global _db
    _db = db


class EvolutionConfig(BaseModel):
    generations: int = 10
    population_size: int = 20


class BacktestParams(BaseModel):
    sharpe_ratio: float = 0.5
    max_drawdown: float = 0.1
    win_rate: float = 0.55
    total_return: float = 0.05


# =============================================================================
# TRADING LOOP ENDPOINTS
# =============================================================================

@router.post("/start")
async def start_trading_loop(
    interval: int = 60,
    background_tasks: BackgroundTasks = None
):
    """Start continuous trading loop"""
    global _trading_loop, _db
    
    from services.tethys_trading import get_trading_loop
    _trading_loop = get_trading_loop(_db)
    
    if _trading_loop.is_running:
        return {"status": "already_running"}
    
    async def run_loop():
        await _trading_loop.initialize()
        await _trading_loop.run_continuous(interval)
    
    background_tasks.add_task(run_loop)
    
    # Persist state
    try:
        from services.state_persistence import get_state_persistence
        persistence = get_state_persistence(_db)
        if persistence:
            await persistence.set_state("tethys_trading", True, metadata={"interval": interval})
    except Exception as e:
        pass
    
    return {
        "status": "started",
        "interval": interval,
        "message": "Tethys trading loop started in background"
    }


@router.post("/stop")
async def stop_trading_loop():
    """Stop trading loop"""
    global _trading_loop, _db
    
    if not _trading_loop:
        return {"status": "not_running"}
    
    _trading_loop.stop()
    
    # Persist state
    try:
        from services.state_persistence import get_state_persistence
        persistence = get_state_persistence(_db)
        if persistence:
            await persistence.set_state("tethys_trading", False)
    except Exception as e:
        pass
    
    return {"status": "stopped"}


@router.get("/status")
async def get_trading_status():
    """Get trading loop status"""
    global _trading_loop, _db
    
    if not _trading_loop:
        from services.tethys_trading import get_trading_loop
        _trading_loop = get_trading_loop(_db)
    
    status = _trading_loop.get_status()
    
    # Check persisted state
    try:
        from services.state_persistence import get_state_persistence
        persistence = get_state_persistence(_db)
        if persistence:
            state = await persistence.get_state("tethys_trading")
            status["persisted_running"] = state.get("is_running", False) if state else False
    except Exception as e:
        status["persisted_running"] = None
    
    return status


@router.post("/tick")
async def process_single_tick(symbol: str = "BTC/USD"):
    """Process a single trading tick"""
    global _trading_loop, _db
    
    from services.tethys_trading import get_trading_loop
    _trading_loop = get_trading_loop(_db)
    
    if not _trading_loop._rainbow:
        await _trading_loop.initialize()
    
    result = await _trading_loop.process_tick(symbol)
    
    return result or {"status": "no_action", "symbol": symbol}


@router.get("/history")
async def get_trade_history(limit: int = 50):
    """Get recent trade history"""
    global _trading_loop
    
    if not _trading_loop:
        return {"trades": [], "count": 0}
    
    history = list(_trading_loop.trade_history)[-limit:]
    
    # Convert numpy types to native Python
    def convert(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.int32, np.int64)):
            return int(obj)
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(v) for v in obj]
        return obj
    
    return {
        "count": len(history),
        "trades": [convert(t) for t in history]
    }


# =============================================================================
# EXPLAINABILITY ENDPOINTS
# =============================================================================

@router.get("/explain/latest")
async def get_latest_explanation():
    """Get explanation for most recent decision"""
    global _trading_loop
    
    if not _trading_loop or not _trading_loop._explainer:
        return {"status": "no_data"}
    
    history = _trading_loop._explainer.importance_history
    if not history:
        return {"status": "no_decisions_yet"}
    
    return history[-1]


@router.get("/explain/summary")
async def get_explanation_summary():
    """Get feature importance summary"""
    global _trading_loop
    
    if not _trading_loop or not _trading_loop._explainer:
        from services.tethys_trading import TradingExplainer
        return {"status": "explainer_not_initialized"}
    
    return _trading_loop._explainer.get_feature_importance_summary()


@router.post("/explain/decision")
async def explain_specific_decision(
    symbol: str = "BTC/USD"
):
    """Generate explanation for a new decision"""
    global _trading_loop, _db
    
    from services.tethys_trading import get_trading_loop
    _trading_loop = get_trading_loop(_db)
    
    if not _trading_loop._rainbow:
        await _trading_loop.initialize()
    
    # Get current state
    order_book = _trading_loop._order_book.get_order_book(symbol)
    if not order_book or not order_book.snapshot_received:
        raise HTTPException(status_code=503, detail="Order book not available")
    
    state_sequence = _trading_loop._feature_extractor.get_sequence(symbol)
    
    # Get action and Q-values
    action = _trading_loop._rainbow.select_action(state_sequence, training=False)
    q_dist = _trading_loop._rainbow.online_network(
        state_sequence[np.newaxis, ...], training=False
    )
    q_values = _trading_loop._rainbow.c51.get_q_values(q_dist).numpy()[0]
    
    # Generate explanation
    explanation = _trading_loop._explainer.explain_decision(
        state_sequence, q_values, action
    )
    
    return {
        'symbol': symbol,
        'price': order_book.get_mid_price(),
        'explanation': explanation
    }


# =============================================================================
# HYPERPARAMETER EVOLUTION ENDPOINTS
# =============================================================================

@router.post("/evolve/start")
async def start_evolution(
    config: EvolutionConfig = None,
    background_tasks: BackgroundTasks = None
):
    """Start hyperparameter evolution"""
    global _evolver
    
    config = config or EvolutionConfig()
    
    from services.tethys_trading import HyperparameterEvolver
    _evolver = HyperparameterEvolver(population_size=config.population_size)
    
    async def evolution_loop():
        """Run evolution generations"""
        for gen in range(config.generations):
            # Simulate backtest for each individual
            fitnesses = []
            for individual in _evolver.population:
                # In production, this would run actual backtest
                # For now, simulate with random performance influenced by params
                simulated_results = simulate_backtest(individual)
                fitness = _evolver.evaluate_fitness(individual, simulated_results)
                fitnesses.append(fitness)
            
            _evolver.evolve(fitnesses)
            await asyncio.sleep(0.1)  # Yield control
        
        logger.info(f"Evolution complete: Best fitness = {_evolver.best_fitness:.4f}")
    
    background_tasks.add_task(evolution_loop)
    
    return {
        "status": "evolution_started",
        "generations": config.generations,
        "population_size": config.population_size
    }


def simulate_backtest(params: Dict) -> Dict:
    """
    Simulate backtest results based on hyperparameters.
    
    In production, this would run actual backtests.
    """
    # Better params generally lead to better results (with noise)
    base_sharpe = 0.5
    base_dd = 0.15
    base_wr = 0.52
    
    # Adjust based on params
    sharpe_adj = (
        (0.5 - abs(params['max_position_pct'] - 0.2)) +
        (params['sharpe_weight'] - 0.5) +
        np.random.normal(0, 0.2)
    )
    
    dd_adj = (
        params['max_drawdown_pct'] * 0.5 +
        (1 - params['cvar_weight']) * 0.1 +
        np.random.normal(0, 0.05)
    )
    
    wr_adj = (
        params['confidence_threshold'] * 0.1 +
        np.random.normal(0, 0.05)
    )
    
    return {
        'sharpe_ratio': max(0, base_sharpe + sharpe_adj),
        'max_drawdown': min(0.5, max(0.01, base_dd + dd_adj)),
        'win_rate': min(0.7, max(0.3, base_wr + wr_adj)),
        'total_return': np.random.normal(0.05, 0.1)
    }


@router.get("/evolve/status")
async def get_evolution_status():
    """Get evolution status"""
    global _evolver
    
    if not _evolver:
        return {"status": "not_started"}
    
    return _evolver.get_best_params()


@router.get("/evolve/population")
async def get_current_population():
    """Get current population"""
    global _evolver
    
    if not _evolver:
        return {"population": []}
    
    return {
        "generation": _evolver.generation,
        "population_size": len(_evolver.population),
        "population": _evolver.population[:5],  # Top 5
        "best_individual": _evolver.best_individual,
        "best_fitness": _evolver.best_fitness
    }


@router.post("/evolve/evaluate")
async def evaluate_params(params: BacktestParams):
    """Evaluate specific parameters"""
    global _evolver
    
    if not _evolver:
        from services.tethys_trading import HyperparameterEvolver
        _evolver = HyperparameterEvolver()
    
    # Use provided backtest results
    results = {
        'sharpe_ratio': params.sharpe_ratio,
        'max_drawdown': params.max_drawdown,
        'win_rate': params.win_rate,
        'total_return': params.total_return
    }
    
    fitness = _evolver.evaluate_fitness({}, results)
    
    return {
        'fitness': float(fitness),
        'input_params': results
    }


# =============================================================================
# INTEGRATED ENDPOINTS
# =============================================================================

@router.post("/full-cycle")
async def run_full_trading_cycle(symbol: str = "BTC/USD"):
    """
    Run a complete trading cycle:
    1. Get market data
    2. Generate decision
    3. Explain decision
    4. Risk check
    5. Return complete analysis
    """
    global _trading_loop, _db
    
    from services.tethys_trading import get_trading_loop
    _trading_loop = get_trading_loop(_db)
    
    if not _trading_loop._rainbow:
        await _trading_loop.initialize()
    
    # Process tick
    result = await _trading_loop.process_tick(symbol)
    
    if not result:
        return {"status": "no_action", "reason": "action_interval_not_met"}
    
    # Add evolution status
    if _evolver:
        result['evolution'] = {
            'generation': _evolver.generation,
            'best_fitness': _evolver.best_fitness
        }
    
    return result


@router.get("/dashboard")
async def get_full_dashboard():
    """Get complete Tethys trading dashboard"""
    global _trading_loop, _evolver, _db
    
    from services.tethys_trading import get_trading_loop
    _trading_loop = get_trading_loop(_db)
    
    dashboard = {
        'agent': 'Tethys',
        'trading_loop': _trading_loop.get_status() if _trading_loop else {'status': 'not_initialized'}
    }
    
    # Add explainer summary
    if _trading_loop and _trading_loop._explainer:
        dashboard['explainability'] = _trading_loop._explainer.get_feature_importance_summary()
    
    # Add evolution status
    if _evolver:
        dashboard['evolution'] = _evolver.get_best_params()
    else:
        dashboard['evolution'] = {'status': 'not_started'}
    
    # Add safety status
    if _trading_loop and _trading_loop._safety:
        dashboard['safety'] = _trading_loop._safety.get_full_status()
    
    return dashboard
