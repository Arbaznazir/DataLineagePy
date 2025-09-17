"""
High Availability Infrastructure Module
Health checking, circuit breakers, and fault tolerance components.
"""

from .health_checker import (
    HealthChecker,
    HealthStatus,
    CheckType,
    HealthCheck,
    HealthResult,
    ServiceHealth
)

from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    FailureType,
    CallResult,
    CircuitBreakerStats,
    CircuitBreakerOpenException,
    CircuitBreakerManager,
    circuit_breaker,
    circuit_breaker_manager
)

__all__ = [
    # Health Checker
    'HealthChecker',
    'HealthStatus',
    'CheckType',
    'HealthCheck',
    'HealthResult',
    'ServiceHealth',
    
    # Circuit Breaker
    'CircuitBreaker',
    'CircuitBreakerConfig',
    'CircuitState',
    'FailureType',
    'CallResult',
    'CircuitBreakerStats',
    'CircuitBreakerOpenException',
    'CircuitBreakerManager',
    'circuit_breaker',
    'circuit_breaker_manager'
]

# Module metadata
__version__ = "1.0.0"
__author__ = "DataLineagePy Infrastructure Team"
__description__ = "High availability infrastructure components for fault-tolerant applications"

# Supported health check types
SUPPORTED_CHECK_TYPES = [
    CheckType.HTTP,
    CheckType.TCP,
    CheckType.PING,
    CheckType.PROCESS,
    CheckType.DATABASE,
    CheckType.CUSTOM
]

# Default health check configurations
DEFAULT_HEALTH_CHECK_CONFIGS = {
    CheckType.HTTP: {
        'interval': 30,
        'timeout': 10,
        'retries': 3,
        'failure_threshold': 3,
        'success_threshold': 2
    },
    CheckType.TCP: {
        'interval': 15,
        'timeout': 5,
        'retries': 2,
        'failure_threshold': 3,
        'success_threshold': 2
    },
    CheckType.PING: {
        'interval': 60,
        'timeout': 5,
        'retries': 3,
        'failure_threshold': 5,
        'success_threshold': 3
    },
    CheckType.PROCESS: {
        'interval': 30,
        'timeout': 10,
        'retries': 1,
        'failure_threshold': 2,
        'success_threshold': 1
    },
    CheckType.DATABASE: {
        'interval': 45,
        'timeout': 15,
        'retries': 3,
        'failure_threshold': 3,
        'success_threshold': 2
    }
}

# Default circuit breaker configurations
DEFAULT_CIRCUIT_BREAKER_CONFIGS = {
    'web_service': CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=60,
        success_threshold=3,
        timeout=30.0,
        failure_rate_threshold=50.0,
        minimum_calls=10
    ),
    'database': CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=120,
        success_threshold=2,
        timeout=15.0,
        failure_rate_threshold=30.0,
        minimum_calls=5
    ),
    'external_api': CircuitBreakerConfig(
        failure_threshold=10,
        recovery_timeout=300,
        success_threshold=5,
        timeout=60.0,
        failure_rate_threshold=70.0,
        minimum_calls=20
    )
}
