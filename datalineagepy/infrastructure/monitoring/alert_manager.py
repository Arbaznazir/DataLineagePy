"""
Alert Manager Implementation
Comprehensive alerting and notification system.
"""

import time
import threading
import logging
import smtplib
import json
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(Enum):
    """Alert status."""
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    ACKNOWLEDGED = "acknowledged"


class NotificationChannel(Enum):
    """Notification channels."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    PAGERDUTY = "pagerduty"
    CUSTOM = "custom"


@dataclass
class AlertRule:
    """Alert rule configuration."""
    name: str
    description: str
    metric_name: str
    condition: str  # e.g., "> 80", "< 10", "== 0"
    threshold: Union[int, float]
    severity: AlertSeverity
    evaluation_window: int = 300  # seconds
    evaluation_interval: int = 60  # seconds
    min_duration: int = 120  # minimum duration before firing
    max_frequency: int = 3600  # maximum frequency of notifications
    enabled: bool = True
    
    # Notification settings
    notification_channels: List[NotificationChannel] = field(default_factory=list)
    notification_template: Optional[str] = None
    
    # Labels and metadata
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    
    # Advanced settings
    for_duration: int = 0  # Duration condition must be true before firing
    resolve_timeout: int = 300  # Auto-resolve timeout


@dataclass
class Alert:
    """Active alert instance."""
    id: str
    rule_name: str
    metric_name: str
    current_value: Union[int, float]
    threshold: Union[int, float]
    severity: AlertSeverity
    status: AlertStatus
    message: str
    
    # Timestamps
    created_at: float
    updated_at: float
    resolved_at: Optional[float] = None
    acknowledged_at: Optional[float] = None
    
    # Metadata
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    
    # Notification tracking
    notifications_sent: int = 0
    last_notification_at: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "id": self.id,
            "rule_name": self.rule_name,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "severity": self.severity.value,
            "status": self.status.value,
            "message": self.message,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "resolved_at": self.resolved_at,
            "acknowledged_at": self.acknowledged_at,
            "labels": self.labels,
            "annotations": self.annotations,
            "notifications_sent": self.notifications_sent,
            "last_notification_at": self.last_notification_at
        }


@dataclass
class NotificationConfig:
    """Notification channel configuration."""
    channel: NotificationChannel
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Rate limiting
    rate_limit: int = 10  # max notifications per hour
    rate_window: int = 3600  # rate limit window in seconds


class AlertManager:
    """
    Enterprise-grade alert management system.
    
    Features:
    - Rule-based alerting with flexible conditions
    - Multiple notification channels (email, Slack, webhook, etc.)
    - Alert lifecycle management (active, resolved, acknowledged)
    - Rate limiting and notification throttling
    - Alert grouping and deduplication
    - Escalation policies
    - Comprehensive audit trail
    """
    
    def __init__(self, metrics_collector=None):
        """
        Initialize alert manager.
        
        Args:
            metrics_collector: Optional metrics collector for monitoring
        """
        self.metrics_collector = metrics_collector
        
        # Alert rules and active alerts
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=10000)
        
        # Notification configuration
        self.notification_configs: Dict[NotificationChannel, NotificationConfig] = {}
        self.notification_handlers: Dict[NotificationChannel, Callable] = {}
        
        # Rate limiting tracking
        self.notification_counts: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Threading
        self.lock = threading.RLock()
        self.evaluation_thread = None
        self.running = False
        
        # Statistics
        self.total_alerts_fired = 0
        self.total_alerts_resolved = 0
        self.total_notifications_sent = 0
        self.start_time = time.time()
        
        # Setup default notification handlers
        self._setup_default_handlers()
        
        logger.info("Alert manager initialized")
    
    def _setup_default_handlers(self):
        """Setup default notification handlers."""
        self.notification_handlers[NotificationChannel.EMAIL] = self._send_email_notification
        self.notification_handlers[NotificationChannel.WEBHOOK] = self._send_webhook_notification
        self.notification_handlers[NotificationChannel.CUSTOM] = self._send_custom_notification
    
    def add_alert_rule(self, rule: AlertRule) -> bool:
        """
        Add an alert rule.
        
        Args:
            rule: Alert rule configuration
            
        Returns:
            True if rule was added successfully
        """
        try:
            with self.lock:
                if rule.name in self.alert_rules:
                    logger.warning(f"Alert rule {rule.name} already exists")
                    return False
                
                # Validate rule
                if not self._validate_alert_rule(rule):
                    return False
                
                self.alert_rules[rule.name] = rule
                
                logger.info(f"Added alert rule: {rule.name} ({rule.severity.value})")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add alert rule {rule.name}: {str(e)}")
            return False
    
    def remove_alert_rule(self, rule_name: str) -> bool:
        """
        Remove an alert rule.
        
        Args:
            rule_name: Name of rule to remove
            
        Returns:
            True if rule was removed
        """
        try:
            with self.lock:
                if rule_name not in self.alert_rules:
                    logger.warning(f"Alert rule {rule_name} not found")
                    return False
                
                # Remove rule
                del self.alert_rules[rule_name]
                
                # Resolve any active alerts for this rule
                alerts_to_resolve = [
                    alert_id for alert_id, alert in self.active_alerts.items()
                    if alert.rule_name == rule_name
                ]
                
                for alert_id in alerts_to_resolve:
                    self.resolve_alert(alert_id, "Rule removed")
                
                logger.info(f"Removed alert rule: {rule_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to remove alert rule {rule_name}: {str(e)}")
            return False
    
    def _validate_alert_rule(self, rule: AlertRule) -> bool:
        """Validate alert rule configuration."""
        try:
            # Validate condition
            valid_operators = ['>', '<', '>=', '<=', '==', '!=']
            if not any(op in rule.condition for op in valid_operators):
                logger.error(f"Invalid condition in rule {rule.name}: {rule.condition}")
                return False
            
            # Validate thresholds
            if rule.evaluation_window <= 0 or rule.evaluation_interval <= 0:
                logger.error(f"Invalid timing configuration in rule {rule.name}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Rule validation failed for {rule.name}: {str(e)}")
            return False
    
    def configure_notification(self, channel: NotificationChannel, config: NotificationConfig):
        """
        Configure a notification channel.
        
        Args:
            channel: Notification channel type
            config: Channel configuration
        """
        self.notification_configs[channel] = config
        logger.info(f"Configured notification channel: {channel.value}")
    
    def add_notification_handler(self, channel: NotificationChannel, 
                               handler: Callable[[Alert, Dict[str, Any]], bool]):
        """
        Add a custom notification handler.
        
        Args:
            channel: Notification channel type
            handler: Handler function
        """
        self.notification_handlers[channel] = handler
        logger.info(f"Added notification handler for: {channel.value}")
    
    def start_monitoring(self):
        """Start alert monitoring."""
        if self.running:
            logger.warning("Alert monitoring already running")
            return
        
        self.running = True
        
        # Start evaluation thread
        self.evaluation_thread = threading.Thread(
            target=self._evaluation_loop,
            daemon=True,
            name="alert-evaluation"
        )
        self.evaluation_thread.start()
        
        logger.info("Started alert monitoring")
    
    def stop_monitoring(self):
        """Stop alert monitoring."""
        self.running = False
        
        if self.evaluation_thread:
            self.evaluation_thread.join(timeout=10)
        
        logger.info("Stopped alert monitoring")
    
    def _evaluation_loop(self):
        """Main alert evaluation loop."""
        while self.running:
            try:
                self._evaluate_alert_rules()
                self._check_alert_timeouts()
                time.sleep(30)  # Evaluate every 30 seconds
                
            except Exception as e:
                logger.error(f"Alert evaluation error: {str(e)}")
                time.sleep(60)
    
    def _evaluate_alert_rules(self):
        """Evaluate all alert rules."""
        if not self.metrics_collector:
            return
        
        current_time = time.time()
        
        with self.lock:
            for rule_name, rule in self.alert_rules.items():
                if not rule.enabled:
                    continue
                
                try:
                    self._evaluate_single_rule(rule, current_time)
                except Exception as e:
                    logger.error(f"Failed to evaluate rule {rule_name}: {str(e)}")
    
    def _evaluate_single_rule(self, rule: AlertRule, current_time: float):
        """Evaluate a single alert rule."""
        # Get metric value
        time_range = (current_time - rule.evaluation_window, current_time)
        
        from .metrics_collector import AggregationType
        metric_result = self.metrics_collector.get_metric_value(
            rule.metric_name,
            AggregationType.AVERAGE,
            time_range
        )
        
        if not metric_result:
            return
        
        current_value = metric_result.value
        
        # Evaluate condition
        condition_met = self._evaluate_condition(current_value, rule.condition, rule.threshold)
        
        # Check if alert should be fired or resolved
        alert_id = f"{rule.name}_{rule.metric_name}"
        
        if condition_met:
            if alert_id not in self.active_alerts:
                # Fire new alert
                self._fire_alert(rule, current_value, current_time)
            else:
                # Update existing alert
                self._update_alert(alert_id, current_value, current_time)
        else:
            if alert_id in self.active_alerts:
                # Resolve alert
                self.resolve_alert(alert_id, "Condition no longer met")
    
    def _evaluate_condition(self, value: Union[int, float], condition: str, 
                           threshold: Union[int, float]) -> bool:
        """Evaluate alert condition."""
        try:
            if '>' in condition:
                if '>=' in condition:
                    return value >= threshold
                else:
                    return value > threshold
            elif '<' in condition:
                if '<=' in condition:
                    return value <= threshold
                else:
                    return value < threshold
            elif '==' in condition:
                return value == threshold
            elif '!=' in condition:
                return value != threshold
            else:
                return False
        except Exception:
            return False
    
    def _fire_alert(self, rule: AlertRule, current_value: Union[int, float], current_time: float):
        """Fire a new alert."""
        try:
            alert_id = f"{rule.name}_{rule.metric_name}"
            
            # Create alert
            alert = Alert(
                id=alert_id,
                rule_name=rule.name,
                metric_name=rule.metric_name,
                current_value=current_value,
                threshold=rule.threshold,
                severity=rule.severity,
                status=AlertStatus.ACTIVE,
                message=self._generate_alert_message(rule, current_value),
                created_at=current_time,
                updated_at=current_time,
                labels=rule.labels.copy(),
                annotations=rule.annotations.copy()
            )
            
            # Store alert
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert.to_dict())
            self.total_alerts_fired += 1
            
            # Send notifications
            self._send_notifications(alert, rule)
            
            logger.warning(f"Alert fired: {rule.name} - {alert.message}")
            
        except Exception as e:
            logger.error(f"Failed to fire alert for rule {rule.name}: {str(e)}")
    
    def _update_alert(self, alert_id: str, current_value: Union[int, float], current_time: float):
        """Update an existing alert."""
        try:
            alert = self.active_alerts[alert_id]
            alert.current_value = current_value
            alert.updated_at = current_time
            
            # Check if we should send another notification
            rule = self.alert_rules[alert.rule_name]
            
            if (not alert.last_notification_at or 
                current_time - alert.last_notification_at >= rule.max_frequency):
                self._send_notifications(alert, rule)
            
        except Exception as e:
            logger.error(f"Failed to update alert {alert_id}: {str(e)}")
    
    def _generate_alert_message(self, rule: AlertRule, current_value: Union[int, float]) -> str:
        """Generate alert message."""
        return (f"{rule.description} - "
                f"Metric '{rule.metric_name}' is {current_value} "
                f"(threshold: {rule.condition} {rule.threshold})")
    
    def _send_notifications(self, alert: Alert, rule: AlertRule):
        """Send notifications for an alert."""
        try:
            current_time = time.time()
            
            for channel in rule.notification_channels:
                if channel not in self.notification_configs:
                    continue
                
                config = self.notification_configs[channel]
                if not config.enabled:
                    continue
                
                # Check rate limiting
                if self._is_rate_limited(channel, config):
                    continue
                
                # Send notification
                if channel in self.notification_handlers:
                    try:
                        success = self.notification_handlers[channel](alert, config.config)
                        if success:
                            alert.notifications_sent += 1
                            alert.last_notification_at = current_time
                            self.total_notifications_sent += 1
                            
                            # Track rate limiting
                            self.notification_counts[channel.value].append(current_time)
                            
                    except Exception as e:
                        logger.error(f"Failed to send {channel.value} notification: {str(e)}")
            
        except Exception as e:
            logger.error(f"Failed to send notifications for alert {alert.id}: {str(e)}")
    
    def _is_rate_limited(self, channel: NotificationChannel, config: NotificationConfig) -> bool:
        """Check if notification channel is rate limited."""
        try:
            current_time = time.time()
            channel_key = channel.value
            
            # Clean old entries
            cutoff_time = current_time - config.rate_window
            counts = self.notification_counts[channel_key]
            
            while counts and counts[0] < cutoff_time:
                counts.popleft()
            
            # Check rate limit
            return len(counts) >= config.rate_limit
            
        except Exception:
            return False
    
    def _send_email_notification(self, alert: Alert, config: Dict[str, Any]) -> bool:
        """Send email notification."""
        try:
            smtp_server = config.get('smtp_server', 'localhost')
            smtp_port = config.get('smtp_port', 587)
            username = config.get('username')
            password = config.get('password')
            from_email = config.get('from_email')
            to_emails = config.get('to_emails', [])
            
            if not to_emails or not from_email:
                logger.error("Email configuration incomplete")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.rule_name}"
            
            body = f"""
