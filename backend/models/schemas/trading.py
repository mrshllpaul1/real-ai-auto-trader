"""
Trading Pydantic Models
Validation for all trading operations
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum
from .base import BaseResponse, CoinSymbol


class OrderSide(str, Enum):
    BUY = 'buy'
    SELL = 'sell'


class OrderType(str, Enum):
    MARKET = 'market'
    LIMIT = 'limit'
    STOP_LOSS = 'stop_loss'
    TAKE_PROFIT = 'take_profit'
    TRAILING_STOP = 'trailing_stop'


class OrderStatus(str, Enum):
    PENDING = 'pending'
    OPEN = 'open'
    FILLED = 'filled'
    PARTIALLY_FILLED = 'partially_filled'
    CANCELLED = 'cancelled'
    REJECTED = 'rejected'
    EXPIRED = 'expired'


class TradingMode(str, Enum):
    PAPER = 'paper'
    REAL = 'real'


# Request Models
class CreateOrderRequest(BaseModel):
    """Request to create a new order"""
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading pair symbol")
    side: OrderSide
    order_type: OrderType = Field(default=OrderType.MARKET)
    amount: float = Field(..., gt=0, description="Order amount")
    price: Optional[float] = Field(default=None, gt=0, description="Limit price (required for limit orders)")
    stop_price: Optional[float] = Field(default=None, gt=0, description="Stop price for stop orders")
    time_in_force: Literal['GTC', 'IOC', 'FOK'] = Field(default='GTC')
    trading_mode: TradingMode = Field(default=TradingMode.PAPER)
    ai_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    notes: Optional[str] = Field(default=None, max_length=500)
    
    @field_validator('symbol')
    @classmethod
    def normalize_symbol(cls, v):
        return v.upper().strip()
    
    @model_validator(mode='after')
    def validate_price_for_limit_orders(self):
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError('Price is required for limit orders')
        return self
    
    @model_validator(mode='after')
    def validate_stop_price_for_stop_orders(self):
        if self.order_type in [OrderType.STOP_LOSS, OrderType.TRAILING_STOP] and self.stop_price is None:
            raise ValueError('Stop price is required for stop orders')
        return self


class CancelOrderRequest(BaseModel):
    """Request to cancel an order"""
    order_id: str = Field(..., min_length=1)
    reason: Optional[str] = Field(default=None, max_length=200)


class UpdateOrderRequest(BaseModel):
    """Request to update an existing order"""
    order_id: str = Field(..., min_length=1)
    new_price: Optional[float] = Field(default=None, gt=0)
    new_amount: Optional[float] = Field(default=None, gt=0)
    new_stop_price: Optional[float] = Field(default=None, gt=0)


# Response Models
class OrderResponse(BaseResponse):
    """Order response model"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    amount: float
    filled_amount: float = 0
    price: Optional[float] = None
    average_price: Optional[float] = None
    status: OrderStatus
    trading_mode: TradingMode
    created_at: datetime
    updated_at: Optional[datetime] = None
    fees: float = 0
    ai_confidence: Optional[float] = None


class TradeHistoryResponse(BaseResponse):
    """Trade history response"""
    trades: List[OrderResponse]
    total_trades: int
    total_volume: float
    realized_pnl: float


class TradingStatusResponse(BaseResponse):
    """Trading system status response"""
    is_active: bool
    trading_mode: TradingMode
    open_orders: int
    daily_trades: int
    daily_volume: float
    last_trade_at: Optional[datetime] = None
