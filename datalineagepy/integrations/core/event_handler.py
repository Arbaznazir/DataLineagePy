"""
Event handler for enterprise integrations.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime
from enum import Enum
import json
import uuid
from collections import defaultdict

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Integration event types."""
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_LOST = "connection_lost"
    CONNECTION_RESTORED = "connection_restored"
    AUTHENTICATION_SUCCESS = "authentication_success"
    AUTHENTICATION_FAILURE = "authentication_failure"
    QUERY_EXECUTED = "query_executed"
    QUERY_FAILED = "query_failed"
    METADATA_EXTRACTED = "metadata_extracted"
    LINEAGE_DISCOVERED = "lineage_discovered"
    ERROR_OCCURRED = "error_occurred"
    HEALTH_CHECK_PASSED = "health_check_passed"
    HEALTH_CHECK_FAILED = "health_check_failed"
    CONNECTOR_REGISTERED = "connector_registered"
    CONNECTOR_UNREGISTERED = "connector_unregistered"
    POOL_CONNECTION_CREATED = "pool_connection_created"
    POOL_CONNECTION_CLOSED = "pool_connection_closed"
    RETRY_ATTEMPT = "retry_attempt"
    CIRCUIT_BREAKER_OPENED = "circuit_breaker_opened"
    CIRCUIT_BREAKER_CLOSED = "circuit_breaker_closed"


