"""
Infrastructure Module
Enterprise-grade infrastructure components for scalability, high availability, and production deployment.
"""

from .scalability import (
    LoadBalancer,
    HorizontalScaler,
    DistributedProcessor,
    CacheManager,
    MessageQueue
)

from .high_availability import (
    HealthChecker,
    FailoverManager,
    CircuitBreaker,
    RetryManager,
    ServiceRegistry
)

from .deployment import (
    KubernetesDeployer,
    DockerManager,
    ConfigManager,
    SecretsManager,
    ServiceMesh
)

from .monitoring import (
    MetricsCollector,
    AlertManager,
    LogAggregator,
    PerformanceMonitor,
    InfrastructureMonitor
)

from .storage import (
    DatabaseCluster,
    StorageManager,
    BackupManager,
    DataReplication,
    CacheCluster
)

__all__ = [
    # Scalability
    'LoadBalancer',
    'HorizontalScaler', 
    'DistributedProcessor',
    'CacheManager',
    'MessageQueue',
    
    # High Availability
    'HealthChecker',
    'FailoverManager',
    'CircuitBreaker',
    'RetryManager',
    'ServiceRegistry',
    
    # Deployment
    'KubernetesDeployer',
    'DockerManager',
    'ConfigManager',
    'SecretsManager',
    'ServiceMesh',
    
    # Monitoring
    'MetricsCollector',
    'AlertManager',
    'LogAggregator',
    'PerformanceMonitor',
    'InfrastructureMonitor',
    
    # Storage
    'DatabaseCluster',
    'StorageManager',
    'BackupManager',
    'DataReplication',
    'CacheCluster'
]

# Infrastructure metadata
INFRASTRUCTURE_VERSION = "1.0.0"
SUPPORTED_PLATFORMS = ["kubernetes", "docker", "aws", "azure", "gcp"]
SUPPORTED_DATABASES = ["postgresql", "mongodb", "redis", "elasticsearch"]
SUPPORTED_MESSAGE_QUEUES = ["rabbitmq", "kafka", "redis", "aws-sqs"]

def setup_enterprise_infrastructure(environment: str = "production") -> dict:
    """
    Quick setup for enterprise infrastructure components.
    
    Args:
        environment: Target environment (development, staging, production)
        
    Returns:
        Dictionary with initialized infrastructure components
    """
    try:
        components = {}
        
        # Initialize core infrastructure based on environment
        if environment == "production":
            # Production setup with full HA and scalability
            components["load_balancer"] = LoadBalancer(algorithm="round_robin")
            components["scaler"] = HorizontalScaler(min_instances=3, max_instances=50)
            components["health_checker"] = HealthChecker(check_interval=30)
            components["failover"] = FailoverManager(failover_timeout=60)
            components["circuit_breaker"] = CircuitBreaker(failure_threshold=5)
            components["cache"] = CacheManager(cluster_mode=True)
            components["message_queue"] = MessageQueue(ha_mode=True)
            
        elif environment == "staging":
            # Staging setup with moderate scalability
            components["load_balancer"] = LoadBalancer(algorithm="least_connections")
            components["scaler"] = HorizontalScaler(min_instances=2, max_instances=10)
            components["health_checker"] = HealthChecker(check_interval=60)
            components["cache"] = CacheManager(cluster_mode=False)
            components["message_queue"] = MessageQueue(ha_mode=False)
            
        else:
            # Development setup with minimal infrastructure
            components["health_checker"] = HealthChecker(check_interval=120)
            components["cache"] = CacheManager(cluster_mode=False)
            
        return {
            "status": "success",
            "environment": environment,
            "components": components,
            "features": {
                "scalability": environment in ["staging", "production"],
                "high_availability": environment == "production",
                "monitoring": True,
                "deployment_automation": True
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "components": {}
        }
