"""
Advanced ML Features API Routes
================================
Bayesian networks, transfer learning, explainability, hyperparameter tuning.
"""

import logging
import numpy as np
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
import random
import math

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml-advanced", tags=["Advanced ML Features"])

_db = None


def set_db(db):
    global _db
    _db = db


async def get_database():
    global _db
    if _db is None:
        from server import db
        _db = db
    return _db


# =============================================================================
# MODELS
# =============================================================================

class HyperparameterTuningRequest(BaseModel):
    model_type: str = "gradient_boosting"
    symbol: str = "BTC/USD"
    n_trials: int = 50
    optimization_metric: str = "sharpe_ratio"
    search_space: Optional[Dict] = None


class TransferLearningRequest(BaseModel):
    source_coin: str = "BTC"
    target_coin: str = "ETH"
    fine_tune_epochs: int = 10
    freeze_layers: int = 3


class ExplainabilityRequest(BaseModel):
    model_id: str
    sample_data: Optional[Dict] = None
    method: str = "shap"  # shap, lime, feature_importance


# =============================================================================
# BAYESIAN NEURAL NETWORKS
# =============================================================================

@router.get("/bayesian/models")
async def get_bayesian_models(db = Depends(get_database)):
    """Get available Bayesian neural network models"""
    
    models = [
        {
            "model_id": "bnn-price-predictor",
            "name": "Bayesian Price Predictor",
            "type": "bayesian_lstm",
            "description": "LSTM with Monte Carlo Dropout for uncertainty estimation",
            "uncertainty_type": "epistemic",
            "dropout_rate": 0.2,
            "mc_samples": 100,
            "supported_coins": ["BTC", "ETH", "SOL", "ARB"],
            "metrics": {
                "mean_calibration_error": 0.045,
                "coverage_90": 0.892,
                "sharpness": 0.023
            },
            "status": "active"
        },
        {
            "model_id": "bnn-volatility",
            "name": "Bayesian Volatility Model",
            "type": "variational_inference",
            "description": "Variational inference for volatility prediction with full posterior",
            "uncertainty_type": "aleatoric+epistemic",
            "prior": "gaussian",
            "supported_coins": ["BTC", "ETH"],
            "metrics": {
                "mean_calibration_error": 0.038,
                "coverage_90": 0.908,
                "sharpness": 0.019
            },
            "status": "active"
        },
        {
            "model_id": "bnn-ensemble",
            "name": "Deep Ensemble",
            "type": "deep_ensemble",
            "description": "Ensemble of 5 neural networks for robust uncertainty",
            "n_models": 5,
            "uncertainty_type": "epistemic",
            "supported_coins": ["BTC", "ETH", "SOL", "LINK", "DOGE"],
            "metrics": {
                "mean_calibration_error": 0.032,
                "coverage_90": 0.915,
                "sharpness": 0.021
            },
            "status": "active"
        }
    ]
    
    return {"models": models, "total": len(models)}


