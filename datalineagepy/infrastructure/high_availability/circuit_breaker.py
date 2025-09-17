"""
Circuit Breaker Implementation
Fault tolerance and resilience pattern for service calls.
"""

import time
import threading
import logging
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import statistics

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, calls are blocked
    HALF_OPEN = "half_open"  # Testing if service has recovered


class FailureType(Enum):
    """Types of failures that can trigger circuit breaker."""
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    HTTP_ERROR = "http_error"
    EXCEPTION = "exception"
    CUSTOM = "custom"


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5  # Number of failures to open circuit
    recovery_timeout: int = 60  # Seconds to wait before trying half-open
    success_threshold: int = 3  # Successful calls needed to close circuit
    timeout: float = 30.0  # Call timeout in seconds
    
    # Failure rate configuration
    failure_rate_threshold: float = 50.0  # Percentage
    minimum_calls: int = 10  # Minimum calls before calculating failure rate
    sliding_window_size: int = 100  # Size of sliding window for failure rate
    
    # Advanced options
    exponential_backoff: bool = True
    max_recovery_timeout: int = 300  # Maximum recovery timeout
    jitter: bool = True  # Add randomness to recovery timeout


@dataclass
class CallResult:
    """Result of a circuit breaker protected call."""
    success: bool
    response_time: float
    timestamp: float
    failure_type: Optional[FailureType] = None
    error_message: Optional[str] = None
    exception: Optional[Exception] = None


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics."""
    name: str
    state: CircuitState
    failure_count: int
    success_count: int
    total_calls: int
    failure_rate: float
    average_response_time: float
    last_failure_time: Optional[float]
    last_success_time: Optional[float]
    state_change_count: int
    uptime_percentage: float
    recovery_attempts: int


class CircuitBreaker:
    """
    Circuit breaker implementation for fault tolerance.
    
    Features:
    - Three states: CLOSED, OPEN, HALF_OPEN
    - Configurable failure thresholds and timeouts
    - Failure rate calculation with sliding window
    - Exponential backoff for recovery attempts
    - Comprehensive metrics and monitoring
    - Thread-safe operations
    - Custom failure detection
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize circuit breaker.
        
        Args:
            name: Circuit breaker name
            config: Configuration options
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        # State management
        self.state = CircuitState.CLOSED
        self.last_failure_time = 0
        self.last_success_time = 0
        self.state_change_time = time.time()
        
        # Counters
        self.failure_count = 0
        self.success_count = 0
        self.half_open_success_count = 0
        self.recovery_attempts = 0
        self.state_change_count = 0
        
        # Call history for failure rate calculation
        self.call_history: deque = deque(maxlen=self.config.sliding_window_size)
        
        # Threading
        self.lock = threading.RLock()
        
        # Callbacks
        self.state_change_callbacks: List[Callable[[str, CircuitState, CircuitState], None]] = []
        self.failure_callbacks: List[Callable[[str, CallResult], None]] = []
        
        # Statistics
        self.start_time = time.time()
        
        logger.info(f"Circuit breaker '{name}' initialized")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function call protected by circuit breaker.
        
        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenException: When circuit is open
            Exception: Original function exceptions
        """
        with self.lock:
            # Check if circuit allows the call
            if not self._can_execute():
                raise CircuitBreakerOpenException(
                    f"Circuit breaker '{self.name}' is OPEN"
                )
            
            start_time = time.time()
            
            try:
                # Execute the function with timeout
                result = self._execute_with_timeout(func, *args, **kwargs)
                
                # Record successful call
                response_time = time.time() - start_time
                call_result = CallResult(
                    success=True,
                    response_time=response_time,
                    timestamp=time.time()
                )
                
                self._record_success(call_result)
                return result
                
            except Exception as e:
                # Record failed call
                response_time = time.time() - start_time
                failure_type = self._classify_failure(e)
                
                call_result = CallResult(
                    success=False,
                    response_time=response_time,
                    timestamp=time.time(),
                    failure_type=failure_type,
                    error_message=str(e),
                    exception=e
                )
                
                self._record_failure(call_result)
                raise
    
    def _can_execute(self) -> bool:
        """Check if circuit breaker allows execution."""
        current_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if current_time - self.last_failure_time >= self._get_recovery_timeout():
                self._transition_to_half_open()
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            return True
        
        return False
    
    def _execute_with_timeout(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with timeout."""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Function call timed out after {self.config.timeout} seconds")
        
        # Set timeout (Unix-like systems)
        try:
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(self.config.timeout))
            
            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # Cancel timeout
                return result
            finally:
                signal.signal(signal.SIGALRM, old_handler)
                
        except AttributeError:
            # Windows doesn't support SIGALRM, use threading timeout
            import concurrent.futures
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    return future.result(timeout=self.config.timeout)
                except concurrent.futures.TimeoutError:
                    raise TimeoutError(f"Function call timed out after {self.config.timeout} seconds")
    
    def _classify_failure(self, exception: Exception) -> FailureType:
        """Classify the type of failure."""
        if isinstance(exception, TimeoutError):
            return FailureType.TIMEOUT
        elif isinstance(exception, ConnectionError):
            return FailureType.CONNECTION_ERROR
        elif hasattr(exception, 'response') and hasattr(exception.response, 'status_code'):
            # HTTP error (requests library)
            return FailureType.HTTP_ERROR
        else:
            return FailureType.EXCEPTION
    
    def _record_success(self, call_result: CallResult):
        """Record a successful call."""
        self.success_count += 1
        self.last_success_time = call_result.timestamp
        self.call_history.append(call_result)
        
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_success_count += 1
            
            # Check if we should close the circuit
            if self.half_open_success_count >= self.config.success_threshold:
                self._transition_to_closed()
        
        logger.debug(f"Circuit breaker '{self.name}': Successful call recorded")
    
    def _record_failure(self, call_result: CallResult):
        """Record a failed call."""
        self.failure_count += 1
        self.last_failure_time = call_result.timestamp
        self.call_history.append(call_result)
        
        # Trigger failure callbacks
        for callback in self.failure_callbacks:
            try:
                callback(self.name, call_result)
            except Exception as e:
                logger.error(f"Failure callback error: {str(e)}")
        
        # Check if we should open the circuit
        if self.state == CircuitState.CLOSED:
            if self._should_open_circuit():
                self._transition_to_open()
        elif self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open state opens the circuit
            self._transition_to_open()
        
        logger.debug(f"Circuit breaker '{self.name}': Failure recorded ({call_result.failure_type})")
    
    def _should_open_circuit(self) -> bool:
        """Determine if circuit should be opened."""
        # Check failure count threshold
        if self.failure_count >= self.config.failure_threshold:
            return True
        
        # Check failure rate threshold
        if len(self.call_history) >= self.config.minimum_calls:
            failure_rate = self._calculate_failure_rate()
            if failure_rate >= self.config.failure_rate_threshold:
                return True
        
        return False
    
    def _calculate_failure_rate(self) -> float:
        """Calculate current failure rate."""
        if not self.call_history:
            return 0.0
        
        failed_calls = sum(1 for call in self.call_history if not call.success)
        total_calls = len(self.call_history)
        
        return (failed_calls / total_calls) * 100
    
    def _transition_to_open(self):
        """Transition circuit breaker to OPEN state."""
        old_state = self.state
        self.state = CircuitState.OPEN
        self.state_change_time = time.time()
        self.state_change_count += 1
        self.half_open_success_count = 0
        
        self._trigger_state_change_callbacks(old_state, self.state)
        
        logger.warning(f"Circuit breaker '{self.name}' opened (failures: {self.failure_count})")
    
    def _transition_to_half_open(self):
        """Transition circuit breaker to HALF_OPEN state."""
        old_state = self.state
        self.state = CircuitState.HALF_OPEN
        self.state_change_time = time.time()
        self.state_change_count += 1
        self.half_open_success_count = 0
        self.recovery_attempts += 1
        
        self._trigger_state_change_callbacks(old_state, self.state)
        
        logger.info(f"Circuit breaker '{self.name}' half-opened (attempt #{self.recovery_attempts})")
    
    def _transition_to_closed(self):
        """Transition circuit breaker to CLOSED state."""
        old_state = self.state
        self.state = CircuitState.CLOSED
        self.state_change_time = time.time()
        self.state_change_count += 1
        self.failure_count = 0  # Reset failure count
        self.half_open_success_count = 0
        
        self._trigger_state_change_callbacks(old_state, self.state)
        
        logger.info(f"Circuit breaker '{self.name}' closed (recovered)")
    
    def _get_recovery_timeout(self) -> float:
        """Get recovery timeout with exponential backoff."""
        if not self.config.exponential_backoff:
            timeout = self.config.recovery_timeout
        else:
            # Exponential backoff: base_timeout * (2 ^ recovery_attempts)
            timeout = self.config.recovery_timeout * (2 ** min(self.recovery_attempts, 5))
            timeout = min(timeout, self.config.max_recovery_timeout)
        
        # Add jitter to prevent thundering herd
        if self.config.jitter:
            import random
            jitter = random.uniform(0.8, 1.2)
            timeout *= jitter
        
        return timeout
    
    def _trigger_state_change_callbacks(self, old_state: CircuitState, new_state: CircuitState):
        """Trigger state change callbacks."""
        for callback in self.state_change_callbacks:
            try:
                callback(self.name, old_state, new_state)
            except Exception as e:
                logger.error(f"State change callback error: {str(e)}")
    
    def add_state_change_callback(self, callback: Callable[[str, CircuitState, CircuitState], None]):
        """Add state change callback."""
        self.state_change_callbacks.append(callback)
    
    def add_failure_callback(self, callback: Callable[[str, CallResult], None]):
        """Add failure callback."""
        self.failure_callbacks.append(callback)
    
    def force_open(self):
        """Manually force circuit breaker to OPEN state."""
        with self.lock:
            if self.state != CircuitState.OPEN:
                self._transition_to_open()
                logger.info(f"Circuit breaker '{self.name}' manually opened")
    
    def force_close(self):
        """Manually force circuit breaker to CLOSED state."""
        with self.lock:
            if self.state != CircuitState.CLOSED:
                self._transition_to_closed()
                logger.info(f"Circuit breaker '{self.name}' manually closed")
    
    def force_half_open(self):
        """Manually force circuit breaker to HALF_OPEN state."""
        with self.lock:
            if self.state != CircuitState.HALF_OPEN:
                self._transition_to_half_open()
                logger.info(f"Circuit breaker '{self.name}' manually half-opened")
    
    def reset(self):
        """Reset circuit breaker to initial state."""
        with self.lock:
            old_state = self.state
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.half_open_success_count = 0
            self.recovery_attempts = 0
            self.last_failure_time = 0
            self.last_success_time = 0
            self.state_change_time = time.time()
            self.call_history.clear()
            
            if old_state != CircuitState.CLOSED:
                self._trigger_state_change_callbacks(old_state, self.state)
            
            logger.info(f"Circuit breaker '{self.name}' reset")
    
    def get_stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics."""
        with self.lock:
            total_calls = self.success_count + self.failure_count
            failure_rate = self._calculate_failure_rate()
            
            # Calculate average response time
            if self.call_history:
                avg_response_time = statistics.mean([call.response_time for call in self.call_history])
            else:
                avg_response_time = 0.0
            
            # Calculate uptime percentage
            uptime = time.time() - self.start_time
            if self.state == CircuitState.OPEN:
                downtime = time.time() - self.last_failure_time
                uptime_percentage = max(0, (uptime - downtime) / uptime * 100)
            else:
                uptime_percentage = 100.0
            
            return CircuitBreakerStats(
                name=self.name,
                state=self.state,
                failure_count=self.failure_count,
                success_count=self.success_count,
                total_calls=total_calls,
                failure_rate=failure_rate,
                average_response_time=avg_response_time,
                last_failure_time=self.last_failure_time if self.last_failure_time > 0 else None,
                last_success_time=self.last_success_time if self.last_success_time > 0 else None,
                state_change_count=self.state_change_count,
                uptime_percentage=uptime_percentage,
                recovery_attempts=self.recovery_attempts
            )
    
    def get_state(self) -> CircuitState:
        """Get current circuit breaker state."""
        return self.state
    
    def is_closed(self) -> bool:
        """Check if circuit breaker is closed."""
        return self.state == CircuitState.CLOSED
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open."""
        return self.state == CircuitState.OPEN
    
    def is_half_open(self) -> bool:
        """Check if circuit breaker is half-open."""
        return self.state == CircuitState.HALF_OPEN


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreakerManager:
    """
    Manager for multiple circuit breakers.
    
    Features:
    - Centralized circuit breaker management
    - Global statistics and monitoring
    - Bulk operations
    - Configuration management
    """
    
    def __init__(self):
        """Initialize circuit breaker manager."""
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.lock = threading.RLock()
        
        logger.info("Circuit breaker manager initialized")
    
    def get_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """
        Get or create a circuit breaker.
        
        Args:
            name: Circuit breaker name
            config: Configuration (used only for new circuit breakers)
            
        Returns:
            Circuit breaker instance
        """
        with self.lock:
            if name not in self.circuit_breakers:
                self.circuit_breakers[name] = CircuitBreaker(name, config)
                logger.info(f"Created new circuit breaker: {name}")
            
            return self.circuit_breakers[name]
    
    def remove_circuit_breaker(self, name: str) -> bool:
        """
        Remove a circuit breaker.
        
        Args:
            name: Circuit breaker name
            
        Returns:
            True if removed, False if not found
        """
        with self.lock:
            if name in self.circuit_breakers:
                del self.circuit_breakers[name]
                logger.info(f"Removed circuit breaker: {name}")
                return True
            return False
    
    def get_all_stats(self) -> Dict[str, CircuitBreakerStats]:
        """Get statistics for all circuit breakers."""
        with self.lock:
            return {name: cb.get_stats() for name, cb in self.circuit_breakers.items()}
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global circuit breaker statistics."""
        with self.lock:
            total_breakers = len(self.circuit_breakers)
            open_breakers = sum(1 for cb in self.circuit_breakers.values() if cb.is_open())
            half_open_breakers = sum(1 for cb in self.circuit_breakers.values() if cb.is_half_open())
            closed_breakers = sum(1 for cb in self.circuit_breakers.values() if cb.is_closed())
            
            total_calls = sum(cb.success_count + cb.failure_count for cb in self.circuit_breakers.values())
            total_failures = sum(cb.failure_count for cb in self.circuit_breakers.values())
            
            return {
                "total_circuit_breakers": total_breakers,
                "open_breakers": open_breakers,
                "half_open_breakers": half_open_breakers,
                "closed_breakers": closed_breakers,
                "total_calls": total_calls,
                "total_failures": total_failures,
                "global_success_rate": ((total_calls - total_failures) / max(total_calls, 1)) * 100
            }
    
    def reset_all(self):
        """Reset all circuit breakers."""
        with self.lock:
            for cb in self.circuit_breakers.values():
                cb.reset()
            logger.info("Reset all circuit breakers")
    
    def force_open_all(self):
        """Force all circuit breakers to OPEN state."""
        with self.lock:
            for cb in self.circuit_breakers.values():
                cb.force_open()
            logger.info("Forced all circuit breakers to OPEN")
    
    def force_close_all(self):
        """Force all circuit breakers to CLOSED state."""
        with self.lock:
            for cb in self.circuit_breakers.values():
                cb.force_close()
            logger.info("Forced all circuit breakers to CLOSED")
    
    def shutdown(self):
        """Shutdown circuit breaker manager."""
        with self.lock:
            self.circuit_breakers.clear()
            logger.info("Circuit breaker manager shutdown complete")


# Global circuit breaker manager instance
circuit_breaker_manager = CircuitBreakerManager()


def circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None):
    """
    Decorator for circuit breaker protection.
    
    Args:
        name: Circuit breaker name
        config: Circuit breaker configuration
        
    Returns:
        Decorated function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            cb = circuit_breaker_manager.get_circuit_breaker(name, config)
            return cb.call(func, *args, **kwargs)
        return wrapper
    return decorator
