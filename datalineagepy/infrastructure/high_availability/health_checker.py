"""
Health Checker Implementation
Comprehensive health monitoring and service discovery.
"""

import time
import threading
import requests
import socket
import psutil
import logging
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import statistics

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class CheckType(Enum):
    """Health check types."""
    HTTP = "http"
    TCP = "tcp"
    PING = "ping"
    PROCESS = "process"
    DATABASE = "database"
    CUSTOM = "custom"


@dataclass
class HealthCheck:
    """Health check configuration."""
    name: str
    check_type: CheckType
    target: str  # URL, host:port, process name, etc.
    interval: int = 30  # seconds
    timeout: int = 10  # seconds
    retries: int = 3
    failure_threshold: int = 3
    success_threshold: int = 2
    enabled: bool = True
    
    # HTTP-specific options
    http_method: str = "GET"
    expected_status: int = 200
    expected_content: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    
    # Custom check function
    custom_check: Optional[Callable[[], bool]] = None
    
    # Metadata
    tags: Dict[str, str] = field(default_factory=dict)
    description: str = ""


@dataclass
class HealthResult:
    """Health check result."""
    check_name: str
    status: HealthStatus
    response_time: float
    timestamp: float
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class ServiceHealth:
    """Service health summary."""
    service_name: str
    overall_status: HealthStatus
    checks: Dict[str, HealthResult]
    last_updated: float
    uptime_percentage: float
    response_time_avg: float
    failure_count: int
    success_count: int


