# DataLineagePy Monitoring Guide

## Overview

DataLineagePy's enterprise monitoring infrastructure provides comprehensive observability, alerting, and performance insights for production deployments. This guide covers setup, configuration, and best practices for monitoring your DataLineagePy deployment.

## Architecture

The monitoring system consists of five core components:

1. **Metrics Collector** - Collects and aggregates performance metrics
2. **Alert Manager** - Rule-based alerting with multiple notification channels
3. **Log Aggregator** - Centralized log collection and analysis
4. **Dashboard** - Real-time web-based monitoring interface
5. **Exporters** - Integration with external monitoring systems

## Quick Start

### Basic Setup

```python
from datalineagepy.infrastructure.monitoring import setup_monitoring

# Setup with default configuration
monitoring = setup_monitoring()

# Start monitoring
monitoring.start()

# Your application code here...

# Stop monitoring
monitoring.stop()
```

### With Configuration

```python
config = {
    'dashboard': {
        'enabled': True,
        'host': '0.0.0.0',
        'port': 8080,
        'auto_refresh': 30
    },
    'exporters': {
        'prometheus': {
            'enabled': True,
            'pushgateway_url': 'http://localhost:9091',
            'job_name': 'datalineagepy'
        }
    }
}

monitoring = setup_monitoring(config)
monitoring.start()
```

## Components

### Metrics Collector

Collects various types of metrics:

- **Counters** - Monotonically increasing values
- **Gauges** - Point-in-time values that can go up or down
- **Histograms** - Distribution of values over time
- **Timers** - Duration measurements
- **Summaries** - Statistical summaries with quantiles

#### Usage Examples

```python
from datalineagepy.infrastructure.monitoring import get_monitoring

monitoring = get_monitoring()
collector = monitoring.metrics_collector

# Counter - track total operations
collector.increment("operations.total")
collector.increment("operations.total", labels={"type": "lineage"})

# Gauge - current system state
collector.set_gauge("memory.usage", 75.5)
collector.set_gauge("queue.size", 42)

# Histogram - value distributions
collector.record_histogram("request.size", 1024)
collector.record_histogram("response.time", 0.25)

# Timer - duration measurements
with collector.timer("operation.duration"):
    # Your code here
    pass

# Or using decorator
@collector.timed("function.duration")
def my_function():
    # Function code
    pass
```

### Alert Manager

Rule-based alerting system with multiple notification channels.

#### Alert Rules

```python
from datalineagepy.infrastructure.monitoring import (
    AlertRule, AlertCondition, AlertSeverity
)

# High error rate alert
error_alert = AlertRule(
    name="high_error_rate",
    condition=AlertCondition.GREATER_THAN,
    threshold=10.0,
    metric_name="errors.total",
    severity=AlertSeverity.CRITICAL,
    description="Error rate is too high",
    evaluation_period=300,  # 5 minutes
    min_duration=60         # Must persist for 1 minute
)

monitoring.alert_manager.add_rule(error_alert)
```

#### Notification Channels

```python
from datalineagepy.infrastructure.monitoring import AlertChannel

# Email notifications
email_config = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "alerts@company.com",
    "password": "app_password",
    "recipients": ["admin@company.com", "ops@company.com"]
}

monitoring.alert_manager.add_notification_handler(
    AlertChannel.EMAIL, 
    email_config
)

# Webhook notifications
webhook_config = {
    "url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
    "method": "POST",
    "headers": {"Content-Type": "application/json"}
}

monitoring.alert_manager.add_notification_handler(
    AlertChannel.WEBHOOK,
    webhook_config
)
```

### Log Aggregator

Centralized logging with filtering, search, and analysis capabilities.

#### Basic Usage

```python
from datalineagepy.infrastructure.monitoring import LogLevel, LogSource

log_aggregator = monitoring.log_aggregator

# Add log entries
log_aggregator.add_log(
    level=LogLevel.INFO,
    message="Operation completed successfully",
    logger_name="datalineage.tracker",
    source=LogSource.APPLICATION,
    extra_data={"duration": 0.25, "records": 1000}
)

# Search logs
from datalineagepy.infrastructure.monitoring import LogFilter

log_filter = LogFilter(
    min_level=LogLevel.WARNING,
    message_contains="error",
    time_range=(start_time, end_time)
)

logs = log_aggregator.search_logs(log_filter, limit=100)
```

#### Integration with Python Logging

```python
import logging
from datalineagepy.infrastructure.monitoring import LogHandler

# Create custom log handler
log_handler = LogHandler(log_aggregator, source=LogSource.APPLICATION)

# Add to Python logger
logger = logging.getLogger("myapp")
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)

# Now all log messages go to the aggregator
logger.info("Application started")
logger.error("Database connection failed")
```

