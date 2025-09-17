"""
Monitoring Integration Module
Integrates monitoring with existing DataLineagePy components.
"""

import time
import logging
import threading
from typing import Dict, List, Optional, Any, Callable
from contextlib import contextmanager
from functools import wraps

from .metrics_collector import MetricsCollector, MetricType
from .alert_manager import AlertManager, AlertRule, AlertSeverity, AlertCondition
from .log_aggregator import LogAggregator, LogLevel, LogSource
from .dashboard import MonitoringDashboard, DashboardConfig
from .exporters import ExporterManager, PrometheusExporter, InfluxDBExporter, ElasticsearchExporter

logger = logging.getLogger(__name__)


class MonitoringIntegration:
    """
    Central monitoring integration for DataLineagePy.
    
    Provides seamless integration of monitoring capabilities with
    existing DataLineagePy components and workflows.
    """
    
    def __init__(self, 
                 metrics_collector: MetricsCollector = None,
                 alert_manager: AlertManager = None,
                 log_aggregator: LogAggregator = None,
                 dashboard: MonitoringDashboard = None,
                 exporter_manager: ExporterManager = None):
        """
        Initialize monitoring integration.
        
        Args:
            metrics_collector: Metrics collector instance
            alert_manager: Alert manager instance
            log_aggregator: Log aggregator instance
            dashboard: Monitoring dashboard instance
            exporter_manager: Exporter manager instance
        """
        self.metrics_collector = metrics_collector or MetricsCollector()
        self.alert_manager = alert_manager or AlertManager()
        self.log_aggregator = log_aggregator or LogAggregator()
        self.dashboard = dashboard
        self.exporter_manager = exporter_manager or ExporterManager()
        
        # Integration state
        self.running = False
        self.integrated_components = set()
        
        # Setup default monitoring
        self._setup_default_monitoring()
        
        logger.info("Monitoring integration initialized")
    
    def _setup_default_monitoring(self):
        """Setup default monitoring rules and metrics."""
        
        # Default metrics
        default_metrics = [
            "datalineage.operations.total",
            "datalineage.operations.rate",
            "datalineage.operations.duration",
            "datalineage.errors.total",
            "datalineage.memory.usage",
            "datalineage.cpu.usage",
            "system.health.score"
        ]
        
        for metric_name in default_metrics:
            self.metrics_collector.create_metric(metric_name, MetricType.COUNTER)
        
        # Default alert rules
        default_alerts = [
            AlertRule(
                name="high_error_rate",
                condition=AlertCondition.GREATER_THAN,
                threshold=10.0,
                metric_name="datalineage.errors.total",
                severity=AlertSeverity.HIGH,
                description="High error rate detected"
            ),
            AlertRule(
                name="high_memory_usage",
                condition=AlertCondition.GREATER_THAN,
                threshold=80.0,
                metric_name="datalineage.memory.usage",
                severity=AlertSeverity.MEDIUM,
                description="High memory usage detected"
            ),
            AlertRule(
                name="low_system_health",
                condition=AlertCondition.LESS_THAN,
                threshold=50.0,
                metric_name="system.health.score",
                severity=AlertSeverity.CRITICAL,
                description="System health score is low"
            )
        ]
        
        for rule in default_alerts:
            self.alert_manager.add_rule(rule)
    
    def start(self):
        """Start monitoring integration."""
        if self.running:
            logger.warning("Monitoring integration already running")
            return
        
        self.running = True
        
        # Start components
        self.metrics_collector.start_background_tasks()
        self.alert_manager.start_evaluation()
        self.log_aggregator.start_processing()
        
        if self.dashboard:
            self.dashboard.start()
        
        self.exporter_manager.start_all()
        
        logger.info("Monitoring integration started")
    
    def stop(self):
        """Stop monitoring integration."""
        if not self.running:
            return
        
        self.running = False
        
        # Stop components
        self.metrics_collector.stop_background_tasks()
        self.alert_manager.stop_evaluation()
        self.log_aggregator.stop_processing()
        
        if self.dashboard:
            self.dashboard.stop()
        
        self.exporter_manager.stop_all()
        
        logger.info("Monitoring integration stopped")
    
    def integrate_with_tracker(self, tracker):
        """
        Integrate monitoring with DataLineage tracker.
        
        Args:
            tracker: DataLineage tracker instance
        """
        if 'tracker' in self.integrated_components:
            return
        
        # Wrap tracker methods with monitoring
        original_track = tracker.track
        
        @wraps(original_track)
        def monitored_track(*args, **kwargs):
            start_time = time.time()
            
            try:
                # Increment operation counter
                self.metrics_collector.increment("datalineage.operations.total")
                
                # Execute original method
                result = original_track(*args, **kwargs)
                
                # Record success metrics
                duration = time.time() - start_time
                self.metrics_collector.record_timer("datalineage.operations.duration", duration)
                self.metrics_collector.increment("datalineage.operations.rate")
                
                # Log operation
                self.log_aggregator.add_log(
                    level=LogLevel.INFO,
                    message=f"Tracked lineage operation in {duration:.3f}s",
                    logger_name="datalineage.tracker",
                    source=LogSource.APPLICATION
                )
                
                return result
                
            except Exception as e:
                # Record error metrics
                self.metrics_collector.increment("datalineage.errors.total")
                
                # Log error
                self.log_aggregator.add_log(
                    level=LogLevel.ERROR,
                    message=f"Lineage tracking failed: {str(e)}",
                    logger_name="datalineage.tracker",
                    source=LogSource.APPLICATION,
                    extra_data={"error_type": type(e).__name__}
                )
                
                raise
        
        # Replace method
        tracker.track = monitored_track
        self.integrated_components.add('tracker')
        
        logger.info("Integrated monitoring with DataLineage tracker")
    
    def integrate_with_scalability(self, load_balancer=None, horizontal_scaler=None):
        """
        Integrate monitoring with scalability components.
        
        Args:
            load_balancer: Load balancer instance
            horizontal_scaler: Horizontal scaler instance
        """
        if 'scalability' in self.integrated_components:
            return
        
        # Monitor load balancer
        if load_balancer:
            self._monitor_load_balancer(load_balancer)
        
        # Monitor horizontal scaler
        if horizontal_scaler:
            self._monitor_horizontal_scaler(horizontal_scaler)
        
        self.integrated_components.add('scalability')
        logger.info("Integrated monitoring with scalability components")
    
    def _monitor_load_balancer(self, load_balancer):
        """Monitor load balancer metrics."""
        
        # Create metrics for load balancer
        self.metrics_collector.create_metric("loadbalancer.requests.total", MetricType.COUNTER)
        self.metrics_collector.create_metric("loadbalancer.response_time", MetricType.HISTOGRAM)
        self.metrics_collector.create_metric("loadbalancer.active_connections", MetricType.GAUGE)
        self.metrics_collector.create_metric("loadbalancer.backend_health", MetricType.GAUGE)
        
        # Wrap load balancer methods
        original_get_next_server = load_balancer.get_next_server
        
        @wraps(original_get_next_server)
        def monitored_get_next_server(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = original_get_next_server(*args, **kwargs)
                
                # Record metrics
                self.metrics_collector.increment("loadbalancer.requests.total")
                response_time = time.time() - start_time
                self.metrics_collector.record_histogram("loadbalancer.response_time", response_time)
                
                # Update connection count
                stats = load_balancer.get_stats()
                self.metrics_collector.set_gauge("loadbalancer.active_connections", stats.get("total_connections", 0))
                
                return result
                
            except Exception as e:
                self.log_aggregator.add_log(
                    level=LogLevel.ERROR,
                    message=f"Load balancer error: {str(e)}",
                    logger_name="scalability.loadbalancer",
                    source=LogSource.INFRASTRUCTURE
                )
                raise
        
        load_balancer.get_next_server = monitored_get_next_server
    
    def _monitor_horizontal_scaler(self, horizontal_scaler):
        """Monitor horizontal scaler metrics."""
        
        # Create metrics for horizontal scaler
        self.metrics_collector.create_metric("scaler.instances.current", MetricType.GAUGE)
        self.metrics_collector.create_metric("scaler.scaling_events.total", MetricType.COUNTER)
        self.metrics_collector.create_metric("scaler.cpu_utilization", MetricType.GAUGE)
        self.metrics_collector.create_metric("scaler.memory_utilization", MetricType.GAUGE)
        
        # Monitor scaling events
        def on_scale_up(instance_count):
            self.metrics_collector.increment("scaler.scaling_events.total", labels={"direction": "up"})
            self.metrics_collector.set_gauge("scaler.instances.current", instance_count)
            
            self.log_aggregator.add_log(
                level=LogLevel.INFO,
                message=f"Scaled up to {instance_count} instances",
                logger_name="scalability.scaler",
                source=LogSource.INFRASTRUCTURE
            )
        
        def on_scale_down(instance_count):
            self.metrics_collector.increment("scaler.scaling_events.total", labels={"direction": "down"})
            self.metrics_collector.set_gauge("scaler.instances.current", instance_count)
            
            self.log_aggregator.add_log(
                level=LogLevel.INFO,
                message=f"Scaled down to {instance_count} instances",
                logger_name="scalability.scaler",
                source=LogSource.INFRASTRUCTURE
            )
        
        # Register callbacks if scaler supports them
        if hasattr(horizontal_scaler, 'add_scale_callback'):
            horizontal_scaler.add_scale_callback('up', on_scale_up)
            horizontal_scaler.add_scale_callback('down', on_scale_down)
    
    def integrate_with_high_availability(self, health_checker=None, circuit_breaker=None):
        """
        Integrate monitoring with high availability components.
        
        Args:
            health_checker: Health checker instance
            circuit_breaker: Circuit breaker instance
        """
        if 'high_availability' in self.integrated_components:
            return
        
        # Monitor health checker
        if health_checker:
            self._monitor_health_checker(health_checker)
        
        # Monitor circuit breaker
        if circuit_breaker:
            self._monitor_circuit_breaker(circuit_breaker)
        
        self.integrated_components.add('high_availability')
        logger.info("Integrated monitoring with high availability components")
    
    def _monitor_health_checker(self, health_checker):
        """Monitor health checker metrics."""
        
        # Create metrics
        self.metrics_collector.create_metric("healthcheck.services.healthy", MetricType.GAUGE)
        self.metrics_collector.create_metric("healthcheck.services.unhealthy", MetricType.GAUGE)
        self.metrics_collector.create_metric("healthcheck.checks.total", MetricType.COUNTER)
        self.metrics_collector.create_metric("healthcheck.uptime.percentage", MetricType.GAUGE)
        
        # Monitor health status changes
        def on_health_change(service_id, is_healthy, check_result):
            self.metrics_collector.increment("healthcheck.checks.total")
            
            if is_healthy:
                self.log_aggregator.add_log(
                    level=LogLevel.INFO,
                    message=f"Service {service_id} is healthy",
                    logger_name="ha.healthcheck",
                    source=LogSource.INFRASTRUCTURE
                )
            else:
                self.log_aggregator.add_log(
                    level=LogLevel.WARNING,
                    message=f"Service {service_id} is unhealthy: {check_result.get('error', 'Unknown error')}",
                    logger_name="ha.healthcheck",
                    source=LogSource.INFRASTRUCTURE
                )
        
        # Register callback if supported
        if hasattr(health_checker, 'add_status_callback'):
            health_checker.add_status_callback(on_health_change)
    
    def _monitor_circuit_breaker(self, circuit_breaker):
        """Monitor circuit breaker metrics."""
        
        # Create metrics
        self.metrics_collector.create_metric("circuitbreaker.state", MetricType.GAUGE)
        self.metrics_collector.create_metric("circuitbreaker.failures.total", MetricType.COUNTER)
        self.metrics_collector.create_metric("circuitbreaker.successes.total", MetricType.COUNTER)
        self.metrics_collector.create_metric("circuitbreaker.timeouts.total", MetricType.COUNTER)
        
        # Monitor state changes
        original_call = circuit_breaker.call
        
        @wraps(original_call)
        def monitored_call(*args, **kwargs):
            try:
                result = original_call(*args, **kwargs)
                self.metrics_collector.increment("circuitbreaker.successes.total")
                return result
            except Exception as e:
                self.metrics_collector.increment("circuitbreaker.failures.total")
                
                self.log_aggregator.add_log(
                    level=LogLevel.WARNING,
                    message=f"Circuit breaker failure: {str(e)}",
                    logger_name="ha.circuitbreaker",
                    source=LogSource.INFRASTRUCTURE
                )
                raise
        
        circuit_breaker.call = monitored_call
    
    @contextmanager
    def monitor_operation(self, operation_name: str, labels: Dict[str, str] = None):
        """
        Context manager for monitoring operations.
        
        Args:
            operation_name: Name of the operation
            labels: Additional labels for metrics
        """
        start_time = time.time()
        labels = labels or {}
        
        # Start operation
        self.metrics_collector.increment(f"{operation_name}.started", labels=labels)
        
        try:
            yield
            
            # Success
            duration = time.time() - start_time
            self.metrics_collector.record_timer(f"{operation_name}.duration", duration, labels=labels)
            self.metrics_collector.increment(f"{operation_name}.completed", labels=labels)
            
            self.log_aggregator.add_log(
                level=LogLevel.INFO,
                message=f"Operation {operation_name} completed in {duration:.3f}s",
                logger_name="monitoring.operations",
                source=LogSource.APPLICATION,
                extra_data={"operation": operation_name, "duration": duration, **labels}
            )
            
        except Exception as e:
            # Failure
            duration = time.time() - start_time
            self.metrics_collector.increment(f"{operation_name}.failed", labels=labels)
            
            self.log_aggregator.add_log(
                level=LogLevel.ERROR,
                message=f"Operation {operation_name} failed after {duration:.3f}s: {str(e)}",
                logger_name="monitoring.operations",
                source=LogSource.APPLICATION,
                extra_data={"operation": operation_name, "duration": duration, "error": str(e), **labels}
            )
            
            raise
    
    def monitor_function(self, func_name: str = None, labels: Dict[str, str] = None):
        """
        Decorator for monitoring functions.
        
        Args:
            func_name: Custom function name (defaults to actual function name)
            labels: Additional labels for metrics
        """
        def decorator(func):
            name = func_name or func.__name__
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.monitor_operation(f"function.{name}", labels):
                    return func(*args, **kwargs)
            
            return wrapper
        
        return decorator
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get overall monitoring status."""
        return {
            "running": self.running,
            "integrated_components": list(self.integrated_components),
            "metrics_collector": {
                "running": self.metrics_collector.running,
                "stats": self.metrics_collector.get_collector_stats()
            },
            "alert_manager": {
                "running": self.alert_manager.running,
                "active_alerts": len(self.alert_manager.get_active_alerts()),
                "stats": self.alert_manager.get_alert_stats()
            },
            "log_aggregator": {
                "running": self.log_aggregator.running,
                "stats": self.log_aggregator.get_log_stats()
            },
            "dashboard": {
                "running": self.dashboard.running if self.dashboard else False,
                "url": self.dashboard.get_dashboard_url() if self.dashboard else None
            },
            "exporters": self.exporter_manager.get_stats()
        }


# Global monitoring instance
_global_monitoring = None


def get_monitoring() -> MonitoringIntegration:
    """Get global monitoring instance."""
    global _global_monitoring
    
    if _global_monitoring is None:
        _global_monitoring = MonitoringIntegration()
    
    return _global_monitoring


def setup_monitoring(config: Dict[str, Any] = None) -> MonitoringIntegration:
    """
    Setup and configure monitoring integration.
    
    Args:
        config: Monitoring configuration
        
    Returns:
        Configured monitoring integration instance
    """
    global _global_monitoring
    
    config = config or {}
    
    # Create components
    metrics_collector = MetricsCollector()
    alert_manager = AlertManager()
    log_aggregator = LogAggregator()
    
    # Create dashboard if enabled
    dashboard = None
    if config.get('dashboard', {}).get('enabled', True):
        dashboard_config = DashboardConfig(**config.get('dashboard', {}))
        dashboard = MonitoringDashboard(
            metrics_collector=metrics_collector,
            alert_manager=alert_manager,
            log_aggregator=log_aggregator,
            config=dashboard_config
        )
    
    # Create exporter manager
    exporter_manager = ExporterManager()
    
    # Add exporters based on configuration
    exporters_config = config.get('exporters', {})
    
    if exporters_config.get('prometheus', {}).get('enabled', False):
        from .exporters import PrometheusConfig
        prometheus_config = PrometheusConfig(**exporters_config['prometheus'])
        prometheus_exporter = PrometheusExporter(prometheus_config, metrics_collector)
        exporter_manager.add_exporter(prometheus_exporter)
    
    if exporters_config.get('influxdb', {}).get('enabled', False):
        from .exporters import InfluxDBConfig
        influxdb_config = InfluxDBConfig(**exporters_config['influxdb'])
        influxdb_exporter = InfluxDBExporter(influxdb_config, metrics_collector)
        exporter_manager.add_exporter(influxdb_exporter)
    
    if exporters_config.get('elasticsearch', {}).get('enabled', False):
        from .exporters import ElasticsearchConfig
        elasticsearch_config = ElasticsearchConfig(**exporters_config['elasticsearch'])
        elasticsearch_exporter = ElasticsearchExporter(elasticsearch_config, log_aggregator)
        exporter_manager.add_exporter(elasticsearch_exporter)
    
    # Create monitoring integration
    _global_monitoring = MonitoringIntegration(
        metrics_collector=metrics_collector,
        alert_manager=alert_manager,
        log_aggregator=log_aggregator,
        dashboard=dashboard,
        exporter_manager=exporter_manager
    )
    
    return _global_monitoring
