"""
Scalability Infrastructure Module
Auto-scaling, load balancing, and distributed processing components.
"""

from .load_balancer import (
    LoadBalancer,
    LoadBalancingAlgorithm,
    BackendServer,
    ServerStatus,
    LoadBalancerStats
)

from .horizontal_scaler import (
    HorizontalScaler,
    ScalingDirection,
    ScalingTrigger,
    ScalingRule,
    ScalingEvent,
    InstanceMetrics
)

__all__ = [
    # Load Balancer
    'LoadBalancer',
    'LoadBalancingAlgorithm',
    'BackendServer',
    'ServerStatus',
    'LoadBalancerStats',
    
    # Horizontal Scaler
    'HorizontalScaler',
    'ScalingDirection',
    'ScalingTrigger',
    'ScalingRule',
    'ScalingEvent',
    'InstanceMetrics'
]

# Module metadata
__version__ = "1.0.0"
__author__ = "DataLineagePy Infrastructure Team"
__description__ = "Scalability infrastructure components for enterprise-grade applications"

# Supported scaling algorithms
SUPPORTED_SCALING_TRIGGERS = [
    ScalingTrigger.CPU_UTILIZATION,
    ScalingTrigger.MEMORY_UTILIZATION,
    ScalingTrigger.REQUEST_RATE,
    ScalingTrigger.RESPONSE_TIME,
    ScalingTrigger.QUEUE_LENGTH,
    ScalingTrigger.CUSTOM_METRIC
]

# Supported load balancing algorithms
SUPPORTED_LB_ALGORITHMS = [
    LoadBalancingAlgorithm.ROUND_ROBIN,
    LoadBalancingAlgorithm.LEAST_CONNECTIONS,
    LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN,
    LoadBalancingAlgorithm.IP_HASH,
    LoadBalancingAlgorithm.LEAST_RESPONSE_TIME,
    LoadBalancingAlgorithm.RANDOM
]