### Dashboard

Web-based real-time monitoring interface.

#### Features

- Real-time metrics visualization
- Alert status monitoring
- Log analysis and search
- System health overview
- Interactive charts and graphs
- Responsive design

#### Access

Once started, the dashboard is available at:
- Default: `http://localhost:8080`
- Custom: `http://{host}:{port}` based on configuration

#### Configuration

```python
from datalineagepy.infrastructure.monitoring import DashboardConfig

dashboard_config = DashboardConfig(
    host="0.0.0.0",
    port=8080,
    debug=False,
    auto_refresh=30,  # seconds
    max_data_points=100,
    theme="dark"  # or "light"
)
```

### Exporters

Integration with external monitoring systems.

#### Prometheus

```python
from datalineagepy.infrastructure.monitoring.exporters import (
    PrometheusExporter, PrometheusConfig
)

prometheus_config = PrometheusConfig(
    pushgateway_url="http://localhost:9091",
    job_name="datalineagepy",
    instance="production-01"
)

prometheus_exporter = PrometheusExporter(
    prometheus_config, 
    monitoring.metrics_collector
)

monitoring.exporter_manager.add_exporter(prometheus_exporter)
```

#### InfluxDB

```python
from datalineagepy.infrastructure.monitoring.exporters import (
    InfluxDBExporter, InfluxDBConfig
)

influxdb_config = InfluxDBConfig(
    url="http://localhost:8086",
    database="datalineagepy",
    username="admin",
    password="password"
)

influxdb_exporter = InfluxDBExporter(
    influxdb_config,
    monitoring.metrics_collector
)

monitoring.exporter_manager.add_exporter(influxdb_exporter)
```

#### Elasticsearch

```python
from datalineagepy.infrastructure.monitoring.exporters import (
    ElasticsearchExporter, ElasticsearchConfig
)

elasticsearch_config = ElasticsearchConfig(
    url="http://localhost:9200",
    index_prefix="datalineagepy",
    username="elastic",
    password="password"
)

elasticsearch_exporter = ElasticsearchExporter(
    elasticsearch_config,
    monitoring.log_aggregator
)

monitoring.exporter_manager.add_exporter(elasticsearch_exporter)
```

## Integration

### DataLineage Tracker Integration

```python
# Automatic integration
monitoring.integrate_with_tracker(your_tracker)

# Manual integration using decorators
@monitoring.monitor_function("track_operation")
def track_dataframe(df):
    # Your tracking code
    return result

# Context manager approach
with monitoring.monitor_operation("complex_analysis"):
    # Your analysis code
    pass
```

### Scalability Components Integration

```python
# Integrate with load balancer and horizontal scaler
monitoring.integrate_with_scalability(
    load_balancer=your_load_balancer,
    horizontal_scaler=your_horizontal_scaler
)
```

### High Availability Integration

```python
# Integrate with health checker and circuit breaker
monitoring.integrate_with_high_availability(
    health_checker=your_health_checker,
    circuit_breaker=your_circuit_breaker
)
```

## Configuration

### Environment Variables

```bash
# Dashboard settings
DATALINEAGE_DASHBOARD_HOST=0.0.0.0
DATALINEAGE_DASHBOARD_PORT=8080

# Metrics settings
DATALINEAGE_METRICS_RETENTION=3600
DATALINEAGE_METRICS_MAX_COUNT=100000

# Alert settings
DATALINEAGE_ALERT_EVALUATION_INTERVAL=60
DATALINEAGE_ALERT_MIN_DURATION=120

# Log settings
DATALINEAGE_LOG_MAX_ENTRIES=1000000
DATALINEAGE_LOG_RETENTION_DAYS=30
```

### Configuration File

```yaml
# monitoring-config.yaml
monitoring:
  dashboard:
    enabled: true
    host: "0.0.0.0"
    port: 8080
    auto_refresh: 30
    theme: "dark"
  
  metrics:
    retention_period: 3600
    max_metrics: 100000
    cleanup_interval: 300
    aggregation_interval: 60
  
  alerts:
    evaluation_interval: 60
    min_duration: 120
    max_frequency: 3600
    resolve_timeout: 300
  
  logs:
    max_entries: 1000000
    retention_days: 30
    processing_queue_size: 10000
    cleanup_interval: 3600
  
  exporters:
    prometheus:
      enabled: true
      pushgateway_url: "http://localhost:9091"
      job_name: "datalineagepy"
    
    influxdb:
      enabled: false
      url: "http://localhost:8086"
      database: "datalineagepy"
    
    elasticsearch:
      enabled: false
      url: "http://localhost:9200"
      index_prefix: "datalineagepy"
```