@router.post("/bayesian/predict")
async def bayesian_predict(
    model_id: str,
    symbol: str = "BTC/USD",
    horizon: int = 24,
    confidence_levels: List[float] = [0.5, 0.75, 0.9, 0.95],
    db = Depends(get_database)
):
    """Get prediction with uncertainty bounds from Bayesian model"""
    
    # Simulate Bayesian prediction with uncertainty
    base_price = 45000 if "BTC" in symbol else 2500 if "ETH" in symbol else 100
    
    predictions = []
    current_price = base_price
    
    for h in range(1, horizon + 1):
        # Mean prediction with random walk
        drift = random.gauss(0, 0.002)
        current_price = current_price * (1 + drift)
        
        # Uncertainty grows with horizon
        base_uncertainty = current_price * 0.01  # 1% base
        uncertainty = base_uncertainty * math.sqrt(h)
        
        # Calculate confidence intervals
        intervals = {}
        for conf in confidence_levels:
            z_score = {0.5: 0.674, 0.75: 1.15, 0.9: 1.645, 0.95: 1.96, 0.99: 2.576}.get(conf, 1.96)
            intervals[f"{int(conf*100)}%"] = {
                "lower": round(current_price - z_score * uncertainty, 2),
                "upper": round(current_price + z_score * uncertainty, 2)
            }
        
        predictions.append({
            "hour": h,
            "timestamp": (datetime.now(timezone.utc) + timedelta(hours=h)).isoformat(),
            "mean": round(current_price, 2),
            "std": round(uncertainty, 2),
            "intervals": intervals,
            "epistemic_uncertainty": round(uncertainty * 0.4, 2),
            "aleatoric_uncertainty": round(uncertainty * 0.6, 2)
        })
    
    # Overall prediction summary
    final = predictions[-1]
    
    return {
        "model_id": model_id,
        "symbol": symbol,
        "current_price": base_price,
        "predictions": predictions,
        "summary": {
            "horizon_hours": horizon,
            "expected_price": final["mean"],
            "expected_return": round((final["mean"] - base_price) / base_price * 100, 2),
            "uncertainty_90": final["intervals"]["90%"],
            "total_uncertainty": final["std"],
            "uncertainty_decomposition": {
                "epistemic": final["epistemic_uncertainty"],
                "aleatoric": final["aleatoric_uncertainty"]
            }
        },
        "confidence_levels": confidence_levels,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


# =============================================================================
# TRANSFER LEARNING
# =============================================================================

@router.get("/transfer/available-models")
async def get_transfer_models(db = Depends(get_database)):
    """Get models available for transfer learning"""
    
    models = [
        {
            "model_id": "pretrained-crypto-encoder",
            "name": "Crypto Market Encoder",
            "source_coins": ["BTC", "ETH"],
            "architecture": "transformer",
            "pretrain_data": "2 years crypto data",
            "embedding_dim": 256,
            "transferable_layers": 6,
            "performance": {
                "btc_sharpe": 1.85,
                "eth_sharpe": 1.72
            }
        },
        {
            "model_id": "defi-pattern-recognizer",
            "name": "DeFi Pattern Recognizer",
            "source_coins": ["ETH", "AAVE", "UNI"],
            "architecture": "cnn_lstm",
            "pretrain_data": "DeFi protocol metrics",
            "embedding_dim": 128,
            "transferable_layers": 4,
            "performance": {
                "avg_accuracy": 0.68,
                "avg_profit_factor": 1.45
            }
        },
        {
            "model_id": "cross-market-momentum",
            "name": "Cross-Market Momentum",
            "source_coins": ["BTC", "ETH", "SOL", "AVAX"],
            "architecture": "attention_network",
            "pretrain_data": "Multi-exchange orderbook",
            "embedding_dim": 512,
            "transferable_layers": 8,
            "performance": {
                "momentum_capture": 0.72,
                "signal_quality": 0.65
            }
        }
    ]
    
    return {"models": models}


@router.post("/transfer/train")
async def train_transfer_model(
    request: TransferLearningRequest,
    db = Depends(get_database)
):
    """Start transfer learning from source to target coin"""
    
    job_id = str(uuid.uuid4())
    
    # Simulate transfer learning job
    job = {
        "job_id": job_id,
        "source_coin": request.source_coin,
        "target_coin": request.target_coin,
        "fine_tune_epochs": request.fine_tune_epochs,
        "freeze_layers": request.freeze_layers,
        "status": "running",
        "progress": 0,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "estimated_completion": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    }
    
    await db.transfer_learning_jobs.insert_one(job)
    
    return {
        "job_id": job_id,
        "status": "started",
        "message": f"Transfer learning from {request.source_coin} to {request.target_coin} initiated",
        "config": request.dict()
    }


@router.get("/transfer/status/{job_id}")
async def get_transfer_status(job_id: str, db = Depends(get_database)):
    """Get transfer learning job status"""
    
    # Simulate completed job
    return {
        "job_id": job_id,
        "status": "completed",
        "progress": 100,
        "metrics": {
            "source_performance": {"sharpe": 1.85, "accuracy": 0.62},
            "target_performance_before": {"sharpe": 0.45, "accuracy": 0.51},
            "target_performance_after": {"sharpe": 1.42, "accuracy": 0.59},
            "improvement": {
                "sharpe_gain": "+215%",
                "accuracy_gain": "+15.7%"
            }
        },
        "training_curve": [
            {"epoch": 1, "loss": 0.45, "val_loss": 0.52},
            {"epoch": 2, "loss": 0.38, "val_loss": 0.44},
            {"epoch": 3, "loss": 0.32, "val_loss": 0.38},
            {"epoch": 4, "loss": 0.28, "val_loss": 0.34},
            {"epoch": 5, "loss": 0.24, "val_loss": 0.31},
            {"epoch": 6, "loss": 0.21, "val_loss": 0.29},
            {"epoch": 7, "loss": 0.19, "val_loss": 0.27},
            {"epoch": 8, "loss": 0.17, "val_loss": 0.26},
            {"epoch": 9, "loss": 0.16, "val_loss": 0.25},
            {"epoch": 10, "loss": 0.15, "val_loss": 0.24}
        ]
    }


# =============================================================================
# EXPLAINABILITY (SHAP/LIME)
# =============================================================================

@router.get("/explain/models")
async def get_explainable_models(db = Depends(get_database)):
    """Get models with explainability support"""
    
    return {
        "models": [
            {
                "model_id": "xgb-signal-generator",
                "name": "XGBoost Signal Generator",
                "explainability": ["shap", "feature_importance", "partial_dependence"],
                "n_features": 45
            },
            {
                "model_id": "rf-trend-classifier",
                "name": "Random Forest Trend Classifier",
                "explainability": ["shap", "lime", "feature_importance"],
                "n_features": 32
            },
            {
                "model_id": "lstm-price-predictor",
                "name": "LSTM Price Predictor",
                "explainability": ["attention_weights", "gradient_saliency"],
                "n_features": 28
            }
        ]
    }


@router.post("/explain/shap")
async def get_shap_explanation(
    model_id: str,
    symbol: str = "BTC/USD",
    n_samples: int = 100,
    db = Depends(get_database)
):
    """Get SHAP values for model explanation"""
    
    # Feature names for crypto trading
    features = [
        "price_momentum_1h", "price_momentum_4h", "price_momentum_24h",
        "volume_change_1h", "volume_change_24h", "rsi_14",
        "macd_signal", "macd_histogram", "bollinger_position",
        "orderbook_imbalance", "funding_rate", "open_interest_change",
        "btc_correlation", "eth_correlation", "market_sentiment",
        "fear_greed_index", "twitter_sentiment", "whale_activity",
        "exchange_inflow", "exchange_outflow", "stablecoin_ratio"
    ]
    
    # Generate SHAP values (simulated)
    shap_values = {}
    for feature in features:
        # Random importance with some structure
        base_importance = random.uniform(-0.5, 0.5)
        shap_values[feature] = {
            "mean_abs_shap": round(abs(base_importance) * 0.1, 4),
            "mean_shap": round(base_importance * 0.1, 4),
            "std_shap": round(random.uniform(0.01, 0.05), 4)
        }
    
    # Sort by importance
    sorted_features = sorted(
        shap_values.items(),
        key=lambda x: x[1]["mean_abs_shap"],
        reverse=True
    )
    
    # Top features
    top_features = [
        {"feature": f, "importance": v["mean_abs_shap"], "direction": "positive" if v["mean_shap"] > 0 else "negative"}
        for f, v in sorted_features[:10]
    ]
    
    # Interaction effects
    interactions = [
        {"feature1": "rsi_14", "feature2": "macd_signal", "interaction_strength": 0.045},
        {"feature1": "volume_change_1h", "feature2": "orderbook_imbalance", "interaction_strength": 0.038},
        {"feature1": "fear_greed_index", "feature2": "whale_activity", "interaction_strength": 0.032}
    ]
    
    return {
        "model_id": model_id,
        "symbol": symbol,
        "method": "shap",
        "n_samples": n_samples,
        "shap_values": dict(sorted_features),
        "top_features": top_features,
        "feature_interactions": interactions,
        "global_importance": [
            {"feature": f, "importance": v["mean_abs_shap"]} 
            for f, v in sorted_features
        ],
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


@router.post("/explain/lime")
async def get_lime_explanation(
    model_id: str,
    symbol: str = "BTC/USD",
    db = Depends(get_database)
):
    """Get LIME explanation for a single prediction"""
    
    # Generate LIME explanation for current prediction
    prediction = {
        "class": "bullish",
        "probability": 0.72,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Local feature contributions
    contributions = [
        {"feature": "rsi_14", "value": 45.2, "contribution": 0.15, "direction": "positive"},
        {"feature": "macd_histogram", "value": 0.0023, "contribution": 0.12, "direction": "positive"},
        {"feature": "volume_change_1h", "value": 1.25, "contribution": 0.09, "direction": "positive"},
        {"feature": "fear_greed_index", "value": 62, "contribution": 0.08, "direction": "positive"},
        {"feature": "orderbook_imbalance", "value": 0.15, "contribution": 0.06, "direction": "positive"},
        {"feature": "funding_rate", "value": 0.0001, "contribution": -0.03, "direction": "negative"},
        {"feature": "exchange_inflow", "value": 1500, "contribution": -0.05, "direction": "negative"}
    ]
    
    return {
        "model_id": model_id,
        "symbol": symbol,
        "method": "lime",
        "prediction": prediction,
        "local_explanation": contributions,
        "intercept": 0.50,
        "r_squared": 0.85,
        "explanation_summary": "The bullish prediction is primarily driven by favorable RSI (45.2) and positive MACD histogram, indicating momentum. Volume increase supports the signal. Slightly offset by recent exchange inflows.",
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


# =============================================================================
# HYPERPARAMETER TUNING
# =============================================================================

@router.post("/tuning/start")
async def start_hyperparameter_tuning(
    request: HyperparameterTuningRequest,
    db = Depends(get_database)
):
    """Start automated hyperparameter tuning"""
    
    job_id = str(uuid.uuid4())
    
    # Default search space
    default_search_space = {
        "gradient_boosting": {
            "n_estimators": {"type": "int", "low": 50, "high": 500},
            "max_depth": {"type": "int", "low": 3, "high": 15},
            "learning_rate": {"type": "float", "low": 0.01, "high": 0.3, "log": True},
            "min_child_weight": {"type": "int", "low": 1, "high": 10},
            "subsample": {"type": "float", "low": 0.5, "high": 1.0},
            "colsample_bytree": {"type": "float", "low": 0.5, "high": 1.0}
        },
        "lstm": {
            "hidden_size": {"type": "int", "low": 32, "high": 256},
            "num_layers": {"type": "int", "low": 1, "high": 4},
            "dropout": {"type": "float", "low": 0.1, "high": 0.5},
            "learning_rate": {"type": "float", "low": 0.0001, "high": 0.01, "log": True},
            "batch_size": {"type": "categorical", "choices": [16, 32, 64, 128]}
        }
    }
    
    search_space = request.search_space or default_search_space.get(request.model_type, {})
    
    job = {
        "job_id": job_id,
        "model_type": request.model_type,
        "symbol": request.symbol,
        "n_trials": request.n_trials,
        "optimization_metric": request.optimization_metric,
        "search_space": search_space,
        "status": "running",
        "progress": 0,
        "best_score": None,
        "best_params": None,
        "started_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.tuning_jobs.insert_one(job)
    
    return {
        "job_id": job_id,
        "status": "started",
        "n_trials": request.n_trials,
        "search_space": search_space,
        "estimated_time_minutes": request.n_trials * 0.5
    }


@router.get("/tuning/status/{job_id}")
async def get_tuning_status(job_id: str, db = Depends(get_database)):
    """Get hyperparameter tuning job status"""
    
    # Simulate completed tuning
    trials = []
    for i in range(50):
        trials.append({
            "trial": i + 1,
            "params": {
                "n_estimators": random.randint(50, 500),
                "max_depth": random.randint(3, 15),
                "learning_rate": round(random.uniform(0.01, 0.3), 4),
                "subsample": round(random.uniform(0.5, 1.0), 2)
            },
            "score": round(random.uniform(0.8, 2.2), 3),
            "duration_seconds": round(random.uniform(10, 60), 1)
        })
    
    # Best trial
    best_trial = max(trials, key=lambda x: x["score"])
    
    return {
        "job_id": job_id,
        "status": "completed",
        "progress": 100,
        "n_trials_completed": 50,
        "best_trial": best_trial,
        "best_params": best_trial["params"],
        "best_score": best_trial["score"],
        "optimization_history": [{"trial": t["trial"], "score": t["score"]} for t in trials],
        "parameter_importance": [
            {"param": "learning_rate", "importance": 0.35},
            {"param": "n_estimators", "importance": 0.28},
            {"param": "max_depth", "importance": 0.22},
            {"param": "subsample", "importance": 0.15}
        ],
        "completed_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/tuning/history")
async def get_tuning_history(
    limit: int = 10,
    db = Depends(get_database)
):
    """Get recent tuning jobs"""
    
    jobs = await db.tuning_jobs.find(
        {},
        {"_id": 0}
    ).sort("started_at", -1).limit(limit).to_list(limit)
    
    return {"jobs": jobs, "total": len(jobs)}
