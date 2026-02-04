"""
Training History Service
Tracks and persists all model training sessions with results
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# Singleton instance
_training_history_service = None


class TrainingHistoryService:
    """
    Service to track and persist model training history.
    Stores training sessions, results, and metrics for analysis.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.training_history
    
    async def ensure_indexes(self):
        """Create indexes for efficient queries"""
        await self.collection.create_index([("model_type", 1), ("started_at", -1)])
        await self.collection.create_index([("status", 1)])
        await self.collection.create_index([("started_at", -1)])
    
    async def start_training(
        self,
        model_type: str,
        config: Dict[str, Any],
        task_id: Optional[str] = None
    ) -> str:
        """
        Record the start of a training session
        
        Args:
            model_type: Type of model (e.g., 'rl_agent', 'transformer', 'regime')
            config: Training configuration (episodes, epochs, etc.)
            task_id: Optional background task ID
            
        Returns:
            Training session ID
        """
        session = {
            "model_type": model_type,
            "config": config,
            "task_id": task_id,
            "status": "running",
            "started_at": datetime.now(timezone.utc),
            "completed_at": None,
            "duration_seconds": None,
            "result": None,
            "metrics": {},
            "error": None
        }
        
        result = await self.collection.insert_one(session)
        session_id = str(result.inserted_id)
        
        logger.info(f"📝 Training session started: {model_type} ({session_id})")
        return session_id
    
    async def complete_training(
        self,
        session_id: str,
        result: Dict[str, Any],
        metrics: Optional[Dict[str, Any]] = None
    ):
        """
        Record successful completion of a training session
        
        Args:
            session_id: Training session ID
            result: Training results
            metrics: Optional training metrics
        """
        from bson import ObjectId
        
        completed_at = datetime.now(timezone.utc)
        
        # Calculate duration
        session = await self.collection.find_one({"_id": ObjectId(session_id)})
        duration = None
        if session and session.get("started_at"):
            duration = (completed_at - session["started_at"]).total_seconds()
        
        await self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "status": "completed",
                    "completed_at": completed_at,
                    "duration_seconds": duration,
                    "result": result,
                    "metrics": metrics or {}
                }
            }
        )
        
        logger.info(f"✅ Training session completed: {session_id} ({duration:.1f}s)")
    
    async def fail_training(self, session_id: str, error: str):
        """
        Record failed training session
        
        Args:
            session_id: Training session ID
            error: Error message
        """
        from bson import ObjectId
        
        completed_at = datetime.now(timezone.utc)
        
        session = await self.collection.find_one({"_id": ObjectId(session_id)})
        duration = None
        if session and session.get("started_at"):
            duration = (completed_at - session["started_at"]).total_seconds()
        
        await self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "status": "failed",
                    "completed_at": completed_at,
                    "duration_seconds": duration,
                    "error": error
                }
            }
        )
        
        logger.warning(f"❌ Training session failed: {session_id} - {error}")
    
    async def get_history(
        self,
        model_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get training history
        
        Args:
            model_type: Filter by model type
            status: Filter by status (running, completed, failed)
            limit: Maximum number of records
            
        Returns:
            List of training sessions
        """
        query = {}
        if model_type:
            query["model_type"] = model_type
        if status:
            query["status"] = status
        
        cursor = self.collection.find(
            query,
            {"_id": 0}
        ).sort("started_at", -1).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def get_model_stats(self, model_type: str) -> Dict[str, Any]:
        """
        Get statistics for a specific model type
        
        Args:
            model_type: Type of model
            
        Returns:
            Statistics dictionary
        """
        pipeline = [
            {"$match": {"model_type": model_type}},
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "avg_duration": {"$avg": "$duration_seconds"}
                }
            }
        ]
        
        results = await self.collection.aggregate(pipeline).to_list(length=10)
        
        stats = {
            "model_type": model_type,
            "total_sessions": 0,
            "completed": 0,
            "failed": 0,
            "running": 0,
            "avg_duration_seconds": 0
        }
        
        total_duration = 0
        completed_count = 0
        
        for r in results:
            status = r["_id"]
            count = r["count"]
            stats["total_sessions"] += count
            
            if status == "completed":
                stats["completed"] = count
                if r["avg_duration"]:
                    total_duration += r["avg_duration"] * count
                    completed_count += count
            elif status == "failed":
                stats["failed"] = count
            elif status == "running":
                stats["running"] = count
        
        if completed_count > 0:
            stats["avg_duration_seconds"] = round(total_duration / completed_count, 1)
        
        # Get best result
        best = await self.collection.find_one(
            {
                "model_type": model_type,
                "status": "completed",
                "result": {"$exists": True}
            },
            sort=[("result.val_accuracy", -1), ("result.avg_return_last_20_pct", -1)]
        )
        
        if best:
            stats["best_result"] = best.get("result")
            stats["best_session_date"] = best.get("completed_at")
        
        return stats
    
    async def get_all_stats(self) -> Dict[str, Any]:
        """Get overall training statistics"""
        pipeline = [
            {
                "$group": {
                    "_id": "$model_type",
                    "total": {"$sum": 1},
                    "completed": {
                        "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                    },
                    "avg_duration": {
                        "$avg": {
                            "$cond": [
                                {"$eq": ["$status", "completed"]},
                                "$duration_seconds",
                                None
                            ]
                        }
                    }
                }
            }
        ]
        
        results = await self.collection.aggregate(pipeline).to_list(length=20)
        
        return {
            "by_model": {r["_id"]: {
                "total": r["total"],
                "completed": r["completed"],
                "success_rate": round(r["completed"] / r["total"] * 100, 1) if r["total"] > 0 else 0,
                "avg_duration_seconds": round(r["avg_duration"], 1) if r["avg_duration"] else 0
            } for r in results},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


def get_training_history_service(db: AsyncIOMotorDatabase) -> TrainingHistoryService:
    """Get or create the training history service singleton"""
    global _training_history_service
    if _training_history_service is None:
        _training_history_service = TrainingHistoryService(db)
    return _training_history_service
