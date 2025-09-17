"""
Horizontal Scaler Implementation
Auto-scaling infrastructure for dynamic resource management.
"""

import time
import threading
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import statistics

logger = logging.getLogger(__name__)


class ScalingDirection(Enum):
    """Scaling direction."""
    UP = "up"
    DOWN = "down"
    NONE = "none"


class ScalingTrigger(Enum):
    """Scaling trigger types."""
    CPU_UTILIZATION = "cpu_utilization"
    MEMORY_UTILIZATION = "memory_utilization"
    REQUEST_RATE = "request_rate"
    RESPONSE_TIME = "response_time"
    QUEUE_LENGTH = "queue_length"
    CUSTOM_METRIC = "custom_metric"


@dataclass
class ScalingRule:
    """Scaling rule configuration."""
    trigger: ScalingTrigger
    scale_up_threshold: float
    scale_down_threshold: float
    scale_up_adjustment: int = 1
    scale_down_adjustment: int = 1
    cooldown_period: int = 300  # seconds
    evaluation_periods: int = 2
    metric_name: Optional[str] = None
    enabled: bool = True


@dataclass
class ScalingEvent:
    """Scaling event record."""
    timestamp: float
    direction: ScalingDirection
    trigger: ScalingTrigger
    old_capacity: int
    new_capacity: int
    metric_value: float
    threshold: float
    reason: str


@dataclass
class InstanceMetrics:
    """Instance performance metrics."""
    instance_id: str
    cpu_utilization: float = 0.0
    memory_utilization: float = 0.0
    request_rate: float = 0.0
    response_time: float = 0.0
    queue_length: int = 0
    custom_metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def get_metric_value(self, trigger: ScalingTrigger, metric_name: Optional[str] = None) -> float:
        """Get metric value by trigger type."""
        if trigger == ScalingTrigger.CPU_UTILIZATION:
            return self.cpu_utilization
        elif trigger == ScalingTrigger.MEMORY_UTILIZATION:
            return self.memory_utilization
        elif trigger == ScalingTrigger.REQUEST_RATE:
            return self.request_rate
        elif trigger == ScalingTrigger.RESPONSE_TIME:
            return self.response_time
        elif trigger == ScalingTrigger.QUEUE_LENGTH:
            return float(self.queue_length)
        elif trigger == ScalingTrigger.CUSTOM_METRIC and metric_name:
            return self.custom_metrics.get(metric_name, 0.0)
        return 0.0