class EventPriority(Enum):
    """Event priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class IntegrationEvent:
    """Integration event data structure."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.ERROR_OCCURRED
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = "unknown"
    connector_name: Optional[str] = None
    priority: EventPriority = EventPriority.NORMAL
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Exception] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'connector_name': self.connector_name,
            'priority': self.priority.value,
            'data': self.data,
            'error': str(self.error) if self.error else None,
            'context': self.context
        }
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class EventHandler:
    """Handles integration events."""
    
    def __init__(self, max_events: int = 10000):
        self.max_events = max_events
        self.events: List[IntegrationEvent] = []
        self.event_listeners: Dict[EventType, List[Callable]] = defaultdict(list)
        self.global_listeners: List[Callable] = []
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.processing_task: Optional[asyncio.Task] = None
        self.stats = {
            'total_events': 0,
            'events_by_type': defaultdict(int),
            'events_by_priority': defaultdict(int),
            'events_by_source': defaultdict(int),
            'listeners_count': 0
        }
        self.start_processing()
    
    def start_processing(self):
        """Start event processing task."""
        if not self.processing_task or self.processing_task.done():
            self.processing_task = asyncio.create_task(self._process_events())
    
    async def _process_events(self):
        """Process events from the queue."""
        while True:
            try:
                event = await self.event_queue.get()
                await self._handle_event(event)
                self.event_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}")
    
    async def _handle_event(self, event: IntegrationEvent):
        """Handle a single event."""
        try:
            # Store event
            self.events.append(event)
            
            # Maintain max events limit
            if len(self.events) > self.max_events:
                self.events = self.events[-self.max_events:]
            
            # Update statistics
            self.stats['total_events'] += 1
            self.stats['events_by_type'][event.event_type.value] += 1
            self.stats['events_by_priority'][event.priority.value] += 1
            self.stats['events_by_source'][event.source] += 1
            
            # Call specific event listeners
            listeners = self.event_listeners.get(event.event_type, [])
            for listener in listeners:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        await listener(event)
                    else:
                        listener(event)
                except Exception as e:
                    logger.error(f"Error in event listener: {e}")
            
            # Call global listeners
            for listener in self.global_listeners:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        await listener(event)
                    else:
                        listener(event)
                except Exception as e:
                    logger.error(f"Error in global event listener: {e}")
            
            # Log critical events
            if event.priority == EventPriority.CRITICAL:
                logger.critical(f"Critical event: {event.event_type.value} from {event.source}")
            elif event.priority == EventPriority.HIGH:
                logger.error(f"High priority event: {event.event_type.value} from {event.source}")
            
        except Exception as e:
            logger.error(f"Error handling event {event.event_id}: {e}")
    
    async def emit_event(self, event: IntegrationEvent):
        """Emit an event."""
        await self.event_queue.put(event)
    
    async def emit(self, 
                   event_type: EventType,
                   source: str,
                   connector_name: Optional[str] = None,
                   priority: EventPriority = EventPriority.NORMAL,
                   data: Optional[Dict[str, Any]] = None,
                   error: Optional[Exception] = None,
                   context: Optional[Dict[str, Any]] = None):
        """Emit an event with parameters."""
        event = IntegrationEvent(
            event_type=event_type,
            source=source,
            connector_name=connector_name,
            priority=priority,
            data=data or {},
            error=error,
            context=context or {}
        )
        await self.emit_event(event)
    
    def add_listener(self, event_type: EventType, listener: Callable):
        """Add event listener for specific event type."""
        self.event_listeners[event_type].append(listener)
        self.stats['listeners_count'] += 1
        logger.debug(f"Added listener for {event_type.value}")
    
    def add_global_listener(self, listener: Callable):
        """Add global event listener."""
        self.global_listeners.append(listener)
        self.stats['listeners_count'] += 1
        logger.debug("Added global event listener")
    
    def remove_listener(self, event_type: EventType, listener: Callable):
        """Remove event listener."""
        if listener in self.event_listeners[event_type]:
            self.event_listeners[event_type].remove(listener)
            self.stats['listeners_count'] -= 1
            logger.debug(f"Removed listener for {event_type.value}")
    
    def remove_global_listener(self, listener: Callable):
        """Remove global event listener."""
        if listener in self.global_listeners:
            self.global_listeners.remove(listener)
            self.stats['listeners_count'] -= 1
            logger.debug("Removed global event listener")
    
    def get_events(self, 
                   event_type: Optional[EventType] = None,
                   source: Optional[str] = None,
                   connector_name: Optional[str] = None,
                   priority: Optional[EventPriority] = None,
                   limit: Optional[int] = None) -> List[IntegrationEvent]:
        """Get events with optional filtering."""
        filtered_events = self.events
        
        if event_type:
            filtered_events = [e for e in filtered_events if e.event_type == event_type]
        
        if source:
            filtered_events = [e for e in filtered_events if e.source == source]
        
        if connector_name:
            filtered_events = [e for e in filtered_events if e.connector_name == connector_name]
        
        if priority:
            filtered_events = [e for e in filtered_events if e.priority == priority]
        
        # Sort by timestamp (newest first)
        filtered_events.sort(key=lambda e: e.timestamp, reverse=True)
        
        if limit:
            filtered_events = filtered_events[:limit]
        
        return filtered_events
    
    def get_recent_events(self, minutes: int = 60) -> List[IntegrationEvent]:
        """Get events from the last N minutes."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        return [e for e in self.events if e.timestamp >= cutoff_time]
    
    def get_error_events(self, limit: Optional[int] = None) -> List[IntegrationEvent]:
        """Get error events."""
        error_events = [e for e in self.events if e.error is not None]
        error_events.sort(key=lambda e: e.timestamp, reverse=True)
        
        if limit:
            error_events = error_events[:limit]
        
        return error_events
    
    def get_critical_events(self, limit: Optional[int] = None) -> List[IntegrationEvent]:
        """Get critical events."""
        return self.get_events(priority=EventPriority.CRITICAL, limit=limit)
    
    def clear_events(self):
        """Clear all stored events."""
        self.events.clear()
        logger.info("Cleared all events")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event handler statistics."""
        return {
            **self.stats,
            'current_events': len(self.events),
            'queue_size': self.event_queue.qsize(),
            'processing_active': self.processing_task and not self.processing_task.done()
        }
    
    async def shutdown(self):
        """Shutdown event handler."""
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        # Wait for remaining events to be processed
        await self.event_queue.join()
        
        logger.info("Event handler shutdown")


