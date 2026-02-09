"""
Portfolio Pydantic Models
Validation for portfolio operations
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
from .base import BaseResponse


class AssetType(str, Enum):
    CRYPTO = 'crypto'
    STABLECOIN = 'stablecoin'
    FIAT = 'fiat'


# Request Models
class PortfolioSnapshotRequest(BaseModel):
    """Request to create portfolio snapshot"""
    notes: Optional[str] = Field(default=None, max_length=500)
    include_valuations: bool = Field(default=True)


class RebalanceRequest(BaseModel):
    """Request to rebalance portfolio"""
    target_allocations: Dict[str, float] = Field(
        ..., 
        description="Target allocations as symbol -> percentage"
    )
    max_trade_amount: Optional[float] = Field(default=None, gt=0)
    min_trade_amount: float = Field(default=10.0, gt=0)
    dry_run: bool = Field(default=True)
    
    @field_validator('target_allocations')
    @classmethod
    def validate_allocations(cls, v):
        total = sum(v.values())
        if not (99.0 <= total <= 101.0):  # Allow small rounding errors
            raise ValueError(f'Allocations must sum to 100%, got {total}%')
        
        for symbol, pct in v.items():
            if pct < 0 or pct > 100:
                raise ValueError(f'Allocation for {symbol} must be between 0 and 100%')
        
        return {k.upper(): v for k, v in v.items()}


class AllocationUpdateRequest(BaseModel):
    """Request to update allocation"""
    symbol: str = Field(..., min_length=1, max_length=20)
    target_percentage: float = Field(..., ge=0, le=100)
    
    @field_validator('symbol')
    @classmethod
    def normalize_symbol(cls, v):
        return v.upper().strip()


# Response Models
class HoldingInfo(BaseModel):
    """Single holding information"""
    symbol: str
    asset_type: AssetType
    quantity: float
    average_cost: float
    current_price: float
    current_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    allocation_percent: float
    last_updated: datetime


class PortfolioSummaryResponse(BaseResponse):
    """Portfolio summary response"""
    total_value: float
    total_cost: float
    total_pnl: float
    total_pnl_percent: float
    holdings: List[HoldingInfo]
    cash_balance: float
    last_updated: datetime


class PortfolioSnapshotResponse(BaseResponse):
    """Portfolio snapshot response"""
    snapshot_id: str
    total_value: float
    holdings_count: int
    created_at: datetime
    notes: Optional[str] = None


class RebalancePreviewResponse(BaseResponse):
    """Rebalance preview response"""
    current_allocations: Dict[str, float]
    target_allocations: Dict[str, float]
    required_trades: List[Dict]
    estimated_fees: float
    total_trade_volume: float


class PerformanceMetrics(BaseModel):
    """Portfolio performance metrics"""
    daily_return: float
    weekly_return: float
    monthly_return: float
    all_time_return: float
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None
    total_trades: int
    profitable_trades: int


class PortfolioPerformanceResponse(BaseResponse):
    """Portfolio performance response"""
    metrics: PerformanceMetrics
    period_start: datetime
    period_end: datetime
    benchmark_comparison: Optional[Dict[str, float]] = None
