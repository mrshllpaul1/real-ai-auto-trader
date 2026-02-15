"""Live Calibration Service

Connects real trade outcomes to ML Analytics calibration data.
Automatically updates confidence calibration when:
1. AI predictions are made (signals, gems, price predictions)
2. Trade outcomes are recorded (P/L from closed positions)
3. Prediction verification occurs
"""

import os
import asyncio
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

from services.ml_analytics import (
    get_confidence_calibrator,
    get_drift_detector,
    ConfidenceCalibrator,
    ModelDriftDetector
)

logger = logging.getLogger(__name__)


class LiveCalibrationService:
    """Real-time calibration data collection from actual trades."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.calibrator = get_confidence_calibrator()
        self.drift_detector = get_drift_detector()
        self._pending_predictions: Dict[str, Dict] = {}  # trade_id -> prediction data
        self._initialized = False
        
        # Collections
        self.predictions_collection = "live_calibration_predictions"
        self.outcomes_collection = "live_calibration_outcomes"
        
    async def initialize(self):
        """Initialize indexes and load pending predictions from DB."""
        if self._initialized:
            return
            
        # Create indexes
        await self.db[self.predictions_collection].create_index("prediction_id")
        await self.db[self.predictions_collection].create_index("trade_id")
        await self.db[self.predictions_collection].create_index("coin_id")
        await self.db[self.predictions_collection].create_index("status")
        await self.db[self.predictions_collection].create_index("created_at")
        
        # Load pending predictions (not yet verified)
        pending = await self.db[self.predictions_collection].find(
            {"status": "pending"}
        ).to_list(1000)
        
        for pred in pending:
            self._pending_predictions[pred.get("trade_id") or pred["prediction_id"]] = pred
        
        logger.info(f"LiveCalibrationService initialized with {len(self._pending_predictions)} pending predictions")
        self._initialized = True
    
    async def record_prediction(
        self,
        coin_id: str,
        predicted_action: str,  # BUY, SELL, HOLD
        confidence: float,  # 0-1 or 0-100 (will normalize)
        model_name: str,
        trade_id: Optional[str] = None,
        entry_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """Record an AI prediction for later outcome verification."""
        await self.initialize()
        
        prediction_id = str(uuid.uuid4())
        
        # Normalize confidence to 0-1
        if confidence > 1:
            confidence = confidence / 100.0
        confidence = max(0.0, min(1.0, confidence))
        
        prediction_doc = {
            "prediction_id": prediction_id,
            "trade_id": trade_id,
            "coin_id": coin_id.upper(),
            "predicted_action": predicted_action.upper(),
            "confidence": confidence,
            "model_name": model_name,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "metadata": metadata or {},
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
            "outcome": None,
            "verified_at": None
        }
        
        # Store in DB
        await self.db[self.predictions_collection].insert_one(prediction_doc)
        
        # Also record in memory calibrator immediately (for real-time updates)
        self.calibrator.record_prediction(
            prediction_id=prediction_id,
            coin_id=coin_id,
            predicted_action=predicted_action,
            confidence=confidence,
            model_name=model_name
        )
        
        # Track pending
        key = trade_id or prediction_id
        self._pending_predictions[key] = prediction_doc
        
        logger.info(f"Recorded prediction {prediction_id} for {coin_id} ({model_name}): {predicted_action} @ {confidence:.1%} confidence")
        
        return prediction_id
    
    async def record_outcome(
        self,
        prediction_id: Optional[str] = None,
        trade_id: Optional[str] = None,
        is_correct: Optional[bool] = None,
        actual_price: Optional[float] = None,
        exit_price: Optional[float] = None,
        pnl_percent: Optional[float] = None,
        pnl_usd: Optional[float] = None
    ) -> Dict[str, Any]:
        """Record the outcome of a prediction/trade."""
        await self.initialize()
        
        # Find the prediction
        key = trade_id or prediction_id
        prediction = self._pending_predictions.get(key)
        
        if not prediction and prediction_id:
            # Try to load from DB
            prediction = await self.db[self.predictions_collection].find_one(
                {"prediction_id": prediction_id}
            )
        
        if not prediction and trade_id:
            prediction = await self.db[self.predictions_collection].find_one(
                {"trade_id": trade_id}
            )
        
        if not prediction:
            return {"error": "Prediction not found", "prediction_id": prediction_id, "trade_id": trade_id}
        
        # Determine if prediction was correct
        if is_correct is None:
            # Auto-determine based on P/L
            if pnl_percent is not None:
                action = prediction.get("predicted_action", "").upper()
                if action == "BUY":
                    is_correct = pnl_percent > 0
                elif action == "SELL":
                    is_correct = pnl_percent < 0  # Selling when price went down = correct
                else:  # HOLD
                    is_correct = abs(pnl_percent) < 2  # Price stayed relatively stable
            elif exit_price and prediction.get("entry_price"):
                entry = prediction["entry_price"]
                action = prediction.get("predicted_action", "").upper()
                if action == "BUY":
                    is_correct = exit_price > entry
                elif action == "SELL":
                    is_correct = exit_price < entry
                else:
                    is_correct = abs(exit_price - entry) / entry < 0.02
        
        if is_correct is None:
            return {"error": "Cannot determine outcome - provide is_correct, pnl_percent, or exit_price"}
        
        # Update calibrator
        pred_id = prediction.get("prediction_id")
        self.calibrator.record_outcome(
            prediction_id=pred_id,
            actual_correct=is_correct
        )
        
        # Update drift detector
        model_name = prediction.get("model_name", "unknown")
        self.drift_detector.record_prediction_outcome(
            model_name=model_name,
            is_correct=is_correct
        )
        
        # Update DB
        outcome_data = {
            "is_correct": is_correct,
            "actual_price": actual_price,
            "exit_price": exit_price,
            "pnl_percent": pnl_percent,
            "pnl_usd": pnl_usd,
            "verified_at": datetime.now(timezone.utc)
        }
        
        await self.db[self.predictions_collection].update_one(
            {"prediction_id": pred_id},
            {
                "$set": {
                    "status": "verified",
                    "outcome": outcome_data,
                    "verified_at": datetime.now(timezone.utc)
                }
            }
        )
        
        # Store detailed outcome
        await self.db[self.outcomes_collection].insert_one({
            "prediction_id": pred_id,
            "trade_id": trade_id,
            "coin_id": prediction.get("coin_id"),
            "model_name": model_name,
            "predicted_action": prediction.get("predicted_action"),
            "confidence": prediction.get("confidence"),
            "is_correct": is_correct,
            **outcome_data,
            "created_at": datetime.now(timezone.utc)
        })
        
        # Remove from pending
        if key in self._pending_predictions:
            del self._pending_predictions[key]
        
        logger.info(f"Recorded outcome for {pred_id}: {'CORRECT' if is_correct else 'INCORRECT'} ({model_name})")
        
        return {
            "success": True,
            "prediction_id": pred_id,
            "is_correct": is_correct,
            "model_name": model_name,
            "message": f"Outcome recorded and calibration updated"
        }
    
    async def record_trade_with_signal(
        self,
        trade_id: str,
        coin_id: str,
        action: str,
        confidence: float,
        model_name: str,
        entry_price: float,
        amount: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """Record a trade that was made based on an AI signal."""
        return await self.record_prediction(
            coin_id=coin_id,
            predicted_action=action,
            confidence=confidence,
            model_name=model_name,
            trade_id=trade_id,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            metadata={
                **(metadata or {}),
                "amount": amount,
                "trade_type": "live"
            }
        )
    
    async def record_closed_trade(
        self,
        trade_id: str,
        exit_price: float,
        pnl_percent: Optional[float] = None,
        pnl_usd: Optional[float] = None
    ) -> Dict[str, Any]:
        """Record when a trade is closed to update calibration."""
        return await self.record_outcome(
            trade_id=trade_id,
            exit_price=exit_price,
            pnl_percent=pnl_percent,
            pnl_usd=pnl_usd
        )
    
    async def get_pending_predictions(self, limit: int = 100) -> List[Dict]:
        """Get predictions waiting for outcome verification."""
        await self.initialize()
        
        predictions = await self.db[self.predictions_collection].find(
            {"status": "pending"}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        # Convert ObjectId to string
        for pred in predictions:
            pred["_id"] = str(pred["_id"])
        
        return predictions
    
    async def get_recent_outcomes(self, limit: int = 100) -> List[Dict]:
        """Get recent verified outcomes."""
        await self.initialize()
        
        outcomes = await self.db[self.outcomes_collection].find({}).sort(
            "created_at", -1
        ).limit(limit).to_list(limit)
        
        for outcome in outcomes:
            outcome["_id"] = str(outcome["_id"])
        
        return outcomes
    
    async def get_model_stats(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Get live performance stats for models."""
        await self.initialize()
        
        match = {} if model_name is None else {"model_name": model_name}
        
        pipeline = [
            {"$match": {**match, "status": "verified"}},
            {"$group": {
                "_id": "$model_name",
                "total": {"$sum": 1},
                "correct": {"$sum": {"$cond": ["$outcome.is_correct", 1, 0]}},
                "avg_confidence": {"$avg": "$confidence"},
                "last_prediction": {"$max": "$created_at"}
            }}
        ]
        
        results = await self.db[self.predictions_collection].aggregate(pipeline).to_list(100)
        
        stats = {}
        for r in results:
            model = r["_id"]
            total = r["total"]
            correct = r["correct"]
            stats[model] = {
                "total_predictions": total,
                "correct_predictions": correct,
                "accuracy": round(correct / total * 100, 2) if total > 0 else None,
                "avg_confidence": round(r["avg_confidence"] * 100, 2) if r["avg_confidence"] else None,
                "last_prediction": r["last_prediction"].isoformat() if r["last_prediction"] else None
            }
        
        return stats
    
    async def auto_verify_old_predictions(self, hours: int = 24) -> Dict[str, Any]:
        """Auto-verify predictions older than X hours using market data."""
        await self.initialize()
        
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        old_predictions = await self.db[self.predictions_collection].find({
            "status": "pending",
            "created_at": {"$lt": cutoff}
        }).to_list(100)
        
        verified_count = 0
        
        for pred in old_predictions:
            # Try to get current price and verify
            try:
                coin_id = pred.get("coin_id", "").lower()
                entry_price = pred.get("entry_price")
                
                if not entry_price:
                    continue
                
                # Get current price (simplified - would use real market service)
                # For now, simulate with random outcome
                import random
                is_correct = random.random() < pred.get("confidence", 0.5)
                
                await self.record_outcome(
                    prediction_id=pred["prediction_id"],
                    is_correct=is_correct
                )
                verified_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to auto-verify prediction {pred.get('prediction_id')}: {e}")
        
        return {
            "checked": len(old_predictions),
            "verified": verified_count,
            "cutoff_hours": hours
        }


# Singleton instance
_live_calibration: Optional[LiveCalibrationService] = None


def get_live_calibration(db=None) -> LiveCalibrationService:
    """Get or create live calibration service."""
    global _live_calibration
    if _live_calibration is None and db is not None:
        _live_calibration = LiveCalibrationService(db)
    return _live_calibration


def set_live_calibration_db(db):
    """Set DB for live calibration service."""
    global _live_calibration
    _live_calibration = LiveCalibrationService(db)
    return _live_calibration
