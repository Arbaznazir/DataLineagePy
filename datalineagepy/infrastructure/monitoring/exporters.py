"""
Monitoring Data Exporters
Export monitoring data to external systems (Prometheus, InfluxDB, ELK, etc.).
"""

import time
import threading
import logging
import json
import requests
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

from .metrics_collector import MetricValue, MetricsCollector
from .log_aggregator import LogEntry, LogAggregator
from .alert_manager import Alert, AlertManager

logger = logging.getLogger(__name__)


@dataclass
class ExporterConfig:
    """Base exporter configuration."""
    enabled: bool = True
    export_interval: int = 60  # seconds
    batch_size: int = 1000
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 5


class BaseExporter(ABC):
    """Base class for monitoring data exporters."""
    
    def __init__(self, config: ExporterConfig):
        """
        Initialize exporter.
        
        Args:
            config: Exporter configuration
        """
        self.config = config
        self.running = False
        self.export_thread = None
        self.lock = threading.Lock()
        
        # Statistics
        self.total_exports = 0
        self.failed_exports = 0
        self.last_export_time = None
        
    @abstractmethod
    def export_data(self, data: List[Any]) -> bool:
        """
        Export data to external system.
        
        Args:
            data: Data to export
            
        Returns:
            True if export was successful
        """
        pass
    
    def start_export(self):
        """Start background export process."""
        if self.running or not self.config.enabled:
            return
        
        self.running = True
        self.export_thread = threading.Thread(
            target=self._export_loop,
            daemon=True,
            name=f"{self.__class__.__name__}-export"
        )
        self.export_thread.start()
        
        logger.info(f"Started {self.__class__.__name__} exporter")
    
    def stop_export(self):
        """Stop background export process."""
        self.running = False
        
        if self.export_thread:
            self.export_thread.join(timeout=10)
        
        logger.info(f"Stopped {self.__class__.__name__} exporter")
    
    def _export_loop(self):
        """Background export loop."""
        while self.running:
            try:
                self._perform_export()
                time.sleep(self.config.export_interval)
            except Exception as e:
                logger.error(f"Export loop error in {self.__class__.__name__}: {str(e)}")
                time.sleep(self.config.retry_delay)
    
    @abstractmethod
    def _perform_export(self):
        """Perform the actual export operation."""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get exporter statistics."""
        return {
            "total_exports": self.total_exports,
            "failed_exports": self.failed_exports,
            "last_export_time": self.last_export_time,
            "running": self.running,
            "enabled": self.config.enabled
        }


@dataclass
class PrometheusConfig(ExporterConfig):
    """Prometheus exporter configuration."""
    pushgateway_url: str = "http://localhost:9091"
    job_name: str = "datalineagepy"
    instance: str = "localhost"
    basic_auth: Optional[tuple] = None  # (username, password)
    headers: Dict[str, str] = None


class PrometheusExporter(BaseExporter):
    """
    Prometheus metrics exporter.
    
    Exports metrics to Prometheus Pushgateway in Prometheus format.
    """
    
    def __init__(self, config: PrometheusConfig, metrics_collector: MetricsCollector):
        """
        Initialize Prometheus exporter.
        
        Args:
            config: Prometheus configuration
            metrics_collector: Metrics collector instance
        """
        super().__init__(config)
        self.prometheus_config = config
        self.metrics_collector = metrics_collector
        
    def export_data(self, data: List[MetricValue]) -> bool:
        """Export metrics to Prometheus."""
        try:
            # Convert metrics to Prometheus format
            prometheus_data = self._convert_to_prometheus_format(data)
            
            # Send to Pushgateway
            url = f"{self.prometheus_config.pushgateway_url}/metrics/job/{self.prometheus_config.job_name}/instance/{self.prometheus_config.instance}"
            
            headers = {"Content-Type": "text/plain"}
            if self.prometheus_config.headers:
                headers.update(self.prometheus_config.headers)
            
            auth = self.prometheus_config.basic_auth
            
            response = requests.post(
                url,
                data=prometheus_data,
                headers=headers,
                auth=auth,
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            
            with self.lock:
                self.total_exports += 1
                self.last_export_time = time.time()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to export to Prometheus: {str(e)}")
            with self.lock:
                self.failed_exports += 1
            return False
    
    def _convert_to_prometheus_format(self, data: List[MetricValue]) -> str:
        """Convert metrics to Prometheus format."""
        lines = []
        
        # Group metrics by name
        metrics_by_name = {}
        for metric in data:
            name = metric.labels.get('__name__', 'unknown_metric')
            if name not in metrics_by_name:
                metrics_by_name[name] = []
            metrics_by_name[name].append(metric)
        
        # Convert each metric
        for metric_name, metric_values in metrics_by_name.items():
            # Add help and type comments
            lines.append(f"# HELP {metric_name} DataLineagePy metric")
            lines.append(f"# TYPE {metric_name} gauge")
            
            # Add metric values
            for metric in metric_values:
                labels_str = ""
                if metric.labels:
                    label_pairs = [f'{k}="{v}"' for k, v in metric.labels.items() if k != '__name__']
                    if label_pairs:
                        labels_str = "{" + ",".join(label_pairs) + "}"
                
                lines.append(f"{metric_name}{labels_str} {metric.value} {int(metric.timestamp * 1000)}")
        
        return "\n".join(lines) + "\n"
    
    def _perform_export(self):
        """Perform Prometheus export."""
        if not self.metrics_collector:
            return
        
        # Get all metrics
        all_metrics = self.metrics_collector.get_all_metrics()
        
        # Convert to metric values for export
        metric_values = []
        for name, data in all_metrics.items():
            metric_values.append(MetricValue(
                value=data.get("last_value", 0),
                timestamp=time.time(),
                labels={"__name__": name, "job": self.prometheus_config.job_name}
            ))
        
        if metric_values:
            self.export_data(metric_values)


@dataclass
class InfluxDBConfig(ExporterConfig):
    """InfluxDB exporter configuration."""
    url: str = "http://localhost:8086"
    database: str = "datalineagepy"
    username: Optional[str] = None
    password: Optional[str] = None
    retention_policy: str = "autogen"
    precision: str = "s"  # s, ms, u, ns


class InfluxDBExporter(BaseExporter):
    """
    InfluxDB metrics exporter.
    
    Exports metrics to InfluxDB in line protocol format.
    """
    
    def __init__(self, config: InfluxDBConfig, metrics_collector: MetricsCollector):
        """
        Initialize InfluxDB exporter.
        
        Args:
            config: InfluxDB configuration
            metrics_collector: Metrics collector instance
        """
        super().__init__(config)
        self.influxdb_config = config
        self.metrics_collector = metrics_collector
        
    def export_data(self, data: List[MetricValue]) -> bool:
        """Export metrics to InfluxDB."""
        try:
            # Convert to InfluxDB line protocol
            line_protocol = self._convert_to_line_protocol(data)
            
            # Send to InfluxDB
            url = f"{self.influxdb_config.url}/write"
            params = {
                "db": self.influxdb_config.database,
                "rp": self.influxdb_config.retention_policy,
                "precision": self.influxdb_config.precision
            }
            
            auth = None
            if self.influxdb_config.username and self.influxdb_config.password:
                auth = (self.influxdb_config.username, self.influxdb_config.password)
            
            response = requests.post(
                url,
                params=params,
                data=line_protocol,
                auth=auth,
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            
            with self.lock:
                self.total_exports += 1
                self.last_export_time = time.time()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to export to InfluxDB: {str(e)}")
            with self.lock:
                self.failed_exports += 1
            return False
    
    def _convert_to_line_protocol(self, data: List[MetricValue]) -> str:
        """Convert metrics to InfluxDB line protocol."""
        lines = []
        
        for metric in data:
            measurement = metric.labels.get('__name__', 'metric')
            
            # Build tags
            tags = []
            fields = []
            
            for key, value in metric.labels.items():
                if key != '__name__':
                    tags.append(f"{key}={value}")
            
            # Add value as field
            fields.append(f"value={metric.value}")
            
            # Build line
            tags_str = "," + ",".join(tags) if tags else ""
            fields_str = ",".join(fields)
            timestamp = int(metric.timestamp)
            
            line = f"{measurement}{tags_str} {fields_str} {timestamp}"
            lines.append(line)
        
        return "\n".join(lines)
    
    def _perform_export(self):
        """Perform InfluxDB export."""
        if not self.metrics_collector:
            return
        
        # Get all metrics
        all_metrics = self.metrics_collector.get_all_metrics()
        
        # Convert to metric values for export
        metric_values = []
        for name, data in all_metrics.items():
            metric_values.append(MetricValue(
                value=data.get("last_value", 0),
                timestamp=time.time(),
                labels={"__name__": name}
            ))
        
        if metric_values:
            self.export_data(metric_values)


@dataclass
class ElasticsearchConfig(ExporterConfig):
    """Elasticsearch exporter configuration."""
    url: str = "http://localhost:9200"
    index_prefix: str = "datalineagepy"
    username: Optional[str] = None
    password: Optional[str] = None
    verify_ssl: bool = True


class ElasticsearchExporter(BaseExporter):
    """
    Elasticsearch logs exporter.
    
    Exports logs to Elasticsearch for analysis and visualization.
    """
    
    def __init__(self, config: ElasticsearchConfig, log_aggregator: LogAggregator):
        """
        Initialize Elasticsearch exporter.
        
        Args:
            config: Elasticsearch configuration
            log_aggregator: Log aggregator instance
        """
        super().__init__(config)
        self.elasticsearch_config = config
        self.log_aggregator = log_aggregator
        self.last_export_timestamp = time.time()
        
    def export_data(self, data: List[LogEntry]) -> bool:
        """Export logs to Elasticsearch."""
        try:
            if not data:
                return True
            
            # Prepare bulk request
            bulk_data = []
            
            for log_entry in data:
                # Create index name with date
                date_str = time.strftime("%Y.%m.%d", time.localtime(log_entry.timestamp))
                index_name = f"{self.elasticsearch_config.index_prefix}-{date_str}"
                
                # Index action
                action = {
                    "index": {
                        "_index": index_name,
                        "_type": "_doc"
                    }
                }
                
                # Document data
                doc = log_entry.to_dict()
                doc["@timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.localtime(log_entry.timestamp))
                
                bulk_data.append(json.dumps(action))
                bulk_data.append(json.dumps(doc))
            
            # Send bulk request
            bulk_body = "\n".join(bulk_data) + "\n"
            
            url = f"{self.elasticsearch_config.url}/_bulk"
            headers = {"Content-Type": "application/x-ndjson"}
            
            auth = None
            if self.elasticsearch_config.username and self.elasticsearch_config.password:
                auth = (self.elasticsearch_config.username, self.elasticsearch_config.password)
            
            response = requests.post(
                url,
                data=bulk_body,
                headers=headers,
                auth=auth,
                timeout=self.config.timeout,
                verify=self.elasticsearch_config.verify_ssl
            )
            
            response.raise_for_status()
            
            # Check for errors in response
            result = response.json()
            if result.get("errors"):
                logger.warning("Some documents failed to index in Elasticsearch")
            
            with self.lock:
                self.total_exports += 1
                self.last_export_time = time.time()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to export to Elasticsearch: {str(e)}")
            with self.lock:
                self.failed_exports += 1
            return False
    
    def _perform_export(self):
        """Perform Elasticsearch export."""
        if not self.log_aggregator:
            return
        
        # Get logs since last export
        current_time = time.time()
        
        from .log_aggregator import LogFilter
        log_filter = LogFilter(
            time_range=(self.last_export_timestamp, current_time)
        )
        
        logs = self.log_aggregator.search_logs(log_filter, limit=self.config.batch_size)
        
        if logs:
            success = self.export_data(logs)
            if success:
                self.last_export_timestamp = current_time


@dataclass
class WebhookConfig(ExporterConfig):
    """Webhook exporter configuration."""
    url: str
    method: str = "POST"
    headers: Dict[str, str] = None
    auth_token: Optional[str] = None
    verify_ssl: bool = True


class WebhookExporter(BaseExporter):
    """
    Generic webhook exporter.
    
    Exports monitoring data to custom webhook endpoints.
    """
    
    def __init__(self, config: WebhookConfig, data_source: Union[MetricsCollector, LogAggregator, AlertManager]):
        """
        Initialize webhook exporter.
        
        Args:
            config: Webhook configuration
            data_source: Data source (metrics, logs, or alerts)
        """
        super().__init__(config)
        self.webhook_config = config
        self.data_source = data_source
        
    def export_data(self, data: List[Any]) -> bool:
        """Export data to webhook."""
        try:
            # Prepare payload
            payload = {
                "timestamp": time.time(),
                "source": self.data_source.__class__.__name__,
                "data": [item.to_dict() if hasattr(item, 'to_dict') else item for item in data]
            }
            
            # Prepare headers
            headers = {"Content-Type": "application/json"}
            if self.webhook_config.headers:
                headers.update(self.webhook_config.headers)
            
            if self.webhook_config.auth_token:
                headers["Authorization"] = f"Bearer {self.webhook_config.auth_token}"
            
            # Send request
            response = requests.request(
                method=self.webhook_config.method,
                url=self.webhook_config.url,
                json=payload,
                headers=headers,
                timeout=self.config.timeout,
                verify=self.webhook_config.verify_ssl
            )
            
            response.raise_for_status()
            
            with self.lock:
                self.total_exports += 1
                self.last_export_time = time.time()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to export to webhook: {str(e)}")
            with self.lock:
                self.failed_exports += 1
            return False
    
    def _perform_export(self):
        """Perform webhook export."""
        # This is a generic implementation - specific data collection
        # would depend on the data source type
        if hasattr(self.data_source, 'get_all_metrics'):
            # Metrics collector
            data = self.data_source.get_all_metrics()
            if data:
                self.export_data([{"metrics": data}])
        elif hasattr(self.data_source, 'get_active_alerts'):
            # Alert manager
            alerts = self.data_source.get_active_alerts()
            if alerts:
                self.export_data(alerts)
        elif hasattr(self.data_source, 'get_log_stats'):
            # Log aggregator
            stats = self.data_source.get_log_stats()
            if stats:
                self.export_data([{"log_stats": stats}])


class ExporterManager:
    """
    Manager for multiple exporters.
    
    Coordinates multiple exporters and provides centralized control.
    """
    
    def __init__(self):
        """Initialize exporter manager."""
        self.exporters: List[BaseExporter] = []
        self.running = False
        
    def add_exporter(self, exporter: BaseExporter):
        """
        Add an exporter.
        
        Args:
            exporter: Exporter instance
        """
        self.exporters.append(exporter)
        
        if self.running:
            exporter.start_export()
        
        logger.info(f"Added exporter: {exporter.__class__.__name__}")
    
    def remove_exporter(self, exporter: BaseExporter):
        """
        Remove an exporter.
        
        Args:
            exporter: Exporter instance to remove
        """
        if exporter in self.exporters:
            exporter.stop_export()
            self.exporters.remove(exporter)
            logger.info(f"Removed exporter: {exporter.__class__.__name__}")
    
    def start_all(self):
        """Start all exporters."""
        if self.running:
            return
        
        self.running = True
        
        for exporter in self.exporters:
            exporter.start_export()
        
        logger.info(f"Started {len(self.exporters)} exporters")
    
    def stop_all(self):
        """Stop all exporters."""
        self.running = False
        
        for exporter in self.exporters:
            exporter.stop_export()
        
        logger.info("Stopped all exporters")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all exporters."""
        stats = {}
        
        for exporter in self.exporters:
            exporter_name = exporter.__class__.__name__
            stats[exporter_name] = exporter.get_stats()
        
        return {
            "total_exporters": len(self.exporters),
            "running": self.running,
            "exporters": stats
        }
