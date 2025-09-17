"""
DataLineagePy Monitoring Infrastructure
Comprehensive monitoring, alerting, and observability components.
"""

from .metrics_collector import (
    MetricsCollector,
    MetricType,
    AggregationType,
    MetricValue,
    MetricHistory
)
from .alert_manager import (
    AlertManager,
    AlertRule,
    AlertCondition,
    AlertSeverity,
    AlertChannel,
    Alert,
    AlertStatus
)
from .log_aggregator import (
    LogAggregator,
    LogEntry,
    LogFilter,
    LogLevel,
    LogSource,
    LogAggregation,
    LogHandler
)
from .dashboard import (
    MonitoringDashboard,
    DashboardConfig
)
from .exporters import (
    ExporterManager,
    PrometheusExporter,
    PrometheusConfig,
    InfluxDBExporter,
    InfluxDBConfig,
    ElasticsearchExporter,
    ElasticsearchConfig,
    WebhookExporter,
    WebhookConfig
)
from .integration import (
    MonitoringIntegration,
    get_monitoring,
    setup_monitoring
)

# Version and metadata
__version__ = "1.0.0"
__author__ = "DataLineagePy Enterprise Team"

# Supported features
SUPPORTED_METRIC_TYPES = [
    MetricType.COUNTER,
    MetricType.GAUGE,
    MetricType.HISTOGRAM,
    MetricType.SUMMARY,
    MetricType.TIMER
]

SUPPORTED_AGGREGATIONS = [
    AggregationType.SUM,
    AggregationType.AVERAGE,
    AggregationType.MIN,
    AggregationType.MAX,
    AggregationType.COUNT,
    AggregationType.PERCENTILE,
    AggregationType.RATE
]

SUPPORTED_ALERT_CHANNELS = [
    AlertChannel.EMAIL,
    AlertChannel.SLACK,
    AlertChannel.WEBHOOK,
    AlertChannel.SMS,
    AlertChannel.PAGERDUTY,
    AlertChannel.CUSTOM
]

SUPPORTED_LOG_SOURCES = [
    LogSource.APPLICATION,
    LogSource.SYSTEM,
    LogSource.SECURITY,
    LogSource.AUDIT,
    LogSource.PERFORMANCE,
    LogSource.CUSTOM
]

# Default configurations
DEFAULT_METRICS_CONFIG = {
    "retention_period": 3600,  # 1 hour
    "max_metrics": 100000,
    "cleanup_interval": 300,   # 5 minutes
    "aggregation_interval": 60  # 1 minute
}

DEFAULT_ALERT_CONFIG = {
    "evaluation_interval": 60,    # 1 minute
    "min_duration": 120,          # 2 minutes
    "max_frequency": 3600,        # 1 hour
    "resolve_timeout": 300        # 5 minutes
}

DEFAULT_LOG_CONFIG = {
    "max_entries": 1000000,       # 1M entries
    "retention_days": 30,         # 30 days
    "processing_queue_size": 10000,
    "cleanup_interval": 3600      # 1 hour
}

# Export all components
__all__ = [
    # Core classes
    "MetricsCollector",
    "AlertManager", 
    "LogAggregator",
    
    # Metrics components
    "MetricType",
    "AggregationType",
    "MetricDefinition",
    "MetricValue",
    "AggregatedMetric",
    "MetricTimer",
    "timed_metric",
    
    # Alert components
    "AlertRule",
    "Alert",
    "AlertSeverity",
    "AlertStatus",
    "NotificationChannel",
    "NotificationConfig",
    
    # Log components
    "LogEntry",
    "LogFilter",
    "LogAggregation",
    "LogLevel",
    "LogSource",
    "LogHandler",
    
    # Metadata
    "SUPPORTED_METRIC_TYPES",
    "SUPPORTED_AGGREGATIONS",
    "SUPPORTED_ALERT_CHANNELS",
    "SUPPORTED_LOG_SOURCES",
    "DEFAULT_METRICS_CONFIG",
    "DEFAULT_ALERT_CONFIG",
    "DEFAULT_LOG_CONFIG"
]


def create_monitoring_stack(metrics_config: dict = None, 
                          alert_config: dict = None,
                          log_config: dict = None) -> tuple:
    """
    Create a complete monitoring stack with integrated components.
    
    Args:
        metrics_config: Metrics collector configuration
        alert_config: Alert manager configuration  
        log_config: Log aggregator configuration
        
    Returns:
        Tuple of (metrics_collector, alert_manager, log_aggregator)
    """
    # Apply default configurations
    metrics_config = {**DEFAULT_METRICS_CONFIG, **(metrics_config or {})}
    alert_config = {**DEFAULT_ALERT_CONFIG, **(alert_config or {})}
    log_config = {**DEFAULT_LOG_CONFIG, **(log_config or {})}
    
    # Create components
    metrics_collector = MetricsCollector(
        retention_period=metrics_config["retention_period"],
        max_metrics=metrics_config["max_metrics"]
    )
    
    alert_manager = AlertManager(metrics_collector=metrics_collector)
    
    log_aggregator = LogAggregator(
        max_entries=log_config["max_entries"],
        retention_days=log_config["retention_days"]
    )
    
    # Start background tasks
    metrics_collector.start_background_tasks()
    alert_manager.start_monitoring()
    log_aggregator.start_processing()
    
    return metrics_collector, alert_manager, log_aggregator


def create_enterprise_monitoring_config() -> dict:
    """
    Create enterprise-grade monitoring configuration.
    
    Returns:
        Dictionary with enterprise monitoring settings
    """
    return {
        "metrics": {
            "retention_period": 86400,     # 24 hours
            "max_metrics": 1000000,        # 1M metrics
            "cleanup_interval": 300,       # 5 minutes
            "aggregation_interval": 60,    # 1 minute
            "export_interval": 300         # 5 minutes
        },
        "alerts": {
            "evaluation_interval": 30,     # 30 seconds
            "min_duration": 60,            # 1 minute
            "max_frequency": 1800,         # 30 minutes
            "resolve_timeout": 600,        # 10 minutes
            "escalation_timeout": 3600     # 1 hour
        },
        "logs": {
            "max_entries": 10000000,       # 10M entries
            "retention_days": 90,          # 90 days
            "processing_queue_size": 50000,
            "cleanup_interval": 1800,      # 30 minutes
            "export_interval": 3600        # 1 hour
        },
        "performance": {
            "enable_profiling": True,
            "profile_interval": 300,       # 5 minutes
            "memory_threshold": 0.8,       # 80% memory usage
            "cpu_threshold": 0.9,          # 90% CPU usage
            "disk_threshold": 0.85         # 85% disk usage
        }
    }