class HealthChecker:
    """
    Comprehensive health monitoring system.
    
    Features:
    - Multiple check types (HTTP, TCP, process, custom)
    - Configurable thresholds and retries
    - Service discovery integration
    - Health history and trends
    - Alerting and notifications
    - Circuit breaker integration
    """
    
    def __init__(self, check_interval: int = 30, max_history: int = 1000):
        """
        Initialize health checker.
        
        Args:
            check_interval: Default check interval in seconds
            max_history: Maximum health history entries to keep
        """
        self.check_interval = check_interval
        self.max_history = max_history
        
        # Health checks and results
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_results: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.service_health: Dict[str, ServiceHealth] = {}
        
        # Failure tracking
        self.consecutive_failures: Dict[str, int] = defaultdict(int)
        self.consecutive_successes: Dict[str, int] = defaultdict(int)
        
        # Threading
        self.lock = threading.RLock()
        self.check_threads: Dict[str, threading.Thread] = {}
        self.running = False
        
        # Callbacks
        self.status_change_callbacks: List[Callable[[str, HealthStatus, HealthStatus], None]] = []
        self.alert_callbacks: List[Callable[[str, HealthResult], None]] = []
        
        # Statistics
        self.total_checks = 0
        self.total_failures = 0
        self.start_time = time.time()
        
        logger.info("Health checker initialized")
    
    def add_health_check(self, health_check: HealthCheck) -> bool:
        """
        Add a health check.
        
        Args:
            health_check: Health check configuration
            
        Returns:
            True if check was added successfully
        """
        try:
            with self.lock:
                if health_check.name in self.health_checks:
                    logger.warning(f"Health check {health_check.name} already exists")
                    return False
                
                self.health_checks[health_check.name] = health_check
                
                # Start check thread if monitoring is running
                if self.running:
                    self._start_check_thread(health_check.name)
                
                logger.info(f"Added health check: {health_check.name} ({health_check.check_type.value})")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add health check {health_check.name}: {str(e)}")
            return False
    
    def remove_health_check(self, check_name: str) -> bool:
        """
        Remove a health check.
        
        Args:
            check_name: Name of check to remove
            
        Returns:
            True if check was removed
        """
        try:
            with self.lock:
                if check_name not in self.health_checks:
                    logger.warning(f"Health check {check_name} not found")
                    return False
                
                # Stop check thread
                if check_name in self.check_threads:
                    # Thread will stop when it sees the check is removed
                    pass
                
                # Remove check and data
                del self.health_checks[check_name]
                if check_name in self.health_results:
                    del self.health_results[check_name]
                if check_name in self.consecutive_failures:
                    del self.consecutive_failures[check_name]
                if check_name in self.consecutive_successes:
                    del self.consecutive_successes[check_name]
                
                logger.info(f"Removed health check: {check_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to remove health check {check_name}: {str(e)}")
            return False
    
    def start_monitoring(self):
        """Start health monitoring for all checks."""
        with self.lock:
            if self.running:
                logger.warning("Health monitoring already running")
                return
            
            self.running = True
            
            # Start check threads for all enabled checks
            for check_name in self.health_checks:
                if self.health_checks[check_name].enabled:
                    self._start_check_thread(check_name)
            
            logger.info(f"Started health monitoring for {len(self.health_checks)} checks")
    
    def stop_monitoring(self):
        """Stop health monitoring."""
        with self.lock:
            self.running = False
            
            # Wait for check threads to finish
            for thread in self.check_threads.values():
                if thread.is_alive():
                    thread.join(timeout=5)
            
            self.check_threads.clear()
            
            logger.info("Stopped health monitoring")
    
    def _start_check_thread(self, check_name: str):
        """Start monitoring thread for a specific check."""
        if check_name in self.check_threads and self.check_threads[check_name].is_alive():
            return
        
        thread = threading.Thread(
            target=self._check_loop,
            args=(check_name,),
            daemon=True,
            name=f"health-check-{check_name}"
        )
        thread.start()
        self.check_threads[check_name] = thread
    
    def _check_loop(self, check_name: str):
        """Health check loop for a specific check."""
        while self.running:
            try:
                with self.lock:
                    if check_name not in self.health_checks:
                        break  # Check was removed
                    
                    health_check = self.health_checks[check_name]
                
                if not health_check.enabled:
                    time.sleep(health_check.interval)
                    continue
                
                # Perform health check
                result = self._perform_health_check(health_check)
                
                # Process result
                self._process_health_result(check_name, result)
                
                # Sleep until next check
                time.sleep(health_check.interval)
                
            except Exception as e:
                logger.error(f"Health check loop error for {check_name}: {str(e)}")
                time.sleep(30)  # Longer delay on error
    
    def _perform_health_check(self, health_check: HealthCheck) -> HealthResult:
        """Perform a single health check."""
        start_time = time.time()
        
        try:
            success = False
            message = ""
            details = {}
            error = None
            
            # Perform check based on type
            if health_check.check_type == CheckType.HTTP:
                success, message, details, error = self._check_http(health_check)
            elif health_check.check_type == CheckType.TCP:
                success, message, details, error = self._check_tcp(health_check)
            elif health_check.check_type == CheckType.PING:
                success, message, details, error = self._check_ping(health_check)
            elif health_check.check_type == CheckType.PROCESS:
                success, message, details, error = self._check_process(health_check)
            elif health_check.check_type == CheckType.DATABASE:
                success, message, details, error = self._check_database(health_check)
            elif health_check.check_type == CheckType.CUSTOM:
                success, message, details, error = self._check_custom(health_check)
            else:
                success = False
                message = f"Unknown check type: {health_check.check_type}"
                error = message
            
            response_time = time.time() - start_time
            status = HealthStatus.HEALTHY if success else HealthStatus.UNHEALTHY
            
            return HealthResult(
                check_name=health_check.name,
                status=status,
                response_time=response_time,
                timestamp=time.time(),
                message=message,
                details=details,
                error=error
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return HealthResult(
                check_name=health_check.name,
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                timestamp=time.time(),
                message=f"Health check failed: {str(e)}",
                error=str(e)
            )
    
    def _check_http(self, health_check: HealthCheck) -> tuple:
        """Perform HTTP health check."""
        try:
            response = requests.request(
                method=health_check.http_method,
                url=health_check.target,
                headers=health_check.headers,
                timeout=health_check.timeout
            )
            
            # Check status code
            if response.status_code != health_check.expected_status:
                return (
                    False,
                    f"HTTP {response.status_code} (expected {health_check.expected_status})",
                    {"status_code": response.status_code, "response_size": len(response.content)},
                    f"Unexpected status code: {response.status_code}"
                )
            
            # Check content if specified
            if health_check.expected_content:
                if health_check.expected_content not in response.text:
                    return (
                        False,
                        "Expected content not found",
                        {"status_code": response.status_code, "content_length": len(response.text)},
                        "Expected content not found in response"
                    )
            
            return (
                True,
                f"HTTP {response.status_code} OK",
                {
                    "status_code": response.status_code,
                    "response_size": len(response.content),
                    "response_time": response.elapsed.total_seconds()
                },
                None
            )
            
        except requests.exceptions.Timeout:
            return (False, "HTTP timeout", {}, "Request timeout")
        except requests.exceptions.ConnectionError:
            return (False, "Connection failed", {}, "Connection error")
        except Exception as e:
            return (False, f"HTTP check failed: {str(e)}", {}, str(e))
    
    def _check_tcp(self, health_check: HealthCheck) -> tuple:
        """Perform TCP health check."""
        try:
            host, port = health_check.target.split(':')
            port = int(port)
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(health_check.timeout)
            
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                return (True, f"TCP connection to {host}:{port} successful", {"host": host, "port": port}, None)
            else:
                return (False, f"TCP connection to {host}:{port} failed", {"host": host, "port": port}, f"Connection failed with code {result}")
                
        except ValueError:
            return (False, "Invalid target format (expected host:port)", {}, "Invalid target format")
        except Exception as e:
            return (False, f"TCP check failed: {str(e)}", {}, str(e))
    
    def _check_ping(self, health_check: HealthCheck) -> tuple:
        """Perform ping health check."""
        try:
            import subprocess
            import platform
            
            # Determine ping command based on OS
            param = "-n" if platform.system().lower() == "windows" else "-c"
            command = ["ping", param, "1", health_check.target]
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=health_check.timeout
            )
            
            if result.returncode == 0:
                return (True, f"Ping to {health_check.target} successful", {"target": health_check.target}, None)
            else:
                return (False, f"Ping to {health_check.target} failed", {"target": health_check.target}, "Ping failed")
                
        except subprocess.TimeoutExpired:
            return (False, "Ping timeout", {"target": health_check.target}, "Ping timeout")
        except Exception as e:
            return (False, f"Ping check failed: {str(e)}", {}, str(e))
    
    def _check_process(self, health_check: HealthCheck) -> tuple:
        """Perform process health check."""
        try:
            process_name = health_check.target
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                if process_name.lower() in proc.info['name'].lower():
                    processes.append(proc.info)
            
            if processes:
                return (
                    True,
                    f"Process '{process_name}' found ({len(processes)} instances)",
                    {"process_count": len(processes), "processes": processes},
                    None
                )
            else:
                return (
                    False,
                    f"Process '{process_name}' not found",
                    {"process_count": 0},
                    "Process not running"
                )
                
        except Exception as e:
            return (False, f"Process check failed: {str(e)}", {}, str(e))
    
    def _check_database(self, health_check: HealthCheck) -> tuple:
        """Perform database health check."""
        try:
            # This is a simplified example - in practice, you'd have specific
            # database connection logic for different database types
            import sqlite3
            
            # For demonstration, assume target is a SQLite database path
            conn = sqlite3.connect(health_check.target, timeout=health_check.timeout)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return (True, "Database connection successful", {"database": health_check.target}, None)
            else:
                return (False, "Database query failed", {"database": health_check.target}, "Query returned no results")
                
        except Exception as e:
            return (False, f"Database check failed: {str(e)}", {}, str(e))
    
    def _check_custom(self, health_check: HealthCheck) -> tuple:
        """Perform custom health check."""
        try:
            if not health_check.custom_check:
                return (False, "No custom check function provided", {}, "Missing custom check function")
            
            result = health_check.custom_check()
            
            if isinstance(result, bool):
                if result:
                    return (True, "Custom check passed", {}, None)
                else:
                    return (False, "Custom check failed", {}, "Custom check returned False")
            elif isinstance(result, tuple) and len(result) >= 2:
                # Custom check returned (success, message, details, error)
                return result
            else:
                return (False, "Invalid custom check result", {}, "Custom check returned invalid result")
                
        except Exception as e:
            return (False, f"Custom check failed: {str(e)}", {}, str(e))
    
    def _process_health_result(self, check_name: str, result: HealthResult):
        """Process health check result and update state."""
        try:
            with self.lock:
                # Update statistics
                self.total_checks += 1
                if result.status != HealthStatus.HEALTHY:
                    self.total_failures += 1
                
                # Store result
                self.health_results[check_name].append(result)
                
                # Update failure/success counters
                if result.status == HealthStatus.HEALTHY:
                    self.consecutive_successes[check_name] += 1
                    self.consecutive_failures[check_name] = 0
                else:
                    self.consecutive_failures[check_name] += 1
                    self.consecutive_successes[check_name] = 0
                
                # Determine if status changed
                health_check = self.health_checks[check_name]
                old_status = self._get_current_status(check_name)
                new_status = self._calculate_health_status(check_name, health_check)
                
                # Update service health
                self._update_service_health(check_name, result, new_status)
                
                # Trigger callbacks if status changed
                if old_status != new_status:
                    self._trigger_status_change_callbacks(check_name, old_status, new_status)
                
                # Trigger alert callbacks for failures
                if result.status != HealthStatus.HEALTHY:
                    self._trigger_alert_callbacks(check_name, result)
                
        except Exception as e:
            logger.error(f"Failed to process health result for {check_name}: {str(e)}")
    
    def _get_current_status(self, check_name: str) -> HealthStatus:
        """Get current health status for a check."""
        if check_name in self.service_health:
            return self.service_health[check_name].overall_status
        return HealthStatus.UNKNOWN
    
    def _calculate_health_status(self, check_name: str, health_check: HealthCheck) -> HealthStatus:
        """Calculate health status based on consecutive failures/successes."""
        consecutive_failures = self.consecutive_failures[check_name]
        consecutive_successes = self.consecutive_successes[check_name]
        
        if consecutive_failures >= health_check.failure_threshold:
            return HealthStatus.UNHEALTHY
        elif consecutive_successes >= health_check.success_threshold:
            return HealthStatus.HEALTHY
        elif consecutive_failures > 0:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
    
    def _update_service_health(self, check_name: str, result: HealthResult, status: HealthStatus):
        """Update service health summary."""
        if check_name not in self.service_health:
            self.service_health[check_name] = ServiceHealth(
                service_name=check_name,
                overall_status=status,
                checks={check_name: result},
                last_updated=time.time(),
                uptime_percentage=0.0,
                response_time_avg=0.0,
                failure_count=0,
                success_count=0
            )
        
        service = self.service_health[check_name]
        service.overall_status = status
        service.checks[check_name] = result
        service.last_updated = time.time()
        
        # Calculate uptime percentage and average response time
        if check_name in self.health_results:
            results = list(self.health_results[check_name])
            if results:
                healthy_count = sum(1 for r in results if r.status == HealthStatus.HEALTHY)
                service.uptime_percentage = (healthy_count / len(results)) * 100
                service.response_time_avg = statistics.mean([r.response_time for r in results])
                service.failure_count = len(results) - healthy_count
                service.success_count = healthy_count
    
    def _trigger_status_change_callbacks(self, check_name: str, old_status: HealthStatus, new_status: HealthStatus):
        """Trigger status change callbacks."""
        for callback in self.status_change_callbacks:
            try:
                callback(check_name, old_status, new_status)
            except Exception as e:
                logger.error(f"Status change callback failed: {str(e)}")
    
    def _trigger_alert_callbacks(self, check_name: str, result: HealthResult):
        """Trigger alert callbacks."""
        for callback in self.alert_callbacks:
            try:
                callback(check_name, result)
            except Exception as e:
                logger.error(f"Alert callback failed: {str(e)}")
    
    def add_status_change_callback(self, callback: Callable[[str, HealthStatus, HealthStatus], None]):
        """Add status change callback."""
        self.status_change_callbacks.append(callback)
    
    def add_alert_callback(self, callback: Callable[[str, HealthResult], None]):
        """Add alert callback."""
        self.alert_callbacks.append(callback)
    
    def get_health_status(self, check_name: Optional[str] = None) -> Union[Dict[str, ServiceHealth], ServiceHealth]:
        """
        Get health status for specific check or all checks.
        
        Args:
            check_name: Specific check name, or None for all checks
            
        Returns:
            Service health information
        """
        with self.lock:
            if check_name:
                return self.service_health.get(check_name)
            else:
                return dict(self.service_health)
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary."""
        with self.lock:
            total_checks = len(self.health_checks)
            healthy_checks = sum(1 for s in self.service_health.values() 
                               if s.overall_status == HealthStatus.HEALTHY)
            degraded_checks = sum(1 for s in self.service_health.values() 
                                if s.overall_status == HealthStatus.DEGRADED)
            unhealthy_checks = sum(1 for s in self.service_health.values() 
                                 if s.overall_status == HealthStatus.UNHEALTHY)
            
            overall_status = HealthStatus.HEALTHY
            if unhealthy_checks > 0:
                overall_status = HealthStatus.UNHEALTHY
            elif degraded_checks > 0:
                overall_status = HealthStatus.DEGRADED
            
            uptime = time.time() - self.start_time
            
            return {
                "overall_status": overall_status.value,
                "total_checks": total_checks,
                "healthy_checks": healthy_checks,
                "degraded_checks": degraded_checks,
                "unhealthy_checks": unhealthy_checks,
                "uptime_seconds": uptime,
                "total_check_executions": self.total_checks,
                "total_failures": self.total_failures,
                "success_rate": ((self.total_checks - self.total_failures) / max(self.total_checks, 1)) * 100
            }
    
    def get_check_history(self, check_name: str, limit: int = 100) -> List[HealthResult]:
        """Get health check history for a specific check."""
        with self.lock:
            if check_name not in self.health_results:
                return []
            
            results = list(self.health_results[check_name])
            return results[-limit:] if limit > 0 else results
    
    def shutdown(self):
        """Gracefully shutdown health checker."""
        logger.info("Shutting down health checker")
        self.stop_monitoring()
        
        with self.lock:
            self.health_checks.clear()
            self.health_results.clear()
            self.service_health.clear()
            self.consecutive_failures.clear()
            self.consecutive_successes.clear()
            self.status_change_callbacks.clear()
            self.alert_callbacks.clear()
        
        logger.info("Health checker shutdown complete")
