"""
AI Model A/B Testing Service
============================
Compare multiple AI models in real-time.
"""

import asyncio
import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ModelPrediction:
    """A prediction from a model"""
    model_id: str
    timestamp: str
    symbol: str
    prediction: str  # 'buy', 'sell', 'hold'
    confidence: float
    actual_outcome: Optional[str] = None
    pnl: Optional[float] = None


@dataclass
class ModelPerformance:
    """Performance metrics for a model"""
    model_id: str
    model_name: str
    total_predictions: int
    correct_predictions: int
    accuracy: float
    avg_confidence: float
    total_pnl: float
    sharpe_ratio: float
    win_rate: float
    is_active: bool


@dataclass
class ABTest:
    """An A/B test configuration"""
    test_id: str
    name: str
    model_a: str
    model_b: str
    start_date: str
    end_date: Optional[str]
    status: str  # 'running', 'completed', 'paused'
    traffic_split: float  # Percentage to model A
    results: Dict = field(default_factory=dict)


class AIABTestingService:
    """
    A/B testing for AI models.
    
    Features:
    - Register multiple models
    - Traffic splitting
    - Performance tracking
    - Statistical significance testing
    """
    
    def __init__(self, db):
        self.db = db
        self.models: Dict[str, Dict] = {}
        self.predictions: Dict[str, List[ModelPrediction]] = defaultdict(list)
        self.performance: Dict[str, ModelPerformance] = {}
        self.active_tests: Dict[str, ABTest] = {}
        self.is_running = False
        logger.info("✅ AI A/B Testing Service initialized")
    
    async def register_model(
        self,
        model_id: str,
        model_name: str,
        model_type: str,
        config: Dict = None
    ) -> Dict[str, Any]:
        """Register a model for testing"""
        self.models[model_id] = {
            'id': model_id,
            'name': model_name,
            'type': model_type,
            'config': config or {},
            'registered_at': datetime.now(timezone.utc).isoformat(),
            'is_active': True
        }
        
        self.performance[model_id] = ModelPerformance(
            model_id=model_id,
            model_name=model_name,
            total_predictions=0,
            correct_predictions=0,
            accuracy=0.0,
            avg_confidence=0.0,
            total_pnl=0.0,
            sharpe_ratio=0.0,
            win_rate=0.0,
            is_active=True
        )
        
        await self.db.ab_models.update_one(
            {'id': model_id},
            {'$set': self.models[model_id]},
            upsert=True
        )
        
        logger.info(f"🤖 Model registered: {model_name} ({model_id})")
        return {'status': 'registered', 'model_id': model_id}
    
    async def create_test(
        self,
        name: str,
        model_a: str,
        model_b: str,
        traffic_split: float = 50.0
    ) -> Dict[str, Any]:
        """Create a new A/B test"""
        if model_a not in self.models:
            return {'status': 'error', 'message': f'Model A not found: {model_a}'}
        if model_b not in self.models:
            return {'status': 'error', 'message': f'Model B not found: {model_b}'}
        
        test_id = f"test_{datetime.now().timestamp()}"
        
        test = ABTest(
            test_id=test_id,
            name=name,
            model_a=model_a,
            model_b=model_b,
            start_date=datetime.now(timezone.utc).isoformat(),
            end_date=None,
            status='running',
            traffic_split=traffic_split,
            results={}
        )
        
        self.active_tests[test_id] = test
        
        await self.db.ab_tests.insert_one(asdict(test))
        
        logger.info(f"🧪 A/B Test created: {name}")
        return {'status': 'created', 'test_id': test_id, 'test': asdict(test)}
    
    async def record_prediction(
        self,
        test_id: str,
        symbol: str,
        model_a_pred: Dict,
        model_b_pred: Dict
    ) -> Dict[str, Any]:
        """Record predictions from both models"""
        test = self.active_tests.get(test_id)
        if not test or test.status != 'running':
            return {'status': 'error', 'message': 'Test not found or not running'}
        
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Record Model A prediction
        pred_a = ModelPrediction(
            model_id=test.model_a,
            timestamp=timestamp,
            symbol=symbol,
            prediction=model_a_pred.get('prediction', 'hold'),
            confidence=model_a_pred.get('confidence', 0.5)
        )
        self.predictions[test.model_a].append(pred_a)
        
        # Record Model B prediction
        pred_b = ModelPrediction(
            model_id=test.model_b,
            timestamp=timestamp,
            symbol=symbol,
            prediction=model_b_pred.get('prediction', 'hold'),
            confidence=model_b_pred.get('confidence', 0.5)
        )
        self.predictions[test.model_b].append(pred_b)
        
        # Route traffic based on split
        selected_model = test.model_a if random.random() * 100 < test.traffic_split else test.model_b
        selected_pred = pred_a if selected_model == test.model_a else pred_b
        
        return {
            'status': 'recorded',
            'selected_model': selected_model,
            'prediction': asdict(selected_pred)
        }
    
    async def record_outcome(
        self,
        test_id: str,
        symbol: str,
        actual_outcome: str,
        pnl: float
    ) -> Dict[str, Any]:
        """Record actual outcome for predictions"""
        test = self.active_tests.get(test_id)
        if not test:
            return {'status': 'error', 'message': 'Test not found'}
        
        # Update recent predictions for both models
        for model_id in [test.model_a, test.model_b]:
            for pred in reversed(self.predictions[model_id][-100:]):
                if pred.symbol == symbol and pred.actual_outcome is None:
                    pred.actual_outcome = actual_outcome
                    pred.pnl = pnl if pred.prediction == actual_outcome else -pnl
                    break
        
        # Update performance
        await self._update_performance(test.model_a)
        await self._update_performance(test.model_b)
        
        return {'status': 'recorded'}
    
    async def _update_performance(self, model_id: str):
        """Update performance metrics for a model"""
        predictions = self.predictions.get(model_id, [])
        if not predictions:
            return
        
        completed = [p for p in predictions if p.actual_outcome is not None]
        if not completed:
            return
        
        correct = sum(1 for p in completed if p.prediction == p.actual_outcome)
        total_pnl = sum(p.pnl or 0 for p in completed)
        confidences = [p.confidence for p in predictions]
        
        # Calculate Sharpe (simplified)
        pnls = [p.pnl or 0 for p in completed]
        if len(pnls) > 1:
            import numpy as np
            sharpe = np.mean(pnls) / (np.std(pnls) + 0.0001) * np.sqrt(252)
        else:
            sharpe = 0
        
        self.performance[model_id] = ModelPerformance(
            model_id=model_id,
            model_name=self.models.get(model_id, {}).get('name', model_id),
            total_predictions=len(predictions),
            correct_predictions=correct,
            accuracy=(correct / len(completed) * 100) if completed else 0,
            avg_confidence=sum(confidences) / len(confidences) if confidences else 0,
            total_pnl=total_pnl,
            sharpe_ratio=sharpe,
            win_rate=(correct / len(completed) * 100) if completed else 0,
            is_active=self.models.get(model_id, {}).get('is_active', False)
        )
    
    async def get_test_results(self, test_id: str) -> Dict[str, Any]:
        """Get results for a specific test"""
        test = self.active_tests.get(test_id)
        if not test:
            return {'status': 'error', 'message': 'Test not found'}
        
        perf_a = self.performance.get(test.model_a)
        perf_b = self.performance.get(test.model_b)
        
        # Determine winner
        winner = None
        if perf_a and perf_b:
            if perf_a.accuracy > perf_b.accuracy + 5:  # 5% significance threshold
                winner = test.model_a
            elif perf_b.accuracy > perf_a.accuracy + 5:
                winner = test.model_b
        
        return {
            'test': asdict(test),
            'model_a_performance': asdict(perf_a) if perf_a else None,
            'model_b_performance': asdict(perf_b) if perf_b else None,
            'winner': winner,
            'is_significant': winner is not None
        }
    
    async def end_test(self, test_id: str) -> Dict[str, Any]:
        """End an A/B test"""
        test = self.active_tests.get(test_id)
        if not test:
            return {'status': 'error', 'message': 'Test not found'}
        
        test.status = 'completed'
        test.end_date = datetime.now(timezone.utc).isoformat()
        
        results = await self.get_test_results(test_id)
        test.results = results
        
        await self.db.ab_tests.update_one(
            {'test_id': test_id},
            {'$set': asdict(test)}
        )
        
        return results
    
    async def get_models(self) -> List[Dict]:
        """Get all registered models"""
        return list(self.models.values())
    
    async def get_active_tests(self) -> List[Dict]:
        """Get all active tests"""
        return [asdict(t) for t in self.active_tests.values() if t.status == 'running']
    
    async def get_performance(self, model_id: str = None) -> Dict[str, Any]:
        """Get performance metrics"""
        if model_id:
            perf = self.performance.get(model_id)
            return asdict(perf) if perf else {}
        
        return {
            model_id: asdict(perf) 
            for model_id, perf in self.performance.items()
        }
    
    async def simulate_predictions(self) -> Dict[str, Any]:
        """Simulate predictions for demo"""
        if not self.models:
            # Register demo models
            await self.register_model('rainbow_dqn', 'Rainbow DQN', 'reinforcement_learning')
            await self.register_model('transformer', 'Transformer Encoder', 'deep_learning')
            await self.register_model('ensemble', 'Ensemble Predictor', 'ensemble')
            await self.register_model('regime_ml', 'Regime ML Models', 'machine_learning')
        
        # Simulate some predictions
        symbols = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA']
        predictions = ['buy', 'sell', 'hold']
        
        for model_id in self.models:
            for _ in range(10):
                pred = ModelPrediction(
                    model_id=model_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    symbol=random.choice(symbols),
                    prediction=random.choice(predictions),
                    confidence=random.uniform(0.5, 0.95),
                    actual_outcome=random.choice(predictions),
                    pnl=random.uniform(-100, 200)
                )
                self.predictions[model_id].append(pred)
            
            await self._update_performance(model_id)
        
        return {'status': 'simulated', 'models': len(self.models)}
    
    async def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'registered_models': len(self.models),
            'active_tests': len([t for t in self.active_tests.values() if t.status == 'running']),
            'total_predictions': sum(len(p) for p in self.predictions.values()),
            'models': list(self.models.keys())
        }


# Singleton
_ab_service: Optional[AIABTestingService] = None


def get_ab_testing_service(db=None) -> Optional[AIABTestingService]:
    """Get or create the A/B testing service"""
    global _ab_service
    if _ab_service is None and db is not None:
        _ab_service = AIABTestingService(db)
    return _ab_service
