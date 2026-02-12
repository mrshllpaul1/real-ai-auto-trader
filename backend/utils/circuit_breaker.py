"""
Circuit Breaker Pattern
=======================
Prevents cascade failures when external services are down.
States:
- CLOSED: Normal operation
- OPEN: Service failing, reject calls immediately
- HALF_OPEN: Testing if service recovered

Usage:
    kraken_breaker = CircuitBreaker("kraken", failure_threshold=3)
    
    async def get_kraken_data():
        return await kraken_breaker.call(kraken_api.get_data)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Optional
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerOpenError(Exception):
    """Raised when circuit is open"""
    def __init__(self, name: str, retry_after: float):
        self.name = name
        self.retry_after = retry_after
        super().__init__(f"Circuit breaker '{name}' is OPEN. Retry after {retry_after:.1f}s")


class CircuitBreaker:
    """
    Circuit breaker implementation for external service calls.
    Protects against cascade failures.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        half_open_max_calls: int = 3,
        success_threshold: int = 2
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Identifier for this circuit breaker
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds to wait before trying recovery
            half_open_max_calls: Max calls allowed in half-open state
            success_threshold: Successes needed to close circuit from half-open
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.success_threshold = success_threshold
        
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._successes = 0
        self._half_open_calls = 0
        self._last_failure_time: Optional[datetime] = None
        self._lock = asyncio.Lock()
        
        # Statistics
        self._stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'rejected_calls': 0,
            'state_changes': 0,
        }
        
        logger.info(f"⚡ Circuit breaker '{name}' initialized (threshold={failure_threshold})")
    
    @property
    def state(self) -> CircuitState:
        """Get current state"""
        return self._state
    
    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)"""
        return self._state == CircuitState.CLOSED
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open (rejecting calls)"""
        return self._state == CircuitState.OPEN
    
    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to try recovery"""
        if self._last_failure_time is None:
            return True
        return datetime.now() > self._last_failure_time + timedelta(seconds=self.recovery_timeout)
    
    def _get_retry_after(self) -> float:
        """Get seconds until retry is allowed"""
        if self._last_failure_time is None:
            return 0
        elapsed = (datetime.now() - self._last_failure_time).total_seconds()
        return max(0, self.recovery_timeout - elapsed)
    
    async def _transition_to(self, new_state: CircuitState):
        """Transition to a new state"""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            self._stats['state_changes'] += 1
            logger.warning(
                f"⚡ Circuit '{self.name}' state change: {old_state.value} -> {new_state.value}"
            )
            
            if new_state == CircuitState.CLOSED:
                self._failures = 0
                self._successes = 0
            elif new_state == CircuitState.HALF_OPEN:
                self._half_open_calls = 0
                self._successes = 0
    
    async def _record_success(self):
        """Record a successful call"""
        async with self._lock:
            self._stats['successful_calls'] += 1
            
            if self._state == CircuitState.HALF_OPEN:
                self._successes += 1
                if self._successes >= self.success_threshold:
                    await self._transition_to(CircuitState.CLOSED)
            else:
                self._failures = 0  # Reset failure count on success
    
    async def _record_failure(self, error: Exception):
        """Record a failed call"""
        async with self._lock:
            self._stats['failed_calls'] += 1
            self._failures += 1
            self._last_failure_time = datetime.now()
            
            logger.warning(f"⚡ Circuit '{self.name}' failure #{self._failures}: {error}")
            
            if self._state == CircuitState.HALF_OPEN:
                await self._transition_to(CircuitState.OPEN)
            elif self._failures >= self.failure_threshold:
                await self._transition_to(CircuitState.OPEN)
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Async function to call
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        self._stats['total_calls'] += 1
        
        # Check if circuit should transition from OPEN to HALF_OPEN
        async with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_recovery():
                    await self._transition_to(CircuitState.HALF_OPEN)
                else:
                    self._stats['rejected_calls'] += 1
                    raise CircuitBreakerOpenError(self.name, self._get_retry_after())
            
            # Rate limit half-open calls
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    self._stats['rejected_calls'] += 1
                    raise CircuitBreakerOpenError(self.name, self._get_retry_after())
                self._half_open_calls += 1
        
        # Execute the function
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            await self._record_success()
            return result
        except Exception as e:
            await self._record_failure(e)
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            'name': self.name,
            'state': self._state.value,
            'failures': self._failures,
            'successes': self._successes,
            'retry_after': self._get_retry_after() if self._state == CircuitState.OPEN else 0,
            **self._stats,
        }


# Global registry of circuit breakers
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 30
) -> CircuitBreaker:
    """Get or create a circuit breaker by name"""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout
        )
    return _circuit_breakers[name]


def get_all_circuit_breakers() -> Dict[str, Dict]:
    """Get stats for all circuit breakers"""
    return {name: cb.get_stats() for name, cb in _circuit_breakers.items()}


def circuit_protected(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 30,
    fallback: Callable = None
):
    """
    Decorator to protect a function with circuit breaker.
    
    Usage:
        @circuit_protected("kraken", failure_threshold=3, fallback=get_cached_data)
        async def get_kraken_prices():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            breaker = get_circuit_breaker(name, failure_threshold, recovery_timeout)
            try:
                return await breaker.call(func, *args, **kwargs)
            except CircuitBreakerOpenError as e:
                if fallback:
                    logger.warning(f"⚡ Circuit '{name}' open, using fallback")
                    if asyncio.iscoroutinefunction(fallback):
                        return await fallback(*args, **kwargs)
                    return fallback(*args, **kwargs)
                raise
        return wrapper
    return decorator
