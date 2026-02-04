"""
Model Persistence Service
Handles saving and loading trained models to/from disk
"""

import os
import json
import logging
import pickle
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Models directory
MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)


class ModelPersistence:
    """
    Service to persist trained models to disk.
    Supports TensorFlow/Keras models and scikit-learn models.
    """
    
    def __init__(self, model_type: str):
        """
        Initialize model persistence for a specific model type.
        
        Args:
            model_type: Type of model (e.g., 'rl_agent', 'transformer', 'regime')
        """
        self.model_type = model_type
        self.model_dir = MODELS_DIR / model_type
        self.model_dir.mkdir(exist_ok=True)
        self.metadata_file = self.model_dir / "metadata.json"
    
    def save_keras_model(self, model, metadata: Dict[str, Any] = None) -> bool:
        """
        Save a Keras/TensorFlow model to disk.
        
        Args:
            model: Keras model to save
            metadata: Optional metadata (training info, metrics, etc.)
            
        Returns:
            True if successful
        """
        try:
            model_path = self.model_dir / "model.keras"
            model.save(str(model_path))
            
            # Save metadata
            meta = {
                "model_type": self.model_type,
                "saved_at": datetime.now(timezone.utc).isoformat(),
                "format": "keras",
                **(metadata or {})
            }
            
            with open(self.metadata_file, 'w') as f:
                json.dump(meta, f, indent=2, default=str)
            
            logger.info(f"✅ Saved {self.model_type} model to {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save {self.model_type} model: {e}")
            return False
    
    def load_keras_model(self):
        """
        Load a Keras/TensorFlow model from disk.
        
        Returns:
            Loaded model or None if not found
        """
        try:
            model_path = self.model_dir / "model.keras"
            
            if not model_path.exists():
                logger.info(f"No saved {self.model_type} model found")
                return None
            
            import tensorflow as tf
            model = tf.keras.models.load_model(str(model_path))
            
            logger.info(f"✅ Loaded {self.model_type} model from {model_path}")
            return model
            
        except Exception as e:
            logger.error(f"❌ Failed to load {self.model_type} model: {e}")
            return None
    
    def save_sklearn_model(self, model, metadata: Dict[str, Any] = None) -> bool:
        """
        Save a scikit-learn model to disk using pickle.
        
        Args:
            model: Scikit-learn model to save
            metadata: Optional metadata
            
        Returns:
            True if successful
        """
        try:
            model_path = self.model_dir / "model.pkl"
            
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            
            # Save metadata
            meta = {
                "model_type": self.model_type,
                "saved_at": datetime.now(timezone.utc).isoformat(),
                "format": "pickle",
                **(metadata or {})
            }
            
            with open(self.metadata_file, 'w') as f:
                json.dump(meta, f, indent=2, default=str)
            
            logger.info(f"✅ Saved {self.model_type} model to {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save {self.model_type} model: {e}")
            return False
    
    def load_sklearn_model(self):
        """
        Load a scikit-learn model from disk.
        
        Returns:
            Loaded model or None if not found
        """
        try:
            model_path = self.model_dir / "model.pkl"
            
            if not model_path.exists():
                logger.info(f"No saved {self.model_type} model found")
                return None
            
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            
            logger.info(f"✅ Loaded {self.model_type} model from {model_path}")
            return model
            
        except Exception as e:
            logger.error(f"❌ Failed to load {self.model_type} model: {e}")
            return None
    
    def save_weights(self, weights: Dict[str, Any], metadata: Dict[str, Any] = None) -> bool:
        """
        Save model weights/state as JSON (for simple models).
        
        Args:
            weights: Dictionary of weights/state
            metadata: Optional metadata
            
        Returns:
            True if successful
        """
        try:
            weights_path = self.model_dir / "weights.json"
            
            # Convert numpy arrays to lists for JSON serialization
            serializable_weights = {}
            for key, value in weights.items():
                if hasattr(value, 'tolist'):
                    serializable_weights[key] = value.tolist()
                else:
                    serializable_weights[key] = value
            
            with open(weights_path, 'w') as f:
                json.dump(serializable_weights, f)
            
            # Save metadata
            meta = {
                "model_type": self.model_type,
                "saved_at": datetime.now(timezone.utc).isoformat(),
                "format": "json_weights",
                **(metadata or {})
            }
            
            with open(self.metadata_file, 'w') as f:
                json.dump(meta, f, indent=2, default=str)
            
            logger.info(f"✅ Saved {self.model_type} weights to {weights_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save {self.model_type} weights: {e}")
            return False
    
    def load_weights(self) -> Optional[Dict[str, Any]]:
        """
        Load model weights/state from JSON.
        
        Returns:
            Dictionary of weights or None if not found
        """
        try:
            weights_path = self.model_dir / "weights.json"
            
            if not weights_path.exists():
                logger.info(f"No saved {self.model_type} weights found")
                return None
            
            with open(weights_path, 'r') as f:
                weights = json.load(f)
            
            logger.info(f"✅ Loaded {self.model_type} weights from {weights_path}")
            return weights
            
        except Exception as e:
            logger.error(f"❌ Failed to load {self.model_type} weights: {e}")
            return None
    
    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """Get saved model metadata"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            return None
        except Exception:
            return None
    
    def model_exists(self) -> bool:
        """Check if a saved model exists"""
        return (
            (self.model_dir / "model.keras").exists() or
            (self.model_dir / "model.pkl").exists() or
            (self.model_dir / "weights.json").exists()
        )
    
    def delete_model(self) -> bool:
        """Delete saved model files"""
        try:
            import shutil
            if self.model_dir.exists():
                shutil.rmtree(self.model_dir)
                self.model_dir.mkdir(exist_ok=True)
            logger.info(f"🗑️ Deleted {self.model_type} model")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {self.model_type} model: {e}")
            return False


# Convenience functions for common model types
def get_rl_persistence() -> ModelPersistence:
    return ModelPersistence("rl_agent")

def get_transformer_persistence() -> ModelPersistence:
    return ModelPersistence("transformer")

def get_regime_persistence() -> ModelPersistence:
    return ModelPersistence("regime")

def get_gem_ml_persistence() -> ModelPersistence:
    return ModelPersistence("gem_ml")
