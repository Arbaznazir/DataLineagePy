"""
Retry handler for enterprise integrations.
"""

import asyncio
import logging
import random
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, Type, Union
from datetime import datetime, timedelta
from enum import Enum
import time
import functools

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategies."""
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIBONACCI = "fibonacci"
    CUSTOM = "custom"


@dataclass
class RetryConfig:
    """Retry configuration."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    backoff_factor: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.1
    retry_on_exceptions: List[Type[Exception]] = field(default_factory=lambda: [Exception])
    stop_on_exceptions: List[Type[Exception]] = field(default_factory=list)
    timeout: Optional[float] = None
    custom_delay_func: Optional[Callable[[int], float]] = None


@dataclass
class RetryAttempt:
    """Information about a retry attempt."""
    attempt_number: int
    exception: Optional[Exception]
    delay: float
    timestamp: datetime
    total_elapsed: float


class RetryHandler:
    """Handles retry logic for enterprise integrations."""
    
    def __init__(self, config: RetryConfig):
        self.config = config
        self.attempts: List[RetryAttempt] = []
        self.start_time: Optional[datetime] = None
        
    def _should_retry(self, exception: Exception, attempt_number: int) -> bool:
        """Determine if we should retry based on exception and attempt count."""
        # Check if we've exceeded max attempts
        if attempt_number >= self.config.max_attempts:
            return False
        
        # Check if exception is in stop list
        for stop_exception in self.config.stop_on_exceptions:
            if isinstance(exception, stop_exception):
                return False
        
        # Check if exception is in retry list
        for retry_exception in self.config.retry_on_exceptions:
            if isinstance(exception, retry_exception):
                return True
        
        return False
    
    def _calculate_delay(self, attempt_number: int) -> float:
        """Calculate delay for the given attempt number."""
        if self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.base_delay
        
        elif self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (self.config.backoff_factor ** (attempt_number - 1))
        
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.base_delay * attempt_number
        
        elif self.config.strategy == RetryStrategy.FIBONACCI:
            delay = self.config.base_delay * self._fibonacci(attempt_number)
        
        elif self.config.strategy == RetryStrategy.CUSTOM:
            if self.config.custom_delay_func:
                delay = self.config.custom_delay_func(attempt_number)
            else:
                delay = self.config.base_delay
        
        else:
            delay = self.config.base_delay
        
        # Apply max delay limit
        delay = min(delay, self.config.max_delay)
        
        # Apply jitter if enabled
        if self.config.jitter:
            jitter_amount = delay * self.config.jitter_factor
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0, delay)
    
    def _fibonacci(self, n: int) -> int:
        """Calculate fibonacci number."""
        if n <= 1:
            return n
        
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        
        return b
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        self.start_time = datetime.utcnow()
        self.attempts = []
        
        for attempt_number in range(1, self.config.max_attempts + 1):
            try:
                # Check timeout
                if self.config.timeout:
                    elapsed = (datetime.utcnow() - self.start_time).total_seconds()
                    if elapsed >= self.config.timeout:
                        raise TimeoutError(f"Retry timeout exceeded: {elapsed}s")
                
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Success - log attempt and return
                attempt = RetryAttempt(
                    attempt_number=attempt_number,
                    exception=None,
                    delay=0,
                    timestamp=datetime.utcnow(),
                    total_elapsed=(datetime.utcnow() - self.start_time).total_seconds()
                )
                self.attempts.append(attempt)
                
                logger.info(f"Function succeeded on attempt {attempt_number}")
                return result
                
            except Exception as e:
                # Calculate elapsed time
                elapsed = (datetime.utcnow() - self.start_time).total_seconds()
                
                # Check if we should retry
                if not self._should_retry(e, attempt_number):
                    attempt = RetryAttempt(
                        attempt_number=attempt_number,
                        exception=e,
                        delay=0,
                        timestamp=datetime.utcnow(),
                        total_elapsed=elapsed
                    )
                    self.attempts.append(attempt)
                    
                    logger.error(f"Function failed on attempt {attempt_number}, not retrying: {e}")
                    raise
                
                # Calculate delay for next attempt
                delay = self._calculate_delay(attempt_number)
                
                # Record attempt
                attempt = RetryAttempt(
                    attempt_number=attempt_number,
                    exception=e,
                    delay=delay,
                    timestamp=datetime.utcnow(),
                    total_elapsed=elapsed
                )
                self.attempts.append(attempt)
                
                logger.warning(f"Function failed on attempt {attempt_number}, retrying in {delay:.2f}s: {e}")
                
                # Wait before retry
                if delay > 0:
                    await asyncio.sleep(delay)
        
        # All attempts failed
        last_exception = self.attempts[-1].exception if self.attempts else Exception("Unknown error")
        logger.error(f"Function failed after {self.config.max_attempts} attempts")
        raise last_exception
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retry statistics."""
        if not self.attempts:
            return {}
        
        total_elapsed = (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0
        
        return {
            'total_attempts': len(self.attempts),
            'successful': self.attempts[-1].exception is None,
            'total_elapsed': total_elapsed,
            'average_delay': sum(a.delay for a in self.attempts) / len(self.attempts),
            'max_delay': max(a.delay for a in self.attempts),
            'exceptions': [str(a.exception) for a in self.attempts if a.exception]
        }


def retry_with_config(config: RetryConfig):
    """Decorator to add retry logic to functions."""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            handler = RetryHandler(config)
            return await handler.execute_with_retry(func, *args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            handler = RetryHandler(config)
            return asyncio.run(handler.execute_with_retry(func, *args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def retry(max_attempts: int = 3, 
          base_delay: float = 1.0,
          strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
          **kwargs):
    """Simple retry decorator."""
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        strategy=strategy,
        **kwargs
    )
    return retry_with_config(config)


class CircuitBreakerRetryHandler(RetryHandler):
    """Retry handler with circuit breaker pattern."""
    
    def __init__(self, config: RetryConfig, failure_threshold: int = 5, 
                 recovery_timeout: float = 60.0):
        super().__init__(config)
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.circuit_open = False
    
    def _should_retry(self, exception: Exception, attempt_number: int) -> bool:
        """Override to include circuit breaker logic."""
        # Check circuit breaker state
        if self.circuit_open:
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if elapsed < self.recovery_timeout:
                    logger.warning("Circuit breaker is open, not retrying")
                    return False
                else:
                    # Try to close circuit
                    self.circuit_open = False
                    self.failure_count = 0
                    logger.info("Circuit breaker recovery attempt")
        
        return super()._should_retry(exception, attempt_number)
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute with circuit breaker logic."""
        try:
            result = await super().execute_with_retry(func, *args, **kwargs)
            
            # Success - reset failure count
            self.failure_count = 0
            self.circuit_open = False
            
            return result
            
        except Exception as e:
            # Increment failure count
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            
            # Check if we should open circuit
            if self.failure_count >= self.failure_threshold:
                self.circuit_open = True
                logger.error(f"Circuit breaker opened after {self.failure_count} failures")
            
            raise


def create_retry_handler(max_attempts: int = 3,
                        base_delay: float = 1.0,
                        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
                        **kwargs) -> RetryHandler:
    """Factory function to create retry handler."""
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        strategy=strategy,
        **kwargs
    )
    return RetryHandler(config)


def create_circuit_breaker_retry_handler(max_attempts: int = 3,
                                       base_delay: float = 1.0,
                                       failure_threshold: int = 5,
                                       recovery_timeout: float = 60.0,
                                       **kwargs) -> CircuitBreakerRetryHandler:
    """Factory function to create circuit breaker retry handler."""
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        **kwargs
    )
    return CircuitBreakerRetryHandler(config, failure_threshold, recovery_timeout)
