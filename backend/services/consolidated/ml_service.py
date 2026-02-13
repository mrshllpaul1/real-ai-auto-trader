"""
Consolidated ML Service
=======================
Combines all machine learning training and inference:
- Model training
- Inference pipelines
- Model registry
- Reinforcement learning
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

__all__ = [
    'MLService',
    'get_ml_service'
]


class MLService:
    """
    Unified ML service that consolidates:
    - ml_optimization_service
    - model_persistence
    - model_benchmarking
    - mlflow_registry
    - deep_rl_trading_engine
    - rl_trading_agent
    - sb3_trading_agents
    - rainbow_dqn
    - transformer_predictor
    - gem_ml_dl_predictor
    """
    
    def __init__(self, db=None):
        self.db = db
        self._model_registry = None
        self._rl_agent = None
        self._transformer = None
        self._trainer = None
        self._available_models = []
        self._check_ml_availability()
        logger.info("🤖 ML Service initialized")
    
    def _check_ml_availability(self):
        """Check which ML libraries are available"""
        self._available_models = []
        
        # Check TensorFlow
        try:
            import tensorflow
            self._available_models.append("tensorflow")
        except ImportError:
            pass
        
        # Check PyTorch
        try:
            import torch
            self._available_models.append("pytorch")
        except ImportError:
            pass
        
        # Check Stable Baselines 3
        try:
            import stable_baselines3
            self._available_models.append("sb3")
        except ImportError:
            pass
        
        # Check scikit-learn
        try:
            import sklearn
            self._available_models.append("sklearn")
        except ImportError:
            pass
        
        # Check XGBoost
        try:
            import xgboost
            self._available_models.append("xgboost")
        except ImportError:
            pass
        
        # Check LightGBM
        try:
            import lightgbm
            self._available_models.append("lightgbm")
        except ImportError:
            pass
        
        logger.info(f"Available ML frameworks: {self._available_models}")
    
    # === Model Management ===
    async def get_available_models(self) -> List[str]:
        """Get list of available model types"""
        return self._available_models
    
    async def load_model(self, model_name: str) -> Dict[str, Any]:
        """Load a trained model"""
        if self._model_registry is None:
            try:
                from services.model_persistence import ModelPersistence
                self._model_registry = ModelPersistence(self.db)
            except Exception as e:
                return {"error": f"Could not load model registry: {e}"}
        
        try:
            model = await self._model_registry.load(model_name)
            return {"loaded": True, "model_name": model_name}
        except Exception as e:
            return {"loaded": False, "error": str(e)}
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List all saved models"""
        if self._model_registry is None:
            try:
                from services.model_persistence import ModelPersistence
                self._model_registry = ModelPersistence(self.db)
            except Exception as e:
                return []
        
        try:
            return await self._model_registry.list_models()
        except Exception as e:
            logger.error(f"List models error: {e}")
            return []
    
    # === Training ===
    async def train_model(
        self,
        model_type: str,
        symbol: str,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Train a new model"""
        if model_type not in self._available_models:
            return {
                "error": f"Model type {model_type} not available",
                "available": self._available_models
            }
        
        if self._trainer is None:
            try:
                from services.historical_trainer import HistoricalTrainer
                self._trainer = HistoricalTrainer(self.db)
            except Exception as e:
                return {"error": f"Could not load trainer: {e}"}
        
        try:
            result = await self._trainer.train(model_type, symbol, params)
            return {"trained": True, "result": result}
        except Exception as e:
            return {"trained": False, "error": str(e)}
    
    async def get_training_status(self) -> Dict[str, Any]:
        """Get current training status"""
        if self._trainer and hasattr(self._trainer, 'get_status'):
            return await self._trainer.get_status()
        return {"training": False, "status": "idle"}
    
    # === Inference ===
    async def predict(self, model_name: str, features: Dict[str, Any]) -> Dict[str, Any]:
        """Run inference on a model"""
        if self._model_registry is None:
            return {"error": "Model registry not available"}
        
        try:
            prediction = await self._model_registry.predict(model_name, features)
            return {"prediction": prediction}
        except Exception as e:
            return {"error": str(e)}
    
    # === Reinforcement Learning ===
    async def get_rl_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get action from RL agent"""
        if "sb3" not in self._available_models:
            return {"error": "Stable Baselines 3 not available"}
        
        if self._rl_agent is None:
            try:
                from services.sb3_trading_agents import SB3TradingAgent
                self._rl_agent = SB3TradingAgent(self.db)
            except Exception as e:
                return {"error": f"Could not load RL agent: {e}"}
        
        try:
            action = await self._rl_agent.get_action(state)
            return {"action": action}
        except Exception as e:
            return {"error": str(e)}
    
    async def train_rl_agent(
        self,
        algorithm: str = "PPO",
        timesteps: int = 10000
    ) -> Dict[str, Any]:
        """Train RL agent"""
        if "sb3" not in self._available_models:
            return {"error": "Stable Baselines 3 not available"}
        
        if self._rl_agent is None:
            try:
                from services.sb3_trading_agents import SB3TradingAgent
                self._rl_agent = SB3TradingAgent(self.db)
            except Exception as e:
                return {"error": f"Could not load RL agent: {e}"}
        
        try:
            result = await self._rl_agent.train(algorithm, timesteps)
            return {"trained": True, "result": result}
        except Exception as e:
            return {"trained": False, "error": str(e)}
    
    # === Transformer Models ===
    async def get_transformer_prediction(self, symbol: str, sequence: List[float]) -> Dict[str, Any]:
        """Get prediction from transformer model"""
        if "pytorch" not in self._available_models:
            return {"error": "PyTorch not available for transformer models"}
        
        if self._transformer is None:
            try:
                from services.transformer_predictor import TransformerPredictor
                self._transformer = TransformerPredictor(self.db)
            except Exception as e:
                return {"error": f"Could not load transformer: {e}"}
        
        try:
            prediction = await self._transformer.predict(symbol, sequence)
            return {"prediction": prediction}
        except Exception as e:
            return {"error": str(e)}
    
    # === Benchmarking ===
    async def benchmark_models(self, symbol: str) -> Dict[str, Any]:
        """Benchmark all available models"""
        results = {}
        
        for model_type in self._available_models:
            try:
                # Run simple benchmark
                start = datetime.now()
                # Placeholder for actual benchmark
                elapsed = (datetime.now() - start).total_seconds()
                results[model_type] = {
                    "available": True,
                    "benchmark_time": elapsed
                }
            except Exception as e:
                results[model_type] = {"available": False, "error": str(e)}
        
        return {
            "benchmarks": results,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get ML service status"""
        return {
            "service": "ml",
            "available_frameworks": self._available_models,
            "model_registry": self._model_registry is not None,
            "rl_agent": self._rl_agent is not None,
            "transformer": self._transformer is not None,
            "trainer": self._trainer is not None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Singleton
_ml_service = None

def get_ml_service(db=None) -> MLService:
    """Get or create ML service singleton"""
    global _ml_service
    if _ml_service is None:
        _ml_service = MLService(db)
    return _ml_service
