"""
Event Triggers Pydantic Models
Validation for event trigger operations
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum
from .base import BaseResponse


class TriggerType(str, Enum):
    PRICE_ABOVE = 'price_above'
    PRICE_BELOW = 'price_below'
    PRICE_CHANGE_PERCENT = 'price_change_percent'
    VOLUME_SPIKE = 'volume_spike'
    NEWS_KEYWORD = 'news_keyword'
    SENTIMENT_CHANGE = 'sentiment_change'
    CUSTOM = 'custom'


class TriggerAction(str, Enum):
    NOTIFY = 'notify'
    BUY = 'buy'
    SELL = 'sell'
    ALERT = 'alert'
    WEBHOOK = 'webhook'


class TriggerStatus(str, Enum):
    ACTIVE = 'active'
    PAUSED = 'paused'
    TRIGGERED = 'triggered'
    EXPIRED = 'expired'
    DISABLED = 'disabled'


# Request Models
class CreateTriggerRequest(BaseModel):
    """Request to create a new trigger"""
    name: str = Field(..., min_length=1, max_length=100, description="Trigger name")
    description: Optional[str] = Field(default=None, max_length=500)
    trigger_type: TriggerType
    coins: List[str] = Field(..., min_length=1, max_length=50, description="Coins to monitor")
    conditions: Dict[str, Any] = Field(..., description="Trigger conditions")
    action: TriggerAction = Field(default=TriggerAction.NOTIFY)
    action_params: Optional[Dict[str, Any]] = Field(default=None)
    is_active: bool = Field(default=True)
    expires_at: Optional[datetime] = Field(default=None)
    cooldown_minutes: int = Field(default=60, ge=0, le=1440)
    max_triggers: Optional[int] = Field(default=None, ge=1)
    
    @field_validator('coins')
    @classmethod
    def normalize_coins(cls, v):
        return [coin.upper().strip() for coin in v]
    
    @model_validator(mode='after')
    def validate_conditions(self):
        trigger_type = self.trigger_type
        conditions = self.conditions
        
        # Validate required conditions based on type
        if trigger_type in [TriggerType.PRICE_ABOVE, TriggerType.PRICE_BELOW]:
            if 'price' not in conditions:
                raise ValueError(f'Price condition required for {trigger_type}')
            if conditions['price'] <= 0:
                raise ValueError('Price must be positive')
        
        if trigger_type == TriggerType.PRICE_CHANGE_PERCENT:
            if 'percent' not in conditions:
                raise ValueError('Percent condition required for price_change_percent')
            if abs(conditions['percent']) > 100:
                raise ValueError('Percent must be between -100 and 100')
        
        if trigger_type == TriggerType.NEWS_KEYWORD:
            if 'keywords' not in conditions or not conditions['keywords']:
                raise ValueError('Keywords required for news_keyword trigger')
        
        return self


class UpdateTriggerRequest(BaseModel):
    """Request to update a trigger"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    conditions: Optional[Dict[str, Any]] = None
    action: Optional[TriggerAction] = None
    action_params: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    cooldown_minutes: Optional[int] = Field(default=None, ge=0, le=1440)


class TriggerCheckRequest(BaseModel):
    """Request to manually check triggers"""
    trigger_ids: Optional[List[str]] = Field(default=None)
    force: bool = Field(default=False, description="Force check even in cooldown")


# Response Models
class TriggerResponse(BaseResponse):
    """Trigger response model"""
    id: str
    name: str
    description: Optional[str] = None
    trigger_type: TriggerType
    coins: List[str]
    conditions: Dict[str, Any]
    action: TriggerAction
    action_params: Optional[Dict[str, Any]] = None
    status: TriggerStatus
    is_active: bool
    trigger_count: int = 0
    last_triggered_at: Optional[datetime] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    cooldown_minutes: int


class TriggerListResponse(BaseResponse):
    """List of triggers response"""
    triggers: List[TriggerResponse]
    total: int
    active_count: int
    triggered_today: int


class TriggerHistoryItem(BaseModel):
    """Single trigger history item"""
    trigger_id: str
    trigger_name: str
    triggered_at: datetime
    conditions_met: Dict[str, Any]
    action_taken: TriggerAction
    result: str
    coins_affected: List[str]


class TriggerHistoryResponse(BaseResponse):
    """Trigger history response"""
    history: List[TriggerHistoryItem]
    total: int
