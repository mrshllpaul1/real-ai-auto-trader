"""
System State Persistence Service
=================================
Persists running states of various system components to MongoDB.
Ensures states survive page navigation and service restarts.

Components tracked:
- Auto Trading
- Adaptive Monitoring
- Master Orchestrator
- Tethys Trading Loop
- Universe Rebuilding
- Training processes
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
    Centralized state persistence for all running components.
    Uses MongoDB to store state that survives restarts.
    """
    
    COLLECTION_NAME = "system_running_states"
    
    def __init__(self, db):
        self.db = db
        self._cache: Dict[str, Dict] = {}  # In-memory cache for fast reads
        logger.info("✅ System State Persistence initialized")
    
    async def get_state(self, component: str, user_id: str = "default") -> Optional[Dict]:
        """
        Get the current state of a component.
        
        Args:
            component: Component type (e.g., 'auto_trading')
            user_id: User identifier
            
        Returns:
            State dict or None if not found
        """
        cache_key = f"{component}:{user_id}"
        
        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Query database
        try:
            state = await self.db[self.COLLECTION_NAME].find_one(
                {"component": component, "user_id": user_id},
                {"_id": 0}
            )
            
            if state:
                self._cache[cache_key] = state
            
            return state
        except Exception as e:
            logger.error(f"Error getting state for {component}: {e}")
            return None
    
    async def set_state(
        self, 
        component: str, 
        is_running: bool, 
        user_id: str = "default",
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Set the running state of a component.
        
        Args:
            component: Component type
            is_running: Whether the component is currently running
            user_id: User identifier
            metadata: Additional metadata to store
            
        Returns:
            Success status
        """
        try:
            state = {
                "component": component,
                "user_id": user_id,
                "is_running": is_running,
                "updated_at": datetime.now(timezone.utc),
                "metadata": metadata or {}
            }
            
            if is_running:
                state["started_at"] = datetime.now(timezone.utc)
            
            await self.db[self.COLLECTION_NAME].update_one(
                {"component": component, "user_id": user_id},
                {"$set": state},
                upsert=True
            )
            
            # Update cache
            cache_key = f"{component}:{user_id}"
            self._cache[cache_key] = state
            
            logger.info(f"{'🟢' if is_running else '🔴'} {component} state updated: running={is_running}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting state for {component}: {e}")
            return False
    
    async def is_running(self, component: str, user_id: str = "default") -> bool:
        """Check if a component is currently running"""
        state = await self.get_state(component, user_id)
        return state.get("is_running", False) if state else False
    
    async def get_all_states(self, user_id: str = "default") -> Dict[str, Dict]:
        """Get states of all components for a user"""
        try:
            cursor = self.db[self.COLLECTION_NAME].find(
                {"user_id": user_id},
                {"_id": 0}
            )
            
            states = {}
            async for state in cursor:
                states[state["component"]] = state
            
            return states
            
        except Exception as e:
            logger.error(f"Error getting all states: {e}")
            return {}
    
    async def stop_all(self, user_id: str = "default", except_components: List[str] = None) -> int:
        """
        Stop all running components for a user.
        
        Args:
            user_id: User identifier
            except_components: List of components to NOT stop
            
        Returns:
            Number of components stopped
        """
        except_components = except_components or []
        
        try:
            query = {
                "user_id": user_id,
                "is_running": True,
                "component": {"$nin": except_components}
            }
            
            result = await self.db[self.COLLECTION_NAME].update_many(
                query,
                {
                    "$set": {
                        "is_running": False,
                        "stopped_at": datetime.now(timezone.utc),
                        "stopped_reason": "stop_all_called"
                    }
                }
            )
            
            # Clear cache for affected components
            for key in list(self._cache.keys()):
                if user_id in key:
                    component = key.split(":")[0]
                    if component not in except_components:
                        del self._cache[key]
            
            logger.warning(f"⚠️ Stopped {result.modified_count} components for user {user_id}")
            return result.modified_count
            
        except Exception as e:
            logger.error(f"Error stopping all components: {e}")
            return 0
    
    async def clear_cache(self):
        """Clear the in-memory cache"""
        self._cache.clear()
    
    async def get_running_summary(self, user_id: str = "default") -> Dict[str, Any]:
        """Get a summary of all running states"""
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
    """Get or create the state persistence service"""
    global _state_persistence
    
    if _state_persistence is None and db is not None:
        _state_persistence = SystemStatePersistence(db)
    
    return _state_persistence


async def initialize_state_persistence(db) -> SystemStatePersistence:
    """Initialize the state persistence service"""
    global _state_persistence
    _state_persistence = SystemStatePersistence(db)
    
    # Create index for fast lookups
    await db[SystemStatePersistence.COLLECTION_NAME].create_index(
        [("component", 1), ("user_id", 1)],
        unique=True
    )
    
    return _state_persistence