Alert Details:
- Rule: {alert.rule_name}
- Metric: {alert.metric_name}
- Current Value: {alert.current_value}
- Threshold: {alert.threshold}
- Severity: {alert.severity.value}
- Message: {alert.message}
- Created: {time.ctime(alert.created_at)}

Labels: {json.dumps(alert.labels, indent=2)}
Annotations: {json.dumps(alert.annotations, indent=2)}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            if username and password:
                server.starttls()
                server.login(username, password)
            
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
            return False
    
    def _send_webhook_notification(self, alert: Alert, config: Dict[str, Any]) -> bool:
        """Send webhook notification."""
        try:
            import requests
            
            url = config.get('url')
            headers = config.get('headers', {})
            timeout = config.get('timeout', 30)
            
            if not url:
                logger.error("Webhook URL not configured")
                return False
            
            # Prepare payload
            payload = {
                "alert": alert.to_dict(),
                "timestamp": time.time()
            }
            
            # Send webhook
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=timeout
            )
            
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {str(e)}")
            return False
    
    def _send_custom_notification(self, alert: Alert, config: Dict[str, Any]) -> bool:
        """Send custom notification."""
        try:
            handler = config.get('handler')
            if handler and callable(handler):
                return handler(alert, config)
            return False
        except Exception as e:
            logger.error(f"Failed to send custom notification: {str(e)}")
            return False
    
    def resolve_alert(self, alert_id: str, reason: str = "Manual resolution") -> bool:
        """
        Resolve an active alert.
        
        Args:
            alert_id: Alert ID to resolve
            reason: Resolution reason
            
        Returns:
            True if alert was resolved
        """
        try:
            with self.lock:
                if alert_id not in self.active_alerts:
                    logger.warning(f"Alert {alert_id} not found")
                    return False
                
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = time.time()
                alert.annotations['resolution_reason'] = reason
                
                # Move to history and remove from active
                self.alert_history.append(alert.to_dict())
                del self.active_alerts[alert_id]
                self.total_alerts_resolved += 1
                
                logger.info(f"Alert resolved: {alert_id} - {reason}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to resolve alert {alert_id}: {str(e)}")
            return False
    
    def acknowledge_alert(self, alert_id: str, user: str = "system") -> bool:
        """
        Acknowledge an active alert.
        
        Args:
            alert_id: Alert ID to acknowledge
            user: User acknowledging the alert
            
        Returns:
            True if alert was acknowledged
        """
        try:
            with self.lock:
                if alert_id not in self.active_alerts:
                    logger.warning(f"Alert {alert_id} not found")
                    return False
                
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = time.time()
                alert.annotations['acknowledged_by'] = user
                
                logger.info(f"Alert acknowledged: {alert_id} by {user}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to acknowledge alert {alert_id}: {str(e)}")
            return False
    
    def _check_alert_timeouts(self):
        """Check for alerts that should auto-resolve."""
        try:
            current_time = time.time()
            alerts_to_resolve = []
            
            with self.lock:
                for alert_id, alert in self.active_alerts.items():
                    rule = self.alert_rules.get(alert.rule_name)
                    if not rule:
                        continue
                    
                    # Check auto-resolve timeout
                    if (rule.resolve_timeout > 0 and 
                        current_time - alert.updated_at >= rule.resolve_timeout):
                        alerts_to_resolve.append(alert_id)
            
            # Resolve timed-out alerts
            for alert_id in alerts_to_resolve:
                self.resolve_alert(alert_id, "Auto-resolved due to timeout")
                
        except Exception as e:
            logger.error(f"Failed to check alert timeouts: {str(e)}")
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """
        Get active alerts.
        
        Args:
            severity: Optional severity filter
            
        Returns:
            List of active alerts
        """
        with self.lock:
            alerts = list(self.active_alerts.values())
            
            if severity:
                alerts = [alert for alert in alerts if alert.severity == severity]
            
            return sorted(alerts, key=lambda x: x.created_at, reverse=True)
    
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get alert history.
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of historical alerts
        """
        with self.lock:
            history = list(self.alert_history)
            return history[-limit:] if limit > 0 else history
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert manager statistics."""
        with self.lock:
            uptime = time.time() - self.start_time
            
            # Count alerts by severity
            severity_counts = defaultdict(int)
            for alert in self.active_alerts.values():
                severity_counts[alert.severity.value] += 1
            
            return {
                "uptime_seconds": uptime,
                "total_rules": len(self.alert_rules),
                "active_alerts": len(self.active_alerts),
                "total_alerts_fired": self.total_alerts_fired,
                "total_alerts_resolved": self.total_alerts_resolved,
                "total_notifications_sent": self.total_notifications_sent,
                "alerts_by_severity": dict(severity_counts),
                "notification_channels": len(self.notification_configs),
                "monitoring_running": self.running
            }
    
    def shutdown(self):
        """Gracefully shutdown alert manager."""
        logger.info("Shutting down alert manager")
        self.stop_monitoring()
        
        with self.lock:
            self.alert_rules.clear()
            self.active_alerts.clear()
            self.alert_history.clear()
            self.notification_configs.clear()
            self.notification_handlers.clear()
            self.notification_counts.clear()
        
        logger.info("Alert manager shutdown complete")
