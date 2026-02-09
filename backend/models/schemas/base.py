"""
Base Pydantic Models
Shared base models and validators
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import re
import uuid


class ResponseStatus(str, Enum):
    """Standard response status"""
    SUCCESS = 'success'
    ERROR = 'error'
    PENDING = 'pending'


class BaseResponse(BaseModel):
    """Base response model"""
    model_config = ConfigDict(from_attributes=True)
    
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4())[:8])


class ErrorResponse(BaseResponse):
    """Error response model"""
    status: ResponseStatus = ResponseStatus.ERROR
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseResponse):
    """Paginated response model"""
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class DateRangeParams(BaseModel):
    """Date range parameters"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    @field_validator('end_date')
    @classmethod
    def end_after_start(cls, v, info):
        if v and info.data.get('start_date') and v < info.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class CoinSymbol(BaseModel):
    """Validated coin symbol"""
    symbol: str = Field(..., min_length=1, max_length=20)
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        v = v.upper().strip()
        if not re.match(r'^[A-Z0-9]+$', v):
            raise ValueError('Symbol must contain only letters and numbers')
        return v


class MonetaryAmount(BaseModel):
    """Validated monetary amount"""
    amount: float = Field(..., gt=0, description="Amount must be positive")
    currency: str = Field(default='USD', max_length=10)
    
    @field_validator('amount')
    @classmethod
    def round_amount(cls, v):
        return round(v, 8)  # 8 decimal places for crypto