class HorizontalScaler:
    """
    Horizontal auto-scaler for dynamic capacity management.
    
    Features:
    - Multiple scaling triggers (CPU, memory, request rate, etc.)
    - Configurable scaling rules and thresholds
    - Cooldown periods to prevent flapping
    - Predictive scaling based on trends
    - Integration with container orchestrators
    - Comprehensive metrics and logging
    """
    
    def __init__(self, min_instances: int = 1, max_instances: int = 10,
                 default_instances: int = 2, check_interval: int = 60):
        """
        Initialize horizontal scaler.
        
        Args:
            min_instances: Minimum number of instances
            max_instances: Maximum number of instances
            default_instances: Default number of instances
            check_interval: Scaling check interval in seconds
        """
        self.min_instances = min_instances
        self.max_instances = max_instances
        self.current_instances = default_instances
        self.desired_instances = default_instances
        self.check_interval = check_interval
        
        # Scaling configuration
        self.scaling_rules: List[ScalingRule] = []
        self.scaling_enabled = True
        
        # Metrics and history
        self.instance_metrics: Dict[str, InstanceMetrics] = {}
        self.metrics_history: deque = deque(maxlen=1000)
        self.scaling_events: deque = deque(maxlen=100)
        
        # Cooldown tracking
        self.last_scale_up_time = 0
        self.last_scale_down_time = 0
        
        # Threading
        self.lock = threading.RLock()
        self.scaling_thread = None
        self.running = False
        
        # Callbacks
        self.scale_up_callback: Optional[Callable[[int], bool]] = None
        self.scale_down_callback: Optional[Callable[[int], bool]] = None
        self.metrics_callback: Optional[Callable[[], Dict[str, InstanceMetrics]]] = None
        
        # Statistics
        self.total_scale_ups = 0
        self.total_scale_downs = 0
        self.start_time = time.time()
        
        # Add default scaling rules
        self._add_default_rules()
        
        logger.info(f"Horizontal scaler initialized: {min_instances}-{max_instances} instances")
    
    def _add_default_rules(self):
        """Add default scaling rules."""
        # CPU-based scaling
        self.add_scaling_rule(ScalingRule(
            trigger=ScalingTrigger.CPU_UTILIZATION,
            scale_up_threshold=70.0,
            scale_down_threshold=30.0,
            scale_up_adjustment=2,
            scale_down_adjustment=1,
            cooldown_period=300,
            evaluation_periods=2
        ))
        
        # Memory-based scaling
        self.add_scaling_rule(ScalingRule(
            trigger=ScalingTrigger.MEMORY_UTILIZATION,
            scale_up_threshold=80.0,
            scale_down_threshold=40.0,
            scale_up_adjustment=1,
            scale_down_adjustment=1,
            cooldown_period=300,
            evaluation_periods=3
        ))
        
        # Request rate-based scaling
        self.add_scaling_rule(ScalingRule(
            trigger=ScalingTrigger.REQUEST_RATE,
            scale_up_threshold=100.0,  # requests per second per instance
            scale_down_threshold=20.0,
            scale_up_adjustment=2,
            scale_down_adjustment=1,
            cooldown_period=180,
            evaluation_periods=2
        ))
    
    def add_scaling_rule(self, rule: ScalingRule) -> bool:
        """
        Add a scaling rule.
        
        Args:
            rule: Scaling rule to add
            
        Returns:
            True if rule was added successfully
        """
        try:
            with self.lock:
                self.scaling_rules.append(rule)
                logger.info(f"Added scaling rule: {rule.trigger.value}")
                return True
        except Exception as e:
            logger.error(f"Failed to add scaling rule: {str(e)}")
            return False
    
    def remove_scaling_rule(self, trigger: ScalingTrigger, metric_name: Optional[str] = None) -> bool:
        """
        Remove a scaling rule.
        
        Args:
            trigger: Trigger type to remove
            metric_name: Metric name for custom triggers
            
        Returns:
            True if rule was removed
        """
        try:
            with self.lock:
                initial_count = len(self.scaling_rules)
                self.scaling_rules = [
                    rule for rule in self.scaling_rules
                    if not (rule.trigger == trigger and rule.metric_name == metric_name)
                ]
                removed = len(self.scaling_rules) < initial_count
                if removed:
                    logger.info(f"Removed scaling rule: {trigger.value}")
                return removed
        except Exception as e:
            logger.error(f"Failed to remove scaling rule: {str(e)}")
            return False
    
    def update_instance_metrics(self, instance_id: str, metrics: InstanceMetrics):
        """
        Update metrics for an instance.
        
        Args:
            instance_id: Instance identifier
            metrics: Instance metrics
        """
        try:
            with self.lock:
                self.instance_metrics[instance_id] = metrics
                self.metrics_history.append({
                    'timestamp': time.time(),
                    'instance_count': self.current_instances,
                    'metrics': dict(self.instance_metrics)
                })
        except Exception as e:
            logger.error(f"Failed to update metrics for {instance_id}: {str(e)}")
    
    def start_auto_scaling(self, scale_up_callback: Callable[[int], bool],
                          scale_down_callback: Callable[[int], bool],
                          metrics_callback: Optional[Callable[[], Dict[str, InstanceMetrics]]] = None):
        """
        Start auto-scaling with callbacks.
        
        Args:
            scale_up_callback: Function to scale up instances
            scale_down_callback: Function to scale down instances
            metrics_callback: Function to get current metrics
        """
        self.scale_up_callback = scale_up_callback
        self.scale_down_callback = scale_down_callback
        self.metrics_callback = metrics_callback
        
        self.running = True
        self.scaling_thread = threading.Thread(
            target=self._scaling_loop,
            daemon=True
        )
        self.scaling_thread.start()
        
        logger.info("Auto-scaling started")
    
    def stop_auto_scaling(self):
        """Stop auto-scaling."""
        self.running = False
        if self.scaling_thread:
            self.scaling_thread.join(timeout=10)
        
        logger.info("Auto-scaling stopped")
    
    def _scaling_loop(self):
        """Main scaling loop running in background thread."""
        while self.running:
            try:
                # Get current metrics
                if self.metrics_callback:
                    current_metrics = self.metrics_callback()
                    for instance_id, metrics in current_metrics.items():
                        self.update_instance_metrics(instance_id, metrics)
                
                # Evaluate scaling decisions
                self._evaluate_scaling()
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Scaling loop error: {str(e)}")
                time.sleep(30)  # Longer delay on error
    
    def _evaluate_scaling(self):
        """Evaluate whether scaling is needed."""
        if not self.scaling_enabled or not self.instance_metrics:
            return
        
        current_time = time.time()
        
        # Calculate aggregate metrics
        aggregate_metrics = self._calculate_aggregate_metrics()
        
        # Evaluate each scaling rule
        scaling_decisions = []
        
        for rule in self.scaling_rules:
            if not rule.enabled:
                continue
            
            decision = self._evaluate_scaling_rule(rule, aggregate_metrics, current_time)
            if decision != ScalingDirection.NONE:
                scaling_decisions.append((rule, decision, aggregate_metrics))
        
        # Apply scaling decisions
        if scaling_decisions:
            self._apply_scaling_decisions(scaling_decisions, current_time)
    
    def _calculate_aggregate_metrics(self) -> InstanceMetrics:
        """Calculate aggregate metrics across all instances."""
        if not self.instance_metrics:
            return InstanceMetrics("aggregate")
        
        metrics_list = list(self.instance_metrics.values())
        
        # Calculate averages
        cpu_avg = statistics.mean([m.cpu_utilization for m in metrics_list])
        memory_avg = statistics.mean([m.memory_utilization for m in metrics_list])
        response_time_avg = statistics.mean([m.response_time for m in metrics_list])
        
        # Calculate totals
        request_rate_total = sum([m.request_rate for m in metrics_list])
        queue_length_total = sum([m.queue_length for m in metrics_list])
        
        # Aggregate custom metrics
        custom_metrics = {}
        all_custom_keys = set()
        for metrics in metrics_list:
            all_custom_keys.update(metrics.custom_metrics.keys())
        
        for key in all_custom_keys:
            values = [m.custom_metrics.get(key, 0.0) for m in metrics_list]
            custom_metrics[key] = statistics.mean(values)
        
        return InstanceMetrics(
            instance_id="aggregate",
            cpu_utilization=cpu_avg,
            memory_utilization=memory_avg,
            request_rate=request_rate_total,
            response_time=response_time_avg,
            queue_length=queue_length_total,
            custom_metrics=custom_metrics
        )
    
    def _evaluate_scaling_rule(self, rule: ScalingRule, metrics: InstanceMetrics,
                              current_time: float) -> ScalingDirection:
        """Evaluate a single scaling rule."""
        try:
            metric_value = metrics.get_metric_value(rule.trigger, rule.metric_name)
            
            # Check cooldown periods
            scale_up_cooldown = current_time - self.last_scale_up_time < rule.cooldown_period
            scale_down_cooldown = current_time - self.last_scale_down_time < rule.cooldown_period
            
            # Evaluate thresholds
            if (metric_value > rule.scale_up_threshold and 
                not scale_up_cooldown and 
                self.current_instances < self.max_instances):
                
                # Check evaluation periods
                if self._check_evaluation_periods(rule, metrics, "up"):
                    return ScalingDirection.UP
            
            elif (metric_value < rule.scale_down_threshold and 
                  not scale_down_cooldown and 
                  self.current_instances > self.min_instances):
                
                # Check evaluation periods
                if self._check_evaluation_periods(rule, metrics, "down"):
                    return ScalingDirection.DOWN
            
            return ScalingDirection.NONE
            
        except Exception as e:
            logger.error(f"Failed to evaluate scaling rule {rule.trigger.value}: {str(e)}")
            return ScalingDirection.NONE
    
    def _check_evaluation_periods(self, rule: ScalingRule, current_metrics: InstanceMetrics,
                                 direction: str) -> bool:
        """Check if metric has been above/below threshold for required periods."""
        if rule.evaluation_periods <= 1:
            return True
        
        # Get recent metrics history
        recent_history = list(self.metrics_history)[-rule.evaluation_periods:]
        if len(recent_history) < rule.evaluation_periods:
            return False
        
        threshold = (rule.scale_up_threshold if direction == "up" 
                    else rule.scale_down_threshold)
        
        # Check if all recent periods meet the threshold
        for history_entry in recent_history:
            if 'metrics' not in history_entry:
                continue
            
            # Calculate aggregate for this historical point
            historical_metrics = self._calculate_historical_aggregate(history_entry['metrics'])
            metric_value = historical_metrics.get_metric_value(rule.trigger, rule.metric_name)
            
            if direction == "up" and metric_value <= threshold:
                return False
            elif direction == "down" and metric_value >= threshold:
                return False
        
        return True
    
    def _calculate_historical_aggregate(self, historical_metrics: Dict[str, InstanceMetrics]) -> InstanceMetrics:
        """Calculate aggregate metrics from historical data."""
        if not historical_metrics:
            return InstanceMetrics("historical_aggregate")
        
        metrics_list = list(historical_metrics.values())
        
        cpu_avg = statistics.mean([m.cpu_utilization for m in metrics_list])
        memory_avg = statistics.mean([m.memory_utilization for m in metrics_list])
        response_time_avg = statistics.mean([m.response_time for m in metrics_list])
        request_rate_total = sum([m.request_rate for m in metrics_list])
        queue_length_total = sum([m.queue_length for m in metrics_list])
        
        return InstanceMetrics(
            instance_id="historical_aggregate",
            cpu_utilization=cpu_avg,
            memory_utilization=memory_avg,
            request_rate=request_rate_total,
            response_time=response_time_avg,
            queue_length=queue_length_total
        )
    
    def _apply_scaling_decisions(self, decisions: List, current_time: float):
        """Apply scaling decisions."""
        # Prioritize scale-up decisions
        scale_up_decisions = [d for d in decisions if d[1] == ScalingDirection.UP]
        scale_down_decisions = [d for d in decisions if d[1] == ScalingDirection.DOWN]
        
        if scale_up_decisions:
            self._execute_scale_up(scale_up_decisions, current_time)
        elif scale_down_decisions:
            self._execute_scale_down(scale_down_decisions, current_time)
    
    def _execute_scale_up(self, decisions: List, current_time: float):
        """Execute scale-up operation."""
        try:
            # Calculate total adjustment needed
            total_adjustment = max([rule.scale_up_adjustment for rule, _, _ in decisions])
            new_capacity = min(self.current_instances + total_adjustment, self.max_instances)
            
            if new_capacity <= self.current_instances:
                return
            
            # Execute scale-up
            if self.scale_up_callback and self.scale_up_callback(new_capacity):
                old_capacity = self.current_instances
                self.current_instances = new_capacity
                self.desired_instances = new_capacity
                self.last_scale_up_time = current_time
                self.total_scale_ups += 1
                
                # Record scaling event
                primary_rule = decisions[0][0]
                primary_metrics = decisions[0][2]
                metric_value = primary_metrics.get_metric_value(primary_rule.trigger, primary_rule.metric_name)
                
                event = ScalingEvent(
                    timestamp=current_time,
                    direction=ScalingDirection.UP,
                    trigger=primary_rule.trigger,
                    old_capacity=old_capacity,
                    new_capacity=new_capacity,
                    metric_value=metric_value,
                    threshold=primary_rule.scale_up_threshold,
                    reason=f"{primary_rule.trigger.value} exceeded threshold"
                )
                
                self.scaling_events.append(event)
                
                logger.info(f"Scaled up from {old_capacity} to {new_capacity} instances "
                           f"({primary_rule.trigger.value}: {metric_value:.2f} > {primary_rule.scale_up_threshold})")
            
        except Exception as e:
            logger.error(f"Failed to execute scale-up: {str(e)}")
    
    def _execute_scale_down(self, decisions: List, current_time: float):
        """Execute scale-down operation."""
        try:
            # Calculate total adjustment needed
            total_adjustment = max([rule.scale_down_adjustment for rule, _, _ in decisions])
            new_capacity = max(self.current_instances - total_adjustment, self.min_instances)
            
            if new_capacity >= self.current_instances:
                return
            
            # Execute scale-down
            if self.scale_down_callback and self.scale_down_callback(new_capacity):
                old_capacity = self.current_instances
                self.current_instances = new_capacity
                self.desired_instances = new_capacity
                self.last_scale_down_time = current_time
                self.total_scale_downs += 1
                
                # Record scaling event
                primary_rule = decisions[0][0]
                primary_metrics = decisions[0][2]
                metric_value = primary_metrics.get_metric_value(primary_rule.trigger, primary_rule.metric_name)
                
                event = ScalingEvent(
                    timestamp=current_time,
                    direction=ScalingDirection.DOWN,
                    trigger=primary_rule.trigger,
                    old_capacity=old_capacity,
                    new_capacity=new_capacity,
                    metric_value=metric_value,
                    threshold=primary_rule.scale_down_threshold,
                    reason=f"{primary_rule.trigger.value} below threshold"
                )
                
                self.scaling_events.append(event)
                
                logger.info(f"Scaled down from {old_capacity} to {new_capacity} instances "
                           f"({primary_rule.trigger.value}: {metric_value:.2f} < {primary_rule.scale_down_threshold})")
            
        except Exception as e:
            logger.error(f"Failed to execute scale-down: {str(e)}")
    
    def manual_scale(self, target_instances: int, reason: str = "Manual scaling") -> bool:
        """
        Manually scale to target instance count.
        
        Args:
            target_instances: Target number of instances
            reason: Reason for manual scaling
            
        Returns:
            True if scaling was successful
        """
        try:
            with self.lock:
                if target_instances < self.min_instances or target_instances > self.max_instances:
                    logger.error(f"Target instances {target_instances} outside allowed range "
                               f"({self.min_instances}-{self.max_instances})")
                    return False
                
                if target_instances == self.current_instances:
                    logger.info(f"Already at target capacity: {target_instances}")
                    return True
                
                old_capacity = self.current_instances
                current_time = time.time()
                
                # Execute scaling
                success = False
                if target_instances > self.current_instances:
                    success = self.scale_up_callback and self.scale_up_callback(target_instances)
                    direction = ScalingDirection.UP
                else:
                    success = self.scale_down_callback and self.scale_down_callback(target_instances)
                    direction = ScalingDirection.DOWN
                
                if success:
                    self.current_instances = target_instances
                    self.desired_instances = target_instances
                    
                    # Record manual scaling event
                    event = ScalingEvent(
                        timestamp=current_time,
                        direction=direction,
                        trigger=ScalingTrigger.CUSTOM_METRIC,
                        old_capacity=old_capacity,
                        new_capacity=target_instances,
                        metric_value=0.0,
                        threshold=0.0,
                        reason=reason
                    )
                    
                    self.scaling_events.append(event)
                    
                    logger.info(f"Manual scaling: {old_capacity} -> {target_instances} instances ({reason})")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Manual scaling failed: {str(e)}")
            return False
    
    def get_scaling_stats(self) -> Dict[str, Any]:
        """Get scaling statistics."""
        with self.lock:
            uptime = time.time() - self.start_time
            
            recent_events = list(self.scaling_events)[-10:]
            
            return {
                "current_instances": self.current_instances,
                "desired_instances": self.desired_instances,
                "min_instances": self.min_instances,
                "max_instances": self.max_instances,
                "scaling_enabled": self.scaling_enabled,
                "uptime_seconds": uptime,
                "total_scale_ups": self.total_scale_ups,
                "total_scale_downs": self.total_scale_downs,
                "total_scaling_events": len(self.scaling_events),
                "active_rules": len([r for r in self.scaling_rules if r.enabled]),
                "recent_events": [
                    {
                        "timestamp": event.timestamp,
                        "direction": event.direction.value,
                        "trigger": event.trigger.value,
                        "old_capacity": event.old_capacity,
                        "new_capacity": event.new_capacity,
                        "reason": event.reason
                    }
                    for event in recent_events
                ]
            }
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current instance metrics."""
        with self.lock:
            if not self.instance_metrics:
                return {}
            
            aggregate = self._calculate_aggregate_metrics()
            
            return {
                "aggregate_metrics": {
                    "cpu_utilization": aggregate.cpu_utilization,
                    "memory_utilization": aggregate.memory_utilization,
                    "request_rate": aggregate.request_rate,
                    "response_time": aggregate.response_time,
                    "queue_length": aggregate.queue_length,
                    "custom_metrics": aggregate.custom_metrics
                },
                "instance_metrics": {
                    instance_id: {
                        "cpu_utilization": metrics.cpu_utilization,
                        "memory_utilization": metrics.memory_utilization,
                        "request_rate": metrics.request_rate,
                        "response_time": metrics.response_time,
                        "queue_length": metrics.queue_length,
                        "timestamp": metrics.timestamp
                    }
                    for instance_id, metrics in self.instance_metrics.items()
                }
            }
    
    def enable_scaling(self):
        """Enable auto-scaling."""
        with self.lock:
            self.scaling_enabled = True
            logger.info("Auto-scaling enabled")
    
    def disable_scaling(self):
        """Disable auto-scaling."""
        with self.lock:
            self.scaling_enabled = False
            logger.info("Auto-scaling disabled")
    
    def shutdown(self):
        """Gracefully shutdown the scaler."""
        logger.info("Shutting down horizontal scaler")
        self.stop_auto_scaling()
        
        with self.lock:
            self.instance_metrics.clear()
            self.metrics_history.clear()
            self.scaling_events.clear()
            self.scaling_rules.clear()
        
        logger.info("Horizontal scaler shutdown complete")
