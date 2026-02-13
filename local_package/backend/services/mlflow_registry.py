"""
MLflow Model Registry Integration
==================================
Production-grade model versioning, staging, and deployment
using MLflow tracking server.
"""

import os
import mlflow
from mlflow.tracking import MlflowClient
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import json
import numpy as np

logger = logging.getLogger(__name__)

# MLflow configuration
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
EXPERIMENT_NAME = "tethys-trading"


class MLflowModelRegistry:
    """
    Production model registry using MLflow.
    Handles model versioning, staging, and deployment.
    """
    
    def __init__(self, db=None):
        self.db = db
        self.client = None
        self.experiment_id = None
        
        self._initialize_mlflow()
        logger.info("📊 MLflow Model Registry initialized")
    
    def _initialize_mlflow(self):
        """Initialize MLflow tracking"""
        try:
            mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
            
            # Create or get experiment
            experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
            if experiment is None:
                self.experiment_id = mlflow.create_experiment(EXPERIMENT_NAME)
            else:
                self.experiment_id = experiment.experiment_id
            
            mlflow.set_experiment(EXPERIMENT_NAME)
            self.client = MlflowClient()
            
            logger.info(f"✅ MLflow initialized with experiment: {EXPERIMENT_NAME}")
        except Exception as e:
            logger.error(f"MLflow initialization error: {e}")
            self.client = None
    
    def log_training_run(
        self,
        model_name: str,
        params: Dict,
        metrics: Dict,
        model_path: Optional[str] = None,
        tags: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Log a training run to MLflow.
        
        Args:
            model_name: Name of the model
            params: Hyperparameters used
            metrics: Training metrics
            model_path: Path to saved model file
            tags: Additional tags
            
        Returns:
            Run ID if successful
        """
        if not self.client:
            logger.warning("MLflow client not initialized")
            return None
        
        try:
            with mlflow.start_run(run_name=f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}") as run:
                # Log parameters
                for key, value in params.items():
                    if isinstance(value, (int, float, str, bool)):
                        mlflow.log_param(key, value)
                    else:
                        mlflow.log_param(key, str(value))
                
                # Log metrics
                for key, value in metrics.items():
                    if isinstance(value, (int, float)):
                        mlflow.log_metric(key, value)
                    elif isinstance(value, list) and value:
                        # Log as series
                        for i, v in enumerate(value[-100:]):  # Last 100 values
                            if isinstance(v, (int, float)):
                                mlflow.log_metric(key, v, step=i)
                
                # Log tags
                mlflow.set_tag("model_name", model_name)
                mlflow.set_tag("timestamp", datetime.now(timezone.utc).isoformat())
                
                if tags:
                    for key, value in tags.items():
                        mlflow.set_tag(key, str(value))
                
                # Log model artifact if path provided
                if model_path and os.path.exists(model_path):
                    mlflow.log_artifact(model_path)
                
                run_id = run.info.run_id
                logger.info(f"✅ Logged training run: {run_id}")
                
                return run_id
                
        except Exception as e:
            logger.error(f"Error logging training run: {e}")
            return None
    
    def register_model(
        self,
        run_id: str,
        model_name: str,
        model_path: str = "model"
    ) -> Optional[str]:
        """
        Register a model from a run to the model registry.
        
        Args:
            run_id: MLflow run ID
            model_name: Name for the registered model
            model_path: Artifact path within the run
            
        Returns:
            Model version if successful
        """
        if not self.client:
            return None
        
        try:
            model_uri = f"runs:/{run_id}/{model_path}"
            
            # Register the model
            result = mlflow.register_model(model_uri, model_name)
            
            logger.info(f"✅ Registered model {model_name} version {result.version}")
            return result.version
            
        except Exception as e:
            logger.error(f"Error registering model: {e}")
            return None
    
    def promote_model(
        self,
        model_name: str,
        version: str,
        stage: str = "Production"
    ) -> bool:
        """
        Promote a model version to a stage (Staging, Production, Archived).
        
        Args:
            model_name: Name of the registered model
            version: Version number to promote
            stage: Target stage (Staging, Production, Archived)
            
        Returns:
            Success status
        """
        if not self.client:
            return False
        
        try:
            # Transition the model version
            self.client.transition_model_version_stage(
                name=model_name,
                version=version,
                stage=stage,
                archive_existing_versions=(stage == "Production")
            )
            
            logger.info(f"✅ Promoted {model_name} v{version} to {stage}")
            return True
            
        except Exception as e:
            logger.error(f"Error promoting model: {e}")
            return False
    
    def get_latest_model(
        self,
        model_name: str,
        stage: str = "Production"
    ) -> Optional[Dict]:
        """
        Get the latest model version for a given stage.
        
        Args:
            model_name: Name of the registered model
            stage: Stage to query (None for all stages)
            
        Returns:
            Model version info if found
        """
        if not self.client:
            return None
        
        try:
            versions = self.client.get_latest_versions(
                name=model_name,
                stages=[stage] if stage else None
            )
            
            if versions:
                latest = versions[0]
                return {
                    "name": latest.name,
                    "version": latest.version,
                    "stage": latest.current_stage,
                    "run_id": latest.run_id,
                    "created_at": latest.creation_timestamp,
                    "description": latest.description
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest model: {e}")
            return None
    
    def get_model_history(self, model_name: str) -> List[Dict]:
        """Get version history for a model"""
        if not self.client:
            return []
        
        try:
            versions = self.client.search_model_versions(f"name='{model_name}'")
            
            return [
                {
                    "version": v.version,
                    "stage": v.current_stage,
                    "run_id": v.run_id,
                    "created_at": v.creation_timestamp,
                    "description": v.description,
                    "status": v.status
                }
                for v in versions
            ]
            
        except Exception as e:
            logger.error(f"Error getting model history: {e}")
            return []
    
    def get_run_metrics(self, run_id: str) -> Dict:
        """Get metrics for a specific run"""
        if not self.client:
            return {}
        
        try:
            run = self.client.get_run(run_id)
            return {
                "params": run.data.params,
                "metrics": run.data.metrics,
                "tags": run.data.tags,
                "start_time": run.info.start_time,
                "end_time": run.info.end_time,
                "status": run.info.status
            }
        except Exception as e:
            logger.error(f"Error getting run metrics: {e}")
            return {}
    
    def compare_models(
        self,
        model_name: str,
        versions: List[str] = None
    ) -> List[Dict]:
        """Compare multiple model versions"""
        if not self.client:
            return []
        
        try:
            all_versions = self.client.search_model_versions(f"name='{model_name}'")
            
            comparisons = []
            for v in all_versions:
                if versions and v.version not in versions:
                    continue
                
                run_metrics = self.get_run_metrics(v.run_id)
                comparisons.append({
                    "version": v.version,
                    "stage": v.current_stage,
                    "metrics": run_metrics.get("metrics", {}),
                    "params": run_metrics.get("params", {})
                })
            
            return comparisons
            
        except Exception as e:
            logger.error(f"Error comparing models: {e}")
            return []
    
    def get_experiment_runs(self, limit: int = 20) -> List[Dict]:
        """Get recent experiment runs"""
        if not self.client:
            return []
        
        try:
            runs = self.client.search_runs(
                experiment_ids=[self.experiment_id],
                max_results=limit,
                order_by=["start_time DESC"]
            )
            
            return [
                {
                    "run_id": r.info.run_id,
                    "run_name": r.data.tags.get("mlflow.runName", ""),
                    "status": r.info.status,
                    "start_time": r.info.start_time,
                    "metrics": r.data.metrics,
                    "params": r.data.params
                }
                for r in runs
            ]
            
        except Exception as e:
            logger.error(f"Error getting experiment runs: {e}")
            return []
    
    def get_status(self) -> Dict:
        """Get MLflow registry status"""
        return {
            "initialized": self.client is not None,
            "tracking_uri": MLFLOW_TRACKING_URI,
            "experiment_name": EXPERIMENT_NAME,
            "experiment_id": self.experiment_id
        }


# Singleton
_mlflow_registry: Optional[MLflowModelRegistry] = None


def get_mlflow_registry(db=None) -> MLflowModelRegistry:
    """Get or create MLflow registry singleton"""
    global _mlflow_registry
    if _mlflow_registry is None:
        _mlflow_registry = MLflowModelRegistry(db)
    return _mlflow_registry
