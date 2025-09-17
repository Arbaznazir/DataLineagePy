"""
Monitoring Dashboard Implementation
Real-time monitoring dashboard with web interface.
"""

import time
import threading
import logging
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify, request
import plotly.graph_objs as go
import plotly.utils

from .metrics_collector import MetricsCollector, AggregationType
from .alert_manager import AlertManager, AlertSeverity
from .log_aggregator import LogAggregator, LogFilter, LogLevel

logger = logging.getLogger(__name__)


@dataclass
class DashboardConfig:
    """Dashboard configuration."""
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    auto_refresh: int = 30  # seconds
    max_data_points: int = 100
    theme: str = "dark"  # dark or light


class MonitoringDashboard:
    """
    Real-time monitoring dashboard with web interface.
    
    Features:
    - Real-time metrics visualization
    - Alert status monitoring
    - Log analysis and search
    - System health overview
    - Interactive charts and graphs
    - Responsive web interface
    """
    
    def __init__(self, metrics_collector: MetricsCollector = None,
                 alert_manager: AlertManager = None,
                 log_aggregator: LogAggregator = None,
                 config: DashboardConfig = None):
        """
        Initialize monitoring dashboard.
        
        Args:
            metrics_collector: Metrics collector instance
            alert_manager: Alert manager instance
            log_aggregator: Log aggregator instance
            config: Dashboard configuration
        """
        self.metrics_collector = metrics_collector
        self.alert_manager = alert_manager
        self.log_aggregator = log_aggregator
        self.config = config or DashboardConfig()
        
        # Flask app
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'monitoring-dashboard-secret'
        
        # Setup routes
        self._setup_routes()
        
        # Dashboard state
        self.running = False
        self.server_thread = None
        
        logger.info("Monitoring dashboard initialized")
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page."""
            return render_template_string(self._get_dashboard_template())
        
        @self.app.route('/api/metrics')
        def api_metrics():
            """Get metrics data."""
            try:
                if not self.metrics_collector:
                    return jsonify({"error": "Metrics collector not available"})
                
                # Get time range from query params
                hours = request.args.get('hours', 1, type=int)
                end_time = time.time()
                start_time = end_time - (hours * 3600)
                
                # Get all metrics
                all_metrics = self.metrics_collector.get_all_metrics((start_time, end_time))
                
                # Format for dashboard
                metrics_data = {}
                for name, data in all_metrics.items():
                    metrics_data[name] = {
                        "current_value": data.get("last_value", 0),
                        "average": data.get("average", 0),
                        "min": data.get("min", 0),
                        "max": data.get("max", 0),
                        "count": data.get("count", 0),
                        "rate": data.get("rate_per_second", 0)
                    }
                
                return jsonify({
                    "metrics": metrics_data,
                    "timestamp": time.time(),
                    "time_range": {"start": start_time, "end": end_time}
                })
                
            except Exception as e:
                logger.error(f"Failed to get metrics data: {str(e)}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/alerts')
        def api_alerts():
            """Get alerts data."""
            try:
                if not self.alert_manager:
                    return jsonify({"error": "Alert manager not available"})
                
                # Get active alerts
                active_alerts = self.alert_manager.get_active_alerts()
                
                # Get alert history
                alert_history = self.alert_manager.get_alert_history(limit=50)
                
                # Get alert stats
                alert_stats = self.alert_manager.get_alert_stats()
                
                return jsonify({
                    "active_alerts": [alert.to_dict() for alert in active_alerts],
                    "alert_history": alert_history,
                    "stats": alert_stats,
                    "timestamp": time.time()
                })
                
            except Exception as e:
                logger.error(f"Failed to get alerts data: {str(e)}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/logs')
        def api_logs():
            """Get logs data."""
            try:
                if not self.log_aggregator:
                    return jsonify({"error": "Log aggregator not available"})
                
                # Get query parameters
                level = request.args.get('level')
                source = request.args.get('source')
                search = request.args.get('search')
                hours = request.args.get('hours', 1, type=int)
                limit = request.args.get('limit', 100, type=int)
                
                # Create filter
                end_time = time.time()
                start_time = end_time - (hours * 3600)
                
                log_filter = LogFilter(
                    time_range=(start_time, end_time),
                    message_contains=search if search else None
                )
                
                if level:
                    log_filter.min_level = LogLevel[level.upper()]
                
                # Search logs
                logs = self.log_aggregator.search_logs(log_filter, limit=limit)
                
                # Get log stats
                log_stats = self.log_aggregator.get_log_stats()
                
                # Get log aggregations
                aggregations = self.log_aggregator.aggregate_logs("1h", (start_time, end_time))
                
                return jsonify({
                    "logs": [log.to_dict() for log in logs],
                    "stats": log_stats,
                    "aggregations": [
                        {
                            "time_bucket": agg.time_bucket,
                            "count": agg.count,
                            "error_count": agg.error_count,
                            "warning_count": agg.warning_count,
                            "levels": dict(agg.levels),
                            "sources": dict(agg.sources)
                        }
                        for agg in aggregations
                    ],
                    "timestamp": time.time()
                })
                
            except Exception as e:
                logger.error(f"Failed to get logs data: {str(e)}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/system')
        def api_system():
            """Get system health data."""
            try:
                import psutil
                
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Get component stats
                component_stats = {}
                
                if self.metrics_collector:
                    component_stats['metrics_collector'] = self.metrics_collector.get_collector_stats()
                
                if self.alert_manager:
                    component_stats['alert_manager'] = self.alert_manager.get_alert_stats()
                
                if self.log_aggregator:
                    component_stats['log_aggregator'] = self.log_aggregator.get_log_stats()
                
                return jsonify({
                    "system": {
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                        "memory_used_gb": memory.used / (1024**3),
                        "memory_total_gb": memory.total / (1024**3),
                        "disk_percent": disk.percent,
                        "disk_used_gb": disk.used / (1024**3),
                        "disk_total_gb": disk.total / (1024**3)
                    },
                    "components": component_stats,
                    "timestamp": time.time()
                })
                
            except Exception as e:
                logger.error(f"Failed to get system data: {str(e)}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/charts/metrics/<metric_name>')
        def api_metric_chart(metric_name):
            """Get metric chart data."""
            try:
                if not self.metrics_collector:
                    return jsonify({"error": "Metrics collector not available"})
                
                # Get time range
                hours = request.args.get('hours', 1, type=int)
                end_time = time.time()
                start_time = end_time - (hours * 3600)
                
                # Get metric history
                history = self.metrics_collector.get_metric_history(metric_name, limit=self.config.max_data_points)
                
                # Filter by time range
                filtered_history = [
                    h for h in history 
                    if start_time <= h.timestamp <= end_time
                ]
                
                if not filtered_history:
                    return jsonify({"error": "No data available"})
                
                # Prepare chart data
                timestamps = [datetime.fromtimestamp(h.timestamp) for h in filtered_history]
                values = [h.value for h in filtered_history]
                
                # Create Plotly chart
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=timestamps,
                    y=values,
                    mode='lines+markers',
                    name=metric_name,
                    line=dict(color='#00d4aa', width=2),
                    marker=dict(size=4)
                ))
                
                fig.update_layout(
                    title=f"Metric: {metric_name}",
                    xaxis_title="Time",
                    yaxis_title="Value",
                    template="plotly_dark" if self.config.theme == "dark" else "plotly_white",
                    height=400
                )
                
                return jsonify({
                    "chart": json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig)),
                    "timestamp": time.time()
                })
                
            except Exception as e:
                logger.error(f"Failed to get metric chart: {str(e)}")
                return jsonify({"error": str(e)}), 500
    
    def _get_dashboard_template(self) -> str:
        """Get dashboard HTML template."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DataLineagePy Monitoring Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { 
            background-color: #1a1a1a; 
            color: #ffffff; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .card { 
            background-color: #2d2d2d; 
            border: 1px solid #404040; 
            margin-bottom: 20px;
        }
        .card-header { 
            background-color: #3d3d3d; 
            border-bottom: 1px solid #404040; 
        }
        .metric-card { 
            text-align: center; 
            padding: 20px; 
        }
        .metric-value { 
            font-size: 2rem; 
            font-weight: bold; 
            color: #00d4aa; 
        }
        .metric-label { 
            font-size: 0.9rem; 
            color: #cccccc; 
        }
        .alert-critical { 
            border-left: 4px solid #dc3545; 
        }
        .alert-high { 
            border-left: 4px solid #fd7e14; 
        }
        .alert-medium { 
            border-left: 4px solid #ffc107; 
        }
        .alert-low { 
            border-left: 4px solid #20c997; 
        }
        .log-entry { 
            font-family: 'Courier New', monospace; 
            font-size: 0.85rem; 
            margin-bottom: 5px; 
            padding: 5px; 
            border-radius: 3px; 
        }
        .log-error { 
            background-color: rgba(220, 53, 69, 0.1); 
        }
        .log-warning { 
            background-color: rgba(255, 193, 7, 0.1); 
        }
        .log-info { 
            background-color: rgba(13, 202, 240, 0.1); 
        }
        .status-indicator { 
            width: 12px; 
            height: 12px; 
            border-radius: 50%; 
            display: inline-block; 
            margin-right: 8px; 
        }
        .status-healthy { 
            background-color: #28a745; 
        }
        .status-warning { 
            background-color: #ffc107; 
        }
        .status-critical { 
            background-color: #dc3545; 
        }
        .refresh-indicator { 
            position: fixed; 
            top: 20px; 
            right: 20px; 
            z-index: 1000; 
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container-fluid">
            <span class="navbar-brand mb-0 h1">
                <i class="fas fa-chart-line"></i> DataLineagePy Monitoring Dashboard
            </span>
            <div class="d-flex">
                <span class="badge bg-success me-2" id="last-update">Last Update: --</span>
                <button class="btn btn-outline-light btn-sm" onclick="refreshDashboard()">
                    <i class="fas fa-sync-alt"></i> Refresh
                </button>
            </div>
        </div>
    </nav>

    <div class="container-fluid mt-4">
        <!-- System Health Row -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body">
                        <div class="metric-value" id="cpu-usage">--</div>
                        <div class="metric-label">CPU Usage</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body">
                        <div class="metric-value" id="memory-usage">--</div>
                        <div class="metric-label">Memory Usage</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body">
                        <div class="metric-value" id="disk-usage">--</div>
                        <div class="metric-label">Disk Usage</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body">
                        <div class="metric-value" id="active-alerts">--</div>
                        <div class="metric-label">Active Alerts</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Content Row -->
        <div class="row">
            <!-- Metrics Column -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-bar"></i> Metrics Overview</h5>
                    </div>
                    <div class="card-body">
                        <div id="metrics-container">
                            <p class="text-muted">Loading metrics...</p>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-exclamation-triangle"></i> Active Alerts</h5>
                    </div>
                    <div class="card-body">
                        <div id="alerts-container">
                            <p class="text-muted">Loading alerts...</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Logs Column -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-file-alt"></i> Recent Logs</h5>
                        <div class="float-end">
                            <select class="form-select form-select-sm" id="log-level-filter" onchange="filterLogs()">
                                <option value="">All Levels</option>
                                <option value="error">Error</option>
                                <option value="warning">Warning</option>
                                <option value="info">Info</option>
                                <option value="debug">Debug</option>
                            </select>
                        </div>
                    </div>
                    <div class="card-body">
                        <div id="logs-container" style="max-height: 600px; overflow-y: auto;">
                            <p class="text-muted">Loading logs...</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts Row -->
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> Metrics Charts</h5>
                    </div>
                    <div class="card-body">
                        <div id="charts-container">
                            <p class="text-muted">Loading charts...</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="refresh-indicator">
        <div class="spinner-border text-primary" role="status" id="loading-spinner" style="display: none;">
            <span class="visually-hidden">Loading...</span>
        </div>
    </div>

    <script>
        let refreshInterval;
        
        function showLoading() {
            document.getElementById('loading-spinner').style.display = 'block';
        }
        
        function hideLoading() {
            document.getElementById('loading-spinner').style.display = 'none';
        }
        
        function updateLastRefresh() {
            document.getElementById('last-update').textContent = 'Last Update: ' + new Date().toLocaleTimeString();
        }
        
        function loadSystemData() {
            fetch('/api/system')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('System data error:', data.error);
                        return;
                    }
                    
                    const system = data.system;
                    document.getElementById('cpu-usage').textContent = system.cpu_percent.toFixed(1) + '%';
                    document.getElementById('memory-usage').textContent = system.memory_percent.toFixed(1) + '%';
                    document.getElementById('disk-usage').textContent = system.disk_percent.toFixed(1) + '%';
                })
                .catch(error => console.error('Error loading system data:', error));
        }
        
        function loadMetrics() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('Metrics error:', data.error);
                        return;
                    }
                    
                    const container = document.getElementById('metrics-container');
                    let html = '';
                    
                    for (const [name, metric] of Object.entries(data.metrics)) {
                        html += `
                            <div class="row mb-2">
                                <div class="col-6">${name}</div>
                                <div class="col-3 text-end">${metric.current_value.toFixed(2)}</div>
                                <div class="col-3 text-end text-muted">${metric.rate.toFixed(2)}/s</div>
                            </div>
                        `;
                    }
                    
                    container.innerHTML = html || '<p class="text-muted">No metrics available</p>';
                })
                .catch(error => console.error('Error loading metrics:', error));
        }
        
        function loadAlerts() {
            fetch('/api/alerts')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('Alerts error:', data.error);
                        return;
                    }
                    
                    document.getElementById('active-alerts').textContent = data.active_alerts.length;
                    
                    const container = document.getElementById('alerts-container');
                    let html = '';
                    
                    if (data.active_alerts.length === 0) {
                        html = '<p class="text-success"><i class="fas fa-check-circle"></i> No active alerts</p>';
                    } else {
                        for (const alert of data.active_alerts) {
                            const severityClass = `alert-${alert.severity}`;
                            html += `
                                <div class="alert ${severityClass} mb-2">
                                    <div class="d-flex justify-content-between">
                                        <div>
                                            <strong>${alert.rule_name}</strong><br>
                                            <small>${alert.message}</small>
                                        </div>
                                        <div class="text-end">
                                            <span class="badge bg-${alert.severity === 'critical' ? 'danger' : alert.severity === 'high' ? 'warning' : 'info'}">${alert.severity}</span><br>
                                            <small>${new Date(alert.created_at * 1000).toLocaleString()}</small>
                                        </div>
                                    </div>
                                </div>
                            `;
                        }
                    }
                    
                    container.innerHTML = html;
                })
                .catch(error => console.error('Error loading alerts:', error));
        }
        
        function loadLogs() {
            const level = document.getElementById('log-level-filter').value;
            const url = level ? `/api/logs?level=${level}` : '/api/logs';
            
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('Logs error:', data.error);
                        return;
                    }
                    
                    const container = document.getElementById('logs-container');
                    let html = '';
                    
                    for (const log of data.logs.slice(0, 50)) {
                        const levelClass = `log-${log.level.toLowerCase()}`;
                        const timestamp = new Date(log.timestamp * 1000).toLocaleTimeString();
                        html += `
                            <div class="log-entry ${levelClass}">
                                <span class="text-muted">${timestamp}</span>
                                <span class="badge bg-secondary">${log.level}</span>
                                <span class="text-info">${log.logger_name}</span>
                                ${log.message}
                            </div>
                        `;
                    }
                    
                    container.innerHTML = html || '<p class="text-muted">No logs available</p>';
                })
                .catch(error => console.error('Error loading logs:', error));
        }
        
        function filterLogs() {
            loadLogs();
        }
        
        function refreshDashboard() {
            showLoading();
            
            Promise.all([
                loadSystemData(),
                loadMetrics(),
                loadAlerts(),
                loadLogs()
            ]).finally(() => {
                hideLoading();
                updateLastRefresh();
            });
        }
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            refreshDashboard();
            
            // Auto-refresh every 30 seconds
            refreshInterval = setInterval(refreshDashboard, {{ config.auto_refresh * 1000 }});
        });
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', function() {
            if (refreshInterval) {
                clearInterval(refreshInterval);
            }
        });
    </script>
</body>
</html>
        """.replace("{{ config.auto_refresh * 1000 }}", str(self.config.auto_refresh * 1000))
    
    def start(self):
        """Start the dashboard server."""
        if self.running:
            logger.warning("Dashboard already running")
            return
        
        self.running = True
        
        # Start server in separate thread
        self.server_thread = threading.Thread(
            target=self._run_server,
            daemon=True,
            name="dashboard-server"
        )
        self.server_thread.start()
        
        logger.info(f"Dashboard started on http://{self.config.host}:{self.config.port}")
    
    def _run_server(self):
        """Run the Flask server."""
        try:
            self.app.run(
                host=self.config.host,
                port=self.config.port,
                debug=self.config.debug,
                use_reloader=False,
                threaded=True
            )
        except Exception as e:
            logger.error(f"Dashboard server error: {str(e)}")
    
    def stop(self):
        """Stop the dashboard server."""
        self.running = False
        logger.info("Dashboard stopped")
    
    def get_dashboard_url(self) -> str:
        """Get dashboard URL."""
        return f"http://{self.config.host}:{self.config.port}"