class EventLogger:
    """Logs events to various destinations."""
    
    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file
        self.file_handler = None
        
        if log_file:
            self.file_handler = logging.FileHandler(log_file)
            self.file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            )
    
    async def log_event(self, event: IntegrationEvent):
        """Log an event."""
        log_message = f"Event: {event.event_type.value} | Source: {event.source}"
        
        if event.connector_name:
            log_message += f" | Connector: {event.connector_name}"
        
        if event.error:
            log_message += f" | Error: {event.error}"
        
        if event.data:
            log_message += f" | Data: {event.data}"
        
        # Log to standard logger
        if event.priority == EventPriority.CRITICAL:
            logger.critical(log_message)
        elif event.priority == EventPriority.HIGH:
            logger.error(log_message)
        elif event.priority == EventPriority.NORMAL:
            logger.info(log_message)
        else:
            logger.debug(log_message)
        
        # Log to file if configured
        if self.file_handler:
            event_logger = logging.getLogger('integration_events')
            event_logger.addHandler(self.file_handler)
            event_logger.info(event.to_json())


class EventMetrics:
    """Collects metrics from events."""
    
    def __init__(self):
        self.metrics = {
            'connection_attempts': 0,
            'successful_connections': 0,
            'failed_connections': 0,
            'authentication_attempts': 0,
            'successful_authentications': 0,
            'failed_authentications': 0,
            'queries_executed': 0,
            'failed_queries': 0,
            'metadata_extractions': 0,
            'lineage_discoveries': 0,
            'errors': 0,
            'health_checks': 0,
            'failed_health_checks': 0
        }
    
    async def process_event(self, event: IntegrationEvent):
        """Process an event and update metrics."""
        if event.event_type == EventType.CONNECTION_ESTABLISHED:
            self.metrics['connection_attempts'] += 1
            self.metrics['successful_connections'] += 1
        
        elif event.event_type == EventType.CONNECTION_LOST:
            self.metrics['connection_attempts'] += 1
            self.metrics['failed_connections'] += 1
        
        elif event.event_type == EventType.AUTHENTICATION_SUCCESS:
            self.metrics['authentication_attempts'] += 1
            self.metrics['successful_authentications'] += 1
        
        elif event.event_type == EventType.AUTHENTICATION_FAILURE:
            self.metrics['authentication_attempts'] += 1
            self.metrics['failed_authentications'] += 1
        
        elif event.event_type == EventType.QUERY_EXECUTED:
            self.metrics['queries_executed'] += 1
        
        elif event.event_type == EventType.QUERY_FAILED:
            self.metrics['failed_queries'] += 1
        
        elif event.event_type == EventType.METADATA_EXTRACTED:
            self.metrics['metadata_extractions'] += 1
        
        elif event.event_type == EventType.LINEAGE_DISCOVERED:
            self.metrics['lineage_discoveries'] += 1
        
        elif event.event_type == EventType.ERROR_OCCURRED:
            self.metrics['errors'] += 1
        
        elif event.event_type == EventType.HEALTH_CHECK_PASSED:
            self.metrics['health_checks'] += 1
        
        elif event.event_type == EventType.HEALTH_CHECK_FAILED:
            self.metrics['failed_health_checks'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return self.metrics.copy()
    
    def get_success_rates(self) -> Dict[str, float]:
        """Get success rates for various operations."""
        rates = {}
        
        if self.metrics['connection_attempts'] > 0:
            rates['connection_success_rate'] = (
                self.metrics['successful_connections'] / self.metrics['connection_attempts']
            )
        
        if self.metrics['authentication_attempts'] > 0:
            rates['authentication_success_rate'] = (
                self.metrics['successful_authentications'] / self.metrics['authentication_attempts']
            )
        
        total_queries = self.metrics['queries_executed'] + self.metrics['failed_queries']
        if total_queries > 0:
            rates['query_success_rate'] = self.metrics['queries_executed'] / total_queries
        
        total_health_checks = self.metrics['health_checks'] + self.metrics['failed_health_checks']
        if total_health_checks > 0:
            rates['health_check_success_rate'] = self.metrics['health_checks'] / total_health_checks
        
        return rates


def create_event_handler(max_events: int = 10000) -> EventHandler:
    """Factory function to create event handler."""
    return EventHandler(max_events)


def create_event_logger(log_file: Optional[str] = None) -> EventLogger:
    """Factory function to create event logger."""
    return EventLogger(log_file)


def create_event_metrics() -> EventMetrics:
    """Factory function to create event metrics."""
    return EventMetrics()