## Best Practices

### Metrics

1. **Use appropriate metric types**:
   - Counters for cumulative values (requests, errors)
   - Gauges for current state (memory usage, queue size)
   - Histograms for distributions (response times, request sizes)

2. **Add meaningful labels**:
   ```python
   collector.increment("requests.total", labels={
       "method": "POST",
       "endpoint": "/api/lineage",
       "status": "200"
   })
   ```

3. **Avoid high cardinality labels**:
   - Don't use user IDs, timestamps, or random values as labels
   - Keep label combinations under 10,000

### Alerts

1. **Set appropriate thresholds**:
   - Use historical data to determine normal ranges
   - Account for business hours and seasonal patterns

2. **Implement alert fatigue prevention**:
   - Use evaluation periods and minimum durations
   - Group related alerts
   - Implement escalation policies

3. **Test alert rules**:
   ```python
   # Test alert conditions
   monitoring.alert_manager.test_rule("high_error_rate", test_metrics)
   ```

### Logs

1. **Use structured logging**:
   ```python
   log_aggregator.add_log(
       level=LogLevel.INFO,
       message="User action completed",
       logger_name="user.service",
       source=LogSource.APPLICATION,
       extra_data={
           "user_id": "12345",
           "action": "create_lineage",
           "duration": 0.25,
           "success": True
       }
   )
   ```

2. **Implement log sampling for high-volume applications**:
   ```python
   import random
   
   if random.random() < 0.1:  # Sample 10% of logs
       log_aggregator.add_log(...)
   ```

### Performance

1. **Monitor monitoring overhead**:
   ```python
   # Check monitoring performance
   stats = monitoring.get_monitoring_status()
   print(f"Metrics processing time: {stats['metrics_collector']['processing_time']}")
   ```

2. **Use background processing**:
   - All components use background threads by default
   - Avoid blocking main application threads

3. **Configure retention policies**:
   - Set appropriate retention periods for metrics and logs
   - Use cleanup intervals to manage memory usage

## Troubleshooting

### Common Issues

1. **Dashboard not accessible**:
   - Check if dashboard is enabled in configuration
   - Verify host and port settings
   - Check firewall rules

2. **Metrics not appearing**:
   - Verify metric names and labels
   - Check if metrics collector is running
   - Review retention settings

3. **Alerts not firing**:
   - Check alert rule conditions and thresholds
   - Verify evaluation periods and minimum durations
   - Test notification channels

4. **High memory usage**:
   - Review retention settings
   - Check for high cardinality metrics
   - Implement sampling for high-volume logs

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger('datalineagepy.infrastructure.monitoring').setLevel(logging.DEBUG)

# Check component status
status = monitoring.get_monitoring_status()
print(json.dumps(status, indent=2))
```

## Production Deployment

### Docker

```dockerfile
# Dockerfile
FROM python:3.9-slim

# Install monitoring dependencies
COPY requirements-monitoring.txt .
RUN pip install -r requirements-monitoring.txt

# Copy application
COPY . /app
WORKDIR /app

# Expose dashboard port
EXPOSE 8080

# Start with monitoring
CMD ["python", "-m", "your_app_with_monitoring"]
```

### Kubernetes

```yaml
# monitoring-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: datalineagepy-monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: datalineagepy-monitoring
  template:
    metadata:
      labels:
        app: datalineagepy-monitoring
    spec:
      containers:
      - name: app
        image: datalineagepy:latest
        ports:
        - containerPort: 8080
          name: dashboard
        env:
        - name: DATALINEAGE_DASHBOARD_HOST
          value: "0.0.0.0"
        - name: DATALINEAGE_DASHBOARD_PORT
          value: "8080"
---
apiVersion: v1
kind: Service
metadata:
  name: datalineagepy-monitoring-service
spec:
  selector:
    app: datalineagepy-monitoring
  ports:
  - port: 8080
    targetPort: 8080
    name: dashboard
  type: LoadBalancer
```

### Security Considerations

1. **Dashboard Access**:
   - Use authentication/authorization
   - Restrict network access
   - Use HTTPS in production

2. **Exporter Credentials**:
   - Store credentials securely (Kubernetes secrets, environment variables)
   - Use least-privilege access
   - Rotate credentials regularly

3. **Log Data**:
   - Avoid logging sensitive information
   - Implement log sanitization
   - Use secure transport for log shipping

## Examples

See `examples/monitoring_example.py` for a complete working example demonstrating all monitoring features.

## Support

For issues and questions:
- Check the troubleshooting section above
- Review component logs with debug logging enabled
- Consult the API documentation for detailed method signatures
- Open an issue in the DataLineagePy repository
