"""
DataLineagePy Monitoring Example
Demonstrates comprehensive monitoring capabilities.
"""

import time
import logging
import threading
from datalineagepy.infrastructure.monitoring import (
    setup_monitoring,
    get_monitoring,
    MetricType,
    AlertRule,
    AlertCondition,
    AlertSeverity,
    LogLevel,
    LogSource
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def simulate_datalineage_operations():
    """Simulate DataLineage operations with monitoring."""
    monitoring = get_monitoring()
    
    # Simulate various operations
    operations = [
        "track_dataframe",
        "analyze_lineage", 
        "generate_report",
        "validate_schema",
        "process_metadata"
    ]
    
    for i in range(100):
        operation = operations[i % len(operations)]
        
        # Use monitoring context manager
        with monitoring.monitor_operation(f"datalineage.{operation}"):
            # Simulate work
            work_time = 0.1 + (i % 5) * 0.05  # Variable work time
            time.sleep(work_time)
            
            # Simulate occasional errors
            if i % 20 == 19:  # 5% error rate
                raise Exception(f"Simulated error in {operation}")
        
        # Add some custom metrics
        monitoring.metrics_collector.increment("operations.processed")
        monitoring.metrics_collector.set_gauge("operations.queue_size", max(0, 50 - i))
        
        if i % 10 == 0:
            logger.info(f"Processed {i+1} operations")


def simulate_system_metrics():
    """Simulate system metrics collection."""
    monitoring = get_monitoring()
    
    import random
    
    for i in range(60):  # Run for 1 minute
        # Simulate system metrics
        cpu_usage = 20 + random.random() * 60  # 20-80%
        memory_usage = 30 + random.random() * 50  # 30-80%
        disk_usage = 40 + random.random() * 40  # 40-80%
        
        monitoring.metrics_collector.set_gauge("system.cpu.usage", cpu_usage)
        monitoring.metrics_collector.set_gauge("system.memory.usage", memory_usage)
        monitoring.metrics_collector.set_gauge("system.disk.usage", disk_usage)
        
        # Simulate network metrics
        network_in = random.random() * 1000  # MB/s
        network_out = random.random() * 500   # MB/s
        
        monitoring.metrics_collector.set_gauge("system.network.in", network_in)
        monitoring.metrics_collector.set_gauge("system.network.out", network_out)
        
        # Add some log entries
        if i % 10 == 0:
            monitoring.log_aggregator.add_log(
                level=LogLevel.INFO,
                message=f"System metrics collected - CPU: {cpu_usage:.1f}%, Memory: {memory_usage:.1f}%",
                logger_name="system.monitor",
                source=LogSource.SYSTEM
            )
        
        time.sleep(1)


def setup_custom_alerts():
    """Setup custom alert rules."""
    monitoring = get_monitoring()
    
    # High CPU usage alert
    cpu_alert = AlertRule(
        name="high_cpu_usage",
        condition=AlertCondition.GREATER_THAN,
        threshold=80.0,
        metric_name="system.cpu.usage",
        severity=AlertSeverity.HIGH,
        description="CPU usage is above 80%",
        evaluation_period=60,  # 1 minute
        min_duration=120       # Must persist for 2 minutes
    )
    
    # High memory usage alert
    memory_alert = AlertRule(
        name="high_memory_usage", 
        condition=AlertCondition.GREATER_THAN,
        threshold=75.0,
        metric_name="system.memory.usage",
        severity=AlertSeverity.MEDIUM,
        description="Memory usage is above 75%",
        evaluation_period=60,
        min_duration=180
    )
    
    # High error rate alert
    error_rate_alert = AlertRule(
        name="high_error_rate",
        condition=AlertCondition.GREATER_THAN,
        threshold=5.0,
        metric_name="datalineage.errors.total",
        severity=AlertSeverity.CRITICAL,
        description="Error rate is too high",
        evaluation_period=300,  # 5 minutes
        min_duration=60
    )
    
    # Low operations rate alert
    ops_rate_alert = AlertRule(
        name="low_operations_rate",
        condition=AlertCondition.LESS_THAN,
        threshold=10.0,
        metric_name="operations.processed",
        severity=AlertSeverity.LOW,
        description="Operations rate is too low",
        evaluation_period=300,
        min_duration=600  # 10 minutes
    )
    
    # Add all alert rules
    for alert in [cpu_alert, memory_alert, error_rate_alert, ops_rate_alert]:
        monitoring.alert_manager.add_rule(alert)
        logger.info(f"Added alert rule: {alert.name}")


def setup_monitoring_dashboard():
    """Setup and start monitoring dashboard."""
    monitoring = get_monitoring()
    
    if monitoring.dashboard:
        logger.info(f"Starting monitoring dashboard at {monitoring.dashboard.get_dashboard_url()}")
        logger.info("Dashboard features:")
        logger.info("- Real-time metrics visualization")
        logger.info("- Alert status monitoring")
        logger.info("- Log analysis and search")
        logger.info("- System health overview")
        logger.info("- Interactive charts and graphs")
    else:
        logger.warning("Dashboard not configured")


def demonstrate_monitoring_integration():
    """Demonstrate monitoring integration with mock components."""
    monitoring = get_monitoring()
    
    # Mock DataLineage tracker
    class MockTracker:
        def track(self, data):
            # Simulate tracking work
            time.sleep(0.1)
            return {"lineage_id": "mock_123", "nodes": 5, "edges": 8}
    
    # Mock load balancer
    class MockLoadBalancer:
        def __init__(self):
            self.stats = {"total_connections": 0, "active_connections": 0}
        
        def get_next_server(self):
            self.stats["total_connections"] += 1
            self.stats["active_connections"] = max(0, self.stats["active_connections"] + 1)
            time.sleep(0.05)  # Simulate work
            return {"server_id": "server_1", "host": "localhost", "port": 8080}
        
        def get_stats(self):
            return self.stats
    
    # Create mock components
    tracker = MockTracker()
    load_balancer = MockLoadBalancer()
    
    # Integrate with monitoring
    monitoring.integrate_with_tracker(tracker)
    monitoring.integrate_with_scalability(load_balancer=load_balancer)
    
    logger.info("Integrated monitoring with mock components")
    
    # Test integrated tracking
    for i in range(10):
        try:
            result = tracker.track(f"data_{i}")
            logger.info(f"Tracked data_{i}: {result}")
        except Exception as e:
            logger.error(f"Tracking failed: {e}")
        
        # Test load balancer
        server = load_balancer.get_next_server()
        logger.info(f"Selected server: {server}")
        
        time.sleep(0.5)


def main():
    """Main monitoring demonstration."""
    logger.info("Starting DataLineagePy Monitoring Example")
    
    # Setup monitoring with configuration
    config = {
        'dashboard': {
            'enabled': True,
            'host': '0.0.0.0',
            'port': 8080,
            'auto_refresh': 30
        },
        'exporters': {
            'prometheus': {
                'enabled': False,  # Disable for demo
                'pushgateway_url': 'http://localhost:9091'
            },
            'influxdb': {
                'enabled': False,  # Disable for demo
                'url': 'http://localhost:8086',
                'database': 'datalineagepy'
            },
            'elasticsearch': {
                'enabled': False,  # Disable for demo
                'url': 'http://localhost:9200',
                'index_prefix': 'datalineagepy'
            }
        }
    }
    
    monitoring = setup_monitoring(config)
    
    # Start monitoring
    monitoring.start()
    
    try:
        # Setup custom alerts
        setup_custom_alerts()
        
        # Setup dashboard
        setup_monitoring_dashboard()
        
        # Demonstrate integration
        demonstrate_monitoring_integration()
        
        # Start background threads for simulation
        threads = []
        
        # System metrics thread
        system_thread = threading.Thread(
            target=simulate_system_metrics,
            daemon=True,
            name="system-metrics"
        )
        system_thread.start()
        threads.append(system_thread)
        
        # Operations thread
        ops_thread = threading.Thread(
            target=simulate_datalineage_operations,
            daemon=True,
            name="operations"
        )
        ops_thread.start()
        threads.append(ops_thread)
        
        # Let simulation run
        logger.info("Monitoring simulation running...")
        logger.info("Check the following:")
        logger.info("1. Dashboard at http://localhost:8080")
        logger.info("2. Metrics being collected")
        logger.info("3. Alerts being triggered")
        logger.info("4. Logs being aggregated")
        logger.info("Press Ctrl+C to stop")
        
        # Monitor status
        while True:
            time.sleep(30)
            
            # Print monitoring status
            status = monitoring.get_monitoring_status()
            logger.info("=== Monitoring Status ===")
            logger.info(f"Running: {status['running']}")
            logger.info(f"Active Alerts: {status['alert_manager']['active_alerts']}")
            logger.info(f"Metrics Count: {status['metrics_collector']['stats'].get('total_metrics', 0)}")
            logger.info(f"Log Entries: {status['log_aggregator']['stats'].get('total_entries', 0)}")
            
            # Show active alerts
            active_alerts = monitoring.alert_manager.get_active_alerts()
            if active_alerts:
                logger.warning(f"Active Alerts ({len(active_alerts)}):")
                for alert in active_alerts[:5]:  # Show first 5
                    logger.warning(f"  - {alert.rule_name}: {alert.message} ({alert.severity})")
            
    except KeyboardInterrupt:
        logger.info("Stopping monitoring example...")
    
    finally:
        # Stop monitoring
        monitoring.stop()
        logger.info("Monitoring example stopped")


if __name__ == "__main__":
    main()
