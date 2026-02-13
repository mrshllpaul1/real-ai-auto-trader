"""
Lightweight System State Persistence Service
=============================================
Fast, non-blocking state persistence for UI components.
Uses in-memory cache with async DB persistence.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class ComponentType(str, Enum):
    """Types of system components that can be tracked"""
    AUTO_TRADING = "auto_trading"
    ADAPTIVE_MONITORING = "adaptive_monitoring"
    MASTER_ORCHESTRATOR = "master_orchestrator"
    TETHYS_TRADING = "tethys_trading"
    TETHYS_AUTOPILOT = "tethys_autopilot"
    UNIVERSE_REBUILD = "universe_rebuild"
    MODEL_TRAINING = "model_training"
    REAL_TRADING = "real_trading"


class SystemStatePersistence:
    """
    Lightweight state persistence with memory-first approach.
    DB operations are non-blocking fire-and-forget.
    """
    
    COLLECTION_NAME = "system_running_states"
    
    def __init__(self, db):
        self.db = db
        # In-memory cache for fast reads
        self._cache: Dict[str, Dict] = {}
        logger.info("✅ System State Persistence initialized")
    
    async def get_state(self, component: str, user_id: str = "default") -> Optional[Dict]:
        """Get state from memory cache (fast)"""
        cache_key = f"{component}:{user_id}"
        
        # Return from cache if available
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Try DB (non-blocking with timeout)
        try:
            state = await self.db[self.COLLECTION_NAME].find_one(
                {"component": component, "user_id": user_id},
                {"_id": 0}
            )
            if state:
                self._cache[cache_key] = state
            return state
        except Exception as e:
            logger.debug(f"DB read error (using cache): {e}")
            return None
    
    async def set_state(
        self, 
        component: str, 
        is_running: bool, 
        user_id: str = "default",
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Set state - updates cache immediately, DB in background"""
        cache_key = f"{component}:{user_id}"
        
        state = {
            "component": component,
            "user_id": user_id,
            "is_running": is_running,
            "updated_at": datetime.now(timezone.utc),
            "metadata": metadata or {}
        }
        
        if is_running:
            state["started_at"] = datetime.now(timezone.utc)
        
        # Update cache immediately
        self._cache[cache_key] = state
        
        # Fire-and-forget DB update
        try:
            await self.db[self.COLLECTION_NAME].update_one(
                {"component": component, "user_id": user_id},
                {"$set": state},
                upsert=True
            )
        except Exception as e:
            logger.debug(f"DB write error (cache updated): {e}")
        
        logger.info(f"{'🟢' if is_running else '🔴'} {component}: running={is_running}")
        return True
    
    async def is_running(self, component: str, user_id: str = "default") -> bool:
        """Quick check if component is running"""
        cache_key = f"{component}:{user_id}"
        if cache_key in self._cache:
            return self._cache[cache_key].get("is_running", False)
        
        state = await self.get_state(component, user_id)
        return state.get("is_running", False) if state else False
    
    async def get_all_states(self, user_id: str = "default") -> Dict[str, Dict]:
        """Get all states for user from cache"""
        states = {}
        for key, value in self._cache.items():
            if key.endswith(f":{user_id}"):
                component = key.split(":")[0]
                states[component] = value
        return states
    
    async def stop_all(self, user_id: str = "default", except_components: List[str] = None) -> int:
        """Stop all components"""
        except_components = except_components or []
        count = 0
        
        for key in list(self._cache.keys()):
            if key.endswith(f":{user_id}"):
                component = key.split(":")[0]
                if component not in except_components:
                    await self.set_state(component, False, user_id)
                    count += 1
        
        return count
    
    async def get_running_summary(self, user_id: str = "default") -> Dict[str, Any]:
        """Get summary of running states"""
        states = await self.get_all_states(user_id)
        
        running = [k for k, v in states.items() if v.get("is_running")]
        stopped = [k for k, v in states.items() if not v.get("is_running")]
        
        return {
            "running_components": running,
            "stopped_components": stopped,
            "total_running": len(running),
            "total_stopped": len(stopped),
            "states": {
                k: {
                    "is_running": v.get("is_running", False),
                    "started_at": v.get("started_at").isoformat() if v.get("started_at") else None,
                    "metadata": v.get("metadata", {})
                }
                for k, v in states.items()
            }
        }


# Singleton instance
_state_persistence: Optional[SystemStatePersistence] = None


def get_state_persistence(db=None) -> Optional[SystemStatePersistence]:
    """Get or create state persistence service"""
    global _state_persistence
    if _state_persistence is None and db is not None:
        _state_persistence = SystemStatePersistence(db)
    return _state_persistence


async def initialize_state_persistence(db) -> SystemStatePersistence:
    """Initialize state persistence service"""
    global _state_persistence
    _state_persistence = SystemStatePersistence(db)
    
    # Create index (fire and forget)
    try:
        await db[SystemStatePersistence.COLLECTION_NAME].create_index(
            [("component", 1), ("user_id", 1)],
            unique=True,
            background=True
        )
    except Exception as e:
        logger.debug(f"Index creation (may already exist): {e}")
    
    return _state_persistence
