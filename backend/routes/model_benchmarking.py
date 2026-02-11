"""
Model Benchmarking API Routes

Endpoints for running and viewing model performance benchmarks.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/model-benchmark", tags=["Model Benchmarking"])

# Service reference
_db = None
_benchmark_service = None


def init_router(db):
    """Initialize router with database"""
    global _db, _benchmark_service
    _db = db
    from services.model_benchmarking import get_benchmark_service
    _benchmark_service = get_benchmark_service(db)
    logger.info("✅ Model Benchmarking routes initialized")


class BenchmarkRequest(BaseModel):
    """Request model for benchmark"""
    days: int = 365
    symbols: Optional[List[str]] = None


@router.get("/status")
async def get_benchmark_status():
    """Get current benchmark status and last run info"""
    if _benchmark_service is None:
        return {
            "initialized": False,
            "message": "Benchmark service not initialized"
        }
    
    latest = await _benchmark_service.get_latest_benchmark()
    
    return {
        "initialized": True,
        "has_benchmark": latest is not None,
        "last_run": latest.get("run_at") if latest else None,
        "benchmark_id": latest.get("benchmark_id") if latest else None,
        "models_compared": list(latest.get("models", {}).keys()) if latest else [],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.post("/run")
async def run_benchmark(
    request: BenchmarkRequest,
    background_tasks: BackgroundTasks
):
    """
    Run a comprehensive model benchmark.
    
    Compares FinRL, Ensemble, Time-Series, and Combined strategies
    across different market conditions.
    """
    if _benchmark_service is None:
        raise HTTPException(status_code=503, detail="Benchmark service not initialized")
    
    try:
        # Run benchmark (can take a few seconds)
        results = await _benchmark_service.run_benchmark(
            days=request.days,
            symbols=request.symbols
        )
        
        return {
            "status": "completed",
            "benchmark_id": results.get("benchmark_id"),
            "period_days": results.get("period_days"),
            "models_tested": list(results.get("models", {}).keys()),
            "scenarios_tested": list(results.get("market_conditions", {}).keys()),
            "top_model": results.get("rankings", {}).get("overall", [{}])[0].get("model"),
            "recommendations_count": len(results.get("recommendations", [])),
            "run_at": results.get("run_at")
        }
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results")
async def get_benchmark_results():
    """Get the latest benchmark results"""
    if _benchmark_service is None:
        raise HTTPException(status_code=503, detail="Benchmark service not initialized")
    
    results = await _benchmark_service.get_latest_benchmark()
    
    if not results:
        return {
            "message": "No benchmark results available. Run a benchmark first.",
            "has_results": False
        }
    
    return {
        "has_results": True,
        **results
    }


@router.get("/rankings")
async def get_model_rankings():
    """Get model rankings from the latest benchmark"""
    if _benchmark_service is None:
        raise HTTPException(status_code=503, detail="Benchmark service not initialized")
    
    results = await _benchmark_service.get_latest_benchmark()
    
    if not results:
        return {
            "message": "No benchmark results available",
            "rankings": {}
        }
    
    return {
        "benchmark_id": results.get("benchmark_id"),
        "run_at": results.get("run_at"),
        "rankings": results.get("rankings", {}),
        "recommendations": results.get("recommendations", [])
    }


@router.get("/chart-data")
async def get_chart_data():
    """Get benchmark data formatted for frontend charts"""
    if _benchmark_service is None:
        raise HTTPException(status_code=503, detail="Benchmark service not initialized")
    
    results = await _benchmark_service.get_latest_benchmark()
    
    if not results:
        # Return sample data for visualization
        return {
            "has_data": False,
            "message": "Run benchmark to see real data",
            "performance_comparison": [
                {"model": "XGBoost/LightGBM Ensemble", "model_key": "ensemble", "avg_return": 0, "avg_sharpe": 0, "avg_win_rate": 50},
                {"model": "LSTM/GRU/Transformer", "model_key": "time_series", "avg_return": 0, "avg_sharpe": 0, "avg_win_rate": 50},
                {"model": "FinRL DRL Agent", "model_key": "finrl", "avg_return": 0, "avg_sharpe": 0, "avg_win_rate": 50},
                {"model": "Combined Strategy", "model_key": "combined", "avg_return": 0, "avg_sharpe": 0, "avg_win_rate": 50}
            ],
            "scenario_breakdown": [],
            "risk_metrics": []
        }
    
    chart_data = _benchmark_service.get_model_comparison_chart_data(results)
    chart_data["has_data"] = True
    chart_data["benchmark_id"] = results.get("benchmark_id")
    
    return chart_data


@router.get("/history")
async def get_benchmark_history(limit: int = Query(10, ge=1, le=50)):
    """Get historical benchmark results"""
    if _benchmark_service is None:
        raise HTTPException(status_code=503, detail="Benchmark service not initialized")
    
    history = await _benchmark_service.get_benchmark_history(limit)
    
    return {
        "count": len(history),
        "history": history
    }


@router.get("/model/{model_key}")
async def get_model_details(model_key: str):
    """Get detailed benchmark results for a specific model"""
    if _benchmark_service is None:
        raise HTTPException(status_code=503, detail="Benchmark service not initialized")
    
    results = await _benchmark_service.get_latest_benchmark()
    
    if not results:
        raise HTTPException(status_code=404, detail="No benchmark results available")
    
    models = results.get("models", {})
    
    if model_key not in models:
        raise HTTPException(
            status_code=404, 
            detail=f"Model '{model_key}' not found. Available: {list(models.keys())}"
        )
    
    model_data = models[model_key]
    
    # Find ranking position
    rankings = results.get("rankings", {}).get("overall", [])
    rank = next((r["rank"] for r in rankings if r["model"] == model_key), None)
    
    return {
        "model_key": model_key,
        "name": model_data.get("name"),
        "type": model_data.get("type"),
        "overall_rank": rank,
        "scenarios": model_data.get("scenarios", {}),
        "benchmark_id": results.get("benchmark_id")
    }


@router.get("/recommendations")
async def get_recommendations():
    """Get actionable recommendations based on benchmark results"""
    if _benchmark_service is None:
        raise HTTPException(status_code=503, detail="Benchmark service not initialized")
    
    results = await _benchmark_service.get_latest_benchmark()
    
    if not results:
        return {
            "recommendations": [{
                "type": "info",
                "title": "No Benchmark Data",
                "message": "Run a benchmark to get model recommendations"
            }]
        }
    
    return {
        "benchmark_id": results.get("benchmark_id"),
        "run_at": results.get("run_at"),
        "recommendations": results.get("recommendations", [])
    }
