"""
Metrics Collector Implementation
Comprehensive metrics collection and aggregation system.
"""

import time
import threading
import logging
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import statistics
import json

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    TIMER = "timer"


class AggregationType(Enum):
    """Aggregation types for metrics."""
    SUM = "sum"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    PERCENTILE = "percentile"
    RATE = "rate"


@dataclass
class MetricValue:
    """Individual metric value."""
    value: Union[int, float]
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "value": self.value,
            "timestamp": self.timestamp,
            "labels": self.labels
        }


@dataclass
class MetricDefinition:
    """Metric definition and configuration."""
    name: str
    metric_type: MetricType
    description: str = ""
    unit: str = ""
    labels: List[str] = field(default_factory=list)
    buckets: Optional[List[float]] = None  # For histograms
    quantiles: Optional[List[float]] = None  # For summaries
    retention_period: int = 3600  # seconds
    max_samples: int = 10000


@dataclass
class AggregatedMetric:
    """Aggregated metric result."""
    name: str
    aggregation_type: AggregationType
    value: Union[int, float]
    timestamp: float
    period_start: float
    period_end: float
    sample_count: int
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    Enterprise-grade metrics collection system.
    
    Features:
    - Multiple metric types (counter, gauge, histogram, summary, timer)
    - Label-based dimensional metrics
    - Real-time aggregation and rollups
    - Configurable retention and sampling
    - Export to multiple backends (Prometheus, InfluxDB, etc.)
    - Thread-safe operations
    - Memory-efficient storage
    """
    
    def __init__(self, retention_period: int = 3600, max_metrics: int = 100000):
        """
        Initialize metrics collector.
        
        Args:
            retention_period: Default retention period in seconds
            max_metrics: Maximum number of metrics to store
        """
        self.retention_period = retention_period
        self.max_metrics = max_metrics
        
        # Metric storage
        self.metric_definitions: Dict[str, MetricDefinition] = {}
        self.metric_values: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.metric_aggregations: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Threading
        self.lock = threading.RLock()
        self.cleanup_thread = None
        self.aggregation_thread = None
        self.running = False
        
        # Export backends
        self.export_backends: List[Callable[[List[MetricValue]], None]] = []
        
        # Statistics
        self.total_metrics_recorded = 0
        self.total_exports = 0
        self.start_time = time.time()
        
        logger.info("Metrics collector initialized")
    
    def register_metric(self, definition: MetricDefinition) -> bool:
        """
        Register a new metric definition.
        
        Args:
            definition: Metric definition
            
        Returns:
            True if registered successfully
        """
        try:
            with self.lock:
                if definition.name in self.metric_definitions:
                    logger.warning(f"Metric {definition.name} already registered")
                    return False
                
                self.metric_definitions[definition.name] = definition
                
                # Initialize storage for this metric
                if definition.name not in self.metric_values:
                    self.metric_values[definition.name] = deque(maxlen=definition.max_samples)
                
                logger.info(f"Registered metric: {definition.name} ({definition.metric_type.value})")
                return True
                
        except Exception as e:
            logger.error(f"Failed to register metric {definition.name}: {str(e)}")
            return False
    
    def record_counter(self, name: str, value: Union[int, float] = 1, 
                      labels: Optional[Dict[str, str]] = None) -> bool:
        """
        Record a counter metric.
        
        Args:
            name: Metric name
            value: Counter increment value
            labels: Metric labels
            
        Returns:
            True if recorded successfully
        """
        return self._record_metric(name, value, MetricType.COUNTER, labels)
    
    def record_gauge(self, name: str, value: Union[int, float], 
                    labels: Optional[Dict[str, str]] = None) -> bool:
        """
        Record a gauge metric.
        
        Args:
            name: Metric name
            value: Gauge value
            labels: Metric labels
            
        Returns:
            True if recorded successfully
        """
        return self._record_metric(name, value, MetricType.GAUGE, labels)
    
    def record_histogram(self, name: str, value: Union[int, float], 
                        labels: Optional[Dict[str, str]] = None) -> bool:
        """
        Record a histogram metric.
        
        Args:
            name: Metric name
            value: Observed value
            labels: Metric labels
            
        Returns:
            True if recorded successfully
        """
        return self._record_metric(name, value, MetricType.HISTOGRAM, labels)
    
    def record_timer(self, name: str, duration: float, 
                    labels: Optional[Dict[str, str]] = None) -> bool:
        """
        Record a timer metric.
        
        Args:
            name: Metric name
            duration: Duration in seconds
            labels: Metric labels
            
        Returns:
            True if recorded successfully
        """
        return self._record_metric(name, duration, MetricType.TIMER, labels)
    
    def _record_metric(self, name: str, value: Union[int, float], 
                      metric_type: MetricType, labels: Optional[Dict[str, str]] = None) -> bool:
        """
        Internal method to record a metric.
        
        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            labels: Metric labels
            
        Returns:
            True if recorded successfully
        """
        try:
            with self.lock:
                # Auto-register metric if not exists
                if name not in self.metric_definitions:
                    definition = MetricDefinition(
                        name=name,
                        metric_type=metric_type,
                        description=f"Auto-registered {metric_type.value} metric",
                        retention_period=self.retention_period
                    )
                    self.register_metric(definition)
                
                # Validate metric type
                expected_type = self.metric_definitions[name].metric_type
                if expected_type != metric_type:
                    logger.error(f"Metric type mismatch for {name}: expected {expected_type.value}, got {metric_type.value}")
                    return False
                
                # Create metric value
                metric_value = MetricValue(
                    value=value,
                    timestamp=time.time(),
                    labels=labels or {}
                )
                
                # Store metric value
                self.metric_values[name].append(metric_value)
                self.total_metrics_recorded += 1
                
                # Update real-time aggregations
                self._update_aggregations(name, metric_value)
                
                # Export to backends if configured
                if self.export_backends:
                    self._export_metric(metric_value, name)
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to record metric {name}: {str(e)}")
            return False
    
    def _update_aggregations(self, name: str, metric_value: MetricValue):
        """Update real-time aggregations for a metric."""
        try:
            metric_def = self.metric_definitions[name]
            
            if name not in self.metric_aggregations:
                self.metric_aggregations[name] = {
                    'count': 0,
                    'sum': 0,
                    'min': float('inf'),
                    'max': float('-inf'),
                    'last_value': 0,
                    'rate_window': deque(maxlen=60),  # 1 minute window
                    'histogram_buckets': defaultdict(int) if metric_def.metric_type == MetricType.HISTOGRAM else None
                }
            
            agg = self.metric_aggregations[name]
            value = metric_value.value
            
            # Update basic aggregations
            agg['count'] += 1
            agg['sum'] += value
            agg['min'] = min(agg['min'], value)
            agg['max'] = max(agg['max'], value)
            agg['last_value'] = value
            
            # Update rate calculation window
            agg['rate_window'].append((metric_value.timestamp, value))
            
            # Update histogram buckets
            if metric_def.metric_type == MetricType.HISTOGRAM and metric_def.buckets:
                for bucket in metric_def.buckets:
                    if value <= bucket:
                        agg['histogram_buckets'][bucket] += 1
            
        except Exception as e:
            logger.error(f"Failed to update aggregations for {name}: {str(e)}")
    
    def _export_metric(self, metric_value: MetricValue, name: str):
        """Export metric to configured backends."""
        try:
            for backend in self.export_backends:
                backend([metric_value])
            self.total_exports += 1
        except Exception as e:
            logger.error(f"Failed to export metric {name}: {str(e)}")
    
    def get_metric_value(self, name: str, aggregation: AggregationType = AggregationType.AVERAGE,
                        time_range: Optional[tuple] = None, 
                        labels: Optional[Dict[str, str]] = None) -> Optional[AggregatedMetric]:
        """
        Get aggregated metric value.
        
        Args:
            name: Metric name
            aggregation: Aggregation type
            time_range: (start_time, end_time) tuple
            labels: Label filters
            
        Returns:
            Aggregated metric or None
        """
        try:
            with self.lock:
                if name not in self.metric_values:
                    return None
                
                # Filter values by time range and labels
                values = self._filter_metric_values(name, time_range, labels)
                if not values:
                    return None
                
                # Calculate aggregation
                result_value = self._calculate_aggregation(values, aggregation)
                
                return AggregatedMetric(
                    name=name,
                    aggregation_type=aggregation,
                    value=result_value,
                    timestamp=time.time(),
                    period_start=values[0].timestamp,
                    period_end=values[-1].timestamp,
                    sample_count=len(values),
                    labels=labels or {}
                )
                
        except Exception as e:
            logger.error(f"Failed to get metric value for {name}: {str(e)}")
            return None
    
    def _filter_metric_values(self, name: str, time_range: Optional[tuple], 
                             labels: Optional[Dict[str, str]]) -> List[MetricValue]:
        """Filter metric values by time range and labels."""
        values = list(self.metric_values[name])
        
        # Filter by time range
        if time_range:
            start_time, end_time = time_range
            values = [v for v in values if start_time <= v.timestamp <= end_time]
        
        # Filter by labels
        if labels:
            filtered_values = []
            for value in values:
                match = True
                for key, expected_value in labels.items():
                    if key not in value.labels or value.labels[key] != expected_value:
                        match = False
                        break
                if match:
                    filtered_values.append(value)
            values = filtered_values
        
        return values
    
    def _calculate_aggregation(self, values: List[MetricValue], 
                              aggregation: AggregationType) -> Union[int, float]:
        """Calculate aggregation for metric values."""
        numeric_values = [v.value for v in values]
        
        if aggregation == AggregationType.SUM:
            return sum(numeric_values)
        elif aggregation == AggregationType.AVERAGE:
            return statistics.mean(numeric_values)
        elif aggregation == AggregationType.MIN:
            return min(numeric_values)
        elif aggregation == AggregationType.MAX:
            return max(numeric_values)
        elif aggregation == AggregationType.COUNT:
            return len(numeric_values)
        elif aggregation == AggregationType.PERCENTILE:
            # Default to 95th percentile
            return statistics.quantiles(numeric_values, n=20)[18] if len(numeric_values) > 1 else numeric_values[0]
        elif aggregation == AggregationType.RATE:
            if len(values) < 2:
                return 0.0
            time_diff = values[-1].timestamp - values[0].timestamp
            value_diff = values[-1].value - values[0].value
            return value_diff / max(time_diff, 1.0)
        else:
            return 0.0
    
    def get_all_metrics(self, time_range: Optional[tuple] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get all metrics with their current aggregations.
        
        Args:
            time_range: Optional time range filter
            
        Returns:
            Dictionary of all metrics and their aggregations
        """
        try:
            with self.lock:
                result = {}
                
                for name in self.metric_definitions:
                    if name in self.metric_aggregations:
                        agg = self.metric_aggregations[name]
                        
                        # Calculate derived metrics
                        avg_value = agg['sum'] / max(agg['count'], 1)
                        
                        # Calculate rate (per second)
                        rate = 0.0
                        if len(agg['rate_window']) >= 2:
                            rate_data = list(agg['rate_window'])
                            time_diff = rate_data[-1][0] - rate_data[0][0]
                            value_diff = rate_data[-1][1] - rate_data[0][1]
                            rate = value_diff / max(time_diff, 1.0)
                        
                        result[name] = {
                            'definition': self.metric_definitions[name],
                            'count': agg['count'],
                            'sum': agg['sum'],
                            'average': avg_value,
                            'min': agg['min'] if agg['min'] != float('inf') else 0,
                            'max': agg['max'] if agg['max'] != float('-inf') else 0,
                            'last_value': agg['last_value'],
                            'rate_per_second': rate,
                            'histogram_buckets': dict(agg['histogram_buckets']) if agg['histogram_buckets'] else None
                        }
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to get all metrics: {str(e)}")
            return {}
    
    def get_metric_history(self, name: str, limit: int = 1000) -> List[MetricValue]:
        """
        Get metric history.
        
        Args:
            name: Metric name
            limit: Maximum number of values to return
            
        Returns:
            List of metric values
        """
        with self.lock:
            if name not in self.metric_values:
                return []
            
            values = list(self.metric_values[name])
            return values[-limit:] if limit > 0 else values
    
    def add_export_backend(self, backend: Callable[[List[MetricValue]], None]):
        """
        Add an export backend.
        
        Args:
            backend: Function to export metrics
        """
        self.export_backends.append(backend)
        logger.info("Added metrics export backend")
    
    def start_background_tasks(self):
        """Start background cleanup and aggregation tasks."""
        if self.running:
            return
        
        self.running = True
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name="metrics-cleanup"
        )
        self.cleanup_thread.start()
        
        # Start aggregation thread
        self.aggregation_thread = threading.Thread(
            target=self._aggregation_loop,
            daemon=True,
            name="metrics-aggregation"
        )
        self.aggregation_thread.start()
        
        logger.info("Started metrics background tasks")
    
    def stop_background_tasks(self):
        """Stop background tasks."""
        self.running = False
        
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        
        if self.aggregation_thread:
            self.aggregation_thread.join(timeout=5)
        
        logger.info("Stopped metrics background tasks")
    
    def _cleanup_loop(self):
        """Background cleanup loop."""
        while self.running:
            try:
                self._cleanup_old_metrics()
                time.sleep(300)  # Run every 5 minutes
            except Exception as e:
                logger.error(f"Metrics cleanup error: {str(e)}")
                time.sleep(60)
    
    def _aggregation_loop(self):
        """Background aggregation loop."""
        while self.running:
            try:
                self._perform_periodic_aggregations()
                time.sleep(60)  # Run every minute
            except Exception as e:
                logger.error(f"Metrics aggregation error: {str(e)}")
                time.sleep(30)
    
    def _cleanup_old_metrics(self):
        """Clean up old metric values."""
        try:
            with self.lock:
                current_time = time.time()
                
                for name, definition in self.metric_definitions.items():
                    if name in self.metric_values:
                        values = self.metric_values[name]
                        cutoff_time = current_time - definition.retention_period
                        
                        # Remove old values
                        while values and values[0].timestamp < cutoff_time:
                            values.popleft()
                
        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {str(e)}")
    
    def _perform_periodic_aggregations(self):
        """Perform periodic aggregations for export."""
        try:
            # This could be extended to create periodic rollups
            # for long-term storage and analysis
            pass
        except Exception as e:
            logger.error(f"Failed to perform periodic aggregations: {str(e)}")
    
    def get_collector_stats(self) -> Dict[str, Any]:
        """Get metrics collector statistics."""
        with self.lock:
            uptime = time.time() - self.start_time
            
            return {
                "uptime_seconds": uptime,
                "total_metrics_registered": len(self.metric_definitions),
                "total_metrics_recorded": self.total_metrics_recorded,
                "total_exports": self.total_exports,
                "export_backends_count": len(self.export_backends),
                "memory_usage": {
                    "metric_values_count": sum(len(values) for values in self.metric_values.values()),
                    "aggregations_count": len(self.metric_aggregations)
                },
                "background_tasks_running": self.running
            }
    
    def export_metrics_json(self, file_path: str, time_range: Optional[tuple] = None) -> bool:
        """
        Export metrics to JSON file.
        
        Args:
            file_path: Output file path
            time_range: Optional time range filter
            
        Returns:
            True if exported successfully
        """
        try:
            metrics_data = {
                "timestamp": time.time(),
                "collector_stats": self.get_collector_stats(),
                "metrics": {}
            }
            
            # Export all metrics
            for name in self.metric_definitions:
                history = self.get_metric_history(name)
                if time_range:
                    start_time, end_time = time_range
                    history = [v for v in history if start_time <= v.timestamp <= end_time]
                
                metrics_data["metrics"][name] = {
                    "definition": {
                        "name": self.metric_definitions[name].name,
                        "type": self.metric_definitions[name].metric_type.value,
                        "description": self.metric_definitions[name].description,
                        "unit": self.metric_definitions[name].unit
                    },
                    "values": [v.to_dict() for v in history]
                }
            
            with open(file_path, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            
            logger.info(f"Exported metrics to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export metrics to JSON: {str(e)}")
            return False
    
    def shutdown(self):
        """Gracefully shutdown metrics collector."""
        logger.info("Shutting down metrics collector")
        self.stop_background_tasks()
        
        with self.lock:
            self.metric_definitions.clear()
            self.metric_values.clear()
            self.metric_aggregations.clear()
            self.export_backends.clear()
        
        logger.info("Metrics collector shutdown complete")


# Context manager for timing operations
class MetricTimer:
    """Context manager for timing operations."""
    
    def __init__(self, collector: MetricsCollector, metric_name: str, 
                 labels: Optional[Dict[str, str]] = None):
        """
        Initialize metric timer.
        
        Args:
            collector: Metrics collector instance
            metric_name: Name of the timer metric
            labels: Optional labels
        """
        self.collector = collector
        self.metric_name = metric_name
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and record metric."""
        if self.start_time:
            duration = time.time() - self.start_time
            self.collector.record_timer(self.metric_name, duration, self.labels)


# Decorator for timing function calls
def timed_metric(collector: MetricsCollector, metric_name: Optional[str] = None, 
                labels: Optional[Dict[str, str]] = None):
    """
    Decorator to time function calls.
    
    Args:
        collector: Metrics collector instance
        metric_name: Optional metric name (defaults to function name)
        labels: Optional labels
        
    Returns:
        Decorated function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            name = metric_name or f"{func.__module__}.{func.__name__}_duration"
            with MetricTimer(collector, name, labels):
                return func(*args, **kwargs)
        return wrapper
    return decorator
