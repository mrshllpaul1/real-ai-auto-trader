"""
AI Coin Selection and Weekly Simulation API Routes
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/ai-selection", tags=["AI Selection"])

# Global references (set during app startup)
db = None
coin_selector = None
simulation_runner = None


def set_dependencies(database, selector, runner):
    """Set dependencies from main app"""
    global db, coin_selector, simulation_runner
    db = database
    coin_selector = selector
    simulation_runner = runner


class SelectionRequest(BaseModel):
    week_start: Optional[str] = None  # ISO date string
    market_condition: Optional[str] = 'neutral'
    max_coins: Optional[int] = 5


class SimulationRequest(BaseModel):
    start_date: Optional[str] = '2009-01-01'
    end_date: Optional[str] = '2026-01-31'


@router.post("/select-coins")
async def select_best_coins(request: SelectionRequest):
    """
    Select the best coins for trading based on current conditions.
    Uses the Adaptive AI Coin Selection Engine.
    """
    if coin_selector is None:
        raise HTTPException(status_code=500, detail="Coin selector not initialized")
    
    try:
        # Parse week start date
        if request.week_start:
            week_start = datetime.fromisoformat(request.week_start)
        else:
            week_start = datetime.now()
        
        # Select best coins
        selected = await coin_selector.select_best_coins(
            week_start=week_start,
            market_condition=request.market_condition,
            max_coins=request.max_coins
        )
        
        return {
            'success': True,
            'week_start': week_start.isoformat(),
            'market_condition': request.market_condition,
            'selected_coins': selected,
            'total_selected': len(selected)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/selection-status")
async def get_selection_status():
    """Get current status of the coin selection engine"""
    if not coin_selector:
        raise HTTPException(status_code=500, detail="Coin selector not initialized")
    
    status = await coin_selector.get_selection_status()
    return status


@router.post("/run-simulation")
async def run_weekly_simulation(request: SimulationRequest, background_tasks: BackgroundTasks):
    """
    Run a full weekly paper trading simulation.
    This is a long-running task that runs in the background.
    """
    if not simulation_runner:
        raise HTTPException(status_code=500, detail="Simulation runner not initialized")
    
    try:
        start = datetime.fromisoformat(request.start_date)
        end = datetime.fromisoformat(request.end_date)
        
        # Start simulation in background
        async def run_sim():
            try:
                await simulation_runner.run_full_simulation(start, end)
            except Exception as e:
                print(f"Simulation error: {e}")
        
        background_tasks.add_task(lambda: asyncio.create_task(run_sim()))
        
        return {
            'success': True,
            'message': 'Simulation started in background',
            'start_date': start.isoformat(),
            'end_date': end.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/simulation-results")
async def get_simulation_results(limit: int = 10):
    """Get recent simulation results"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    results = await db.weekly_simulations.find(
        {}, {'_id': 0, 'weekly_results': 0}  # Exclude large weekly_results array
    ).sort('completed_at', -1).limit(limit).to_list(limit)
    
    return {
        'results': results,
        'count': len(results)
    }


@router.get("/simulation-results/{simulation_id}")
async def get_simulation_detail(simulation_id: str):
    """Get detailed results for a specific simulation"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    result = await db.weekly_simulations.find_one(
        {'_id': simulation_id},
        {'_id': 0}
    )
    
    if not result:
        # Try by completed_at
        result = await db.weekly_simulations.find_one(
            {},
            {'_id': 0}
        )
    
    if not result:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    return result


@router.post("/seed-historical-data")
async def seed_historical_data(background_tasks: BackgroundTasks):
    """
    Seed the database with historical price data.
    Required before running simulations.
    """
    from services.historical_data_seeder import HistoricalDataSeeder
    
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    seeder = HistoricalDataSeeder(db)
    
    # Run in background
    async def seed():
        try:
            await seeder.seed_extended_historical()
        except Exception as e:
            print(f"Seeding error: {e}")
    
    background_tasks.add_task(lambda: asyncio.create_task(seed()))
    
    return {
        'success': True,
        'message': 'Historical data seeding started in background'
    }


@router.get("/historical-data-status")
async def get_historical_data_status():
    """Check status of historical price data"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    total_records = await db.historical_prices.count_documents({})
    
    # Get unique coins
    coins = await db.historical_prices.distinct('coin_id')
    
    # Get date range
    oldest = await db.historical_prices.find_one(
        {}, {'_id': 0, 'timestamp': 1, 'coin_id': 1},
        sort=[('timestamp', 1)]
    )
    newest = await db.historical_prices.find_one(
        {}, {'_id': 0, 'timestamp': 1, 'coin_id': 1},
        sort=[('timestamp', -1)]
    )
    
    return {
        'total_records': total_records,
        'coins': coins,
        'coin_count': len(coins),
        'date_range': {
            'oldest': oldest.get('timestamp') if oldest else None,
            'newest': newest.get('timestamp') if newest else None
        },
        'ready_for_simulation': total_records > 1000
    }


# Import asyncio for background tasks
import asyncio
