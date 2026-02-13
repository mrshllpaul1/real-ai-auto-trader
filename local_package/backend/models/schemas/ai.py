"""
AI System Pydantic Models
Validation for AI/ML operations
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum
from .base import BaseResponse


class ModelType(str, Enum):
    ENSEMBLE = 'ensemble'
    LSTM = 'lstm'
    TRANSFORMER = 'transformer'
    RL_AGENT = 'rl_agent'
    TECHNICAL = 'technical'
    SENTIMENT = 'sentiment'
    PATTERN = 'pattern'


class TrainingStatus(str, Enum):
    IDLE = 'idle'
    TRAINING = 'training'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class PredictionConfidence(str, Enum):
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'


# Request Models
class TrainModelRequest(BaseModel):
    """Request to train AI model"""
    model_type: Optional[ModelType] = Field(default=None, description="Specific model to train, or all if None")
    force_retrain: bool = Field(default=False, description="Force retraining even if recent")
    epochs: int = Field(default=10, ge=1, le=100, description="Training epochs")
    learning_rate: float = Field(default=0.001, gt=0, lt=1)
    batch_size: int = Field(default=32, ge=1, le=512)
    coins: Optional[List[str]] = Field(default=None, description="Specific coins to train on")
    
    @field_validator('coins')
    @classmethod
    def normalize_coins(cls, v):
        if v:
            return [coin.upper().strip() for coin in v]
        return v


class PredictionRequest(BaseModel):
    """Request for AI prediction"""
    coin_id: str = Field(..., min_length=1, max_length=20)
    timeframe: Literal['1h', '4h', '1d', '1w'] = Field(default='1d')
    include_explanation: bool = Field(default=False)
    
    @field_validator('coin_id')
    @classmethod
    def normalize_coin(cls, v):
        return v.upper().strip()


class EnsembleConfigRequest(BaseModel):
    """Request to configure ensemble weights"""
    weights: Dict[str, float] = Field(..., description="Model weights")
    
    @field_validator('weights')
    @classmethod
    def validate_weights(cls, v):
        total = sum(v.values())
        if not (0.99 <= total <= 1.01):
            raise ValueError(f'Weights must sum to 1.0, got {total}')
        
        for model, weight in v.items():
            if weight < 0 or weight > 1:
                raise ValueError(f'Weight for {model} must be between 0 and 1')
        
        return v


class TethysEvaluateRequest(BaseModel):
    """Request for Tethys evaluation"""
    coin_id: str = Field(..., min_length=1, max_length=20)
    amount: Optional[float] = Field(default=None, gt=0)
    include_safety_check: bool = Field(default=True)
    
    @field_validator('coin_id')
    @classmethod
    def normalize_coin(cls, v):
        return v.upper().strip()


# Response Models
class ModelStatusResponse(BaseResponse):
    """Model status response"""
    model_type: ModelType
    status: TrainingStatus
    accuracy: Optional[float] = None
    last_trained: Optional[datetime] = None
    training_duration: Optional[float] = None
    metrics: Optional[Dict[str, float]] = None


class TrainingStatusResponse(BaseResponse):
    """Training status response"""
    is_training: bool
    current_model: Optional[ModelType] = None
    progress: float = 0
    eta_seconds: Optional[float] = None
    models_status: List[ModelStatusResponse] = []


class PredictionResponse(BaseResponse):
    """AI prediction response"""
    coin_id: str
    prediction: Literal['buy', 'sell', 'hold']
    confidence: float = Field(..., ge=0, le=1)
    confidence_level: PredictionConfidence
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None
    timeframe: str
    models_agreement: Dict[str, str] = {}
    explanation: Optional[str] = None
    generated_at: datetime


class EnsembleWeightsResponse(BaseResponse):
    """Ensemble weights response"""
    weights: Dict[str, float]
    last_optimized: Optional[datetime] = None
    optimization_score: Optional[float] = None


class TethysStatusResponse(BaseResponse):
    """Tethys AI status response"""
    is_active: bool
    safety_mode: bool
    last_evaluation: Optional[datetime] = None
    evaluations_today: int = 0
    trades_executed: int = 0
    win_rate: Optional[float] = None
    average_confidence: Optional[float] = None


class TethysEvaluationResponse(BaseResponse):
    """Tethys evaluation response"""
    coin_id: str
    recommendation: Literal['strong_buy', 'buy', 'hold', 'sell', 'strong_sell']
    confidence: float
    risk_score: float = Field(..., ge=0, le=1)
    expected_return: Optional[float] = None
    safety_passed: bool
    safety_warnings: List[str] = []
    supporting_factors: List[str] = []
    against_factors: List[str] = []
    suggested_position_size: Optional[float] = None
