"""
Real-time lineage tracker for streaming data processing.
Provides real-time tracking and updates of data lineage in streaming environments.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set, Callable, AsyncGenerator
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import threading
import time

from .kafka_streams_connector import StreamingEvent, StreamingEventType

logger = logging.getLogger(__name__)


class LineageUpdateType(Enum):
    """Types of lineage updates."""
    NODE_CREATED = "node_created"
    NODE_UPDATED = "node_updated"
    NODE_DELETED = "node_deleted"
    EDGE_CREATED = "edge_created"
    EDGE_UPDATED = "edge_updated"
    EDGE_DELETED = "edge_deleted"
    SCHEMA_CHANGED = "schema_changed"
    PARTITION_CHANGED = "partition_changed"


@dataclass
class LineageUpdate:
    """Represents a real-time lineage update."""
    update_id: str
    update_type: LineageUpdateType
    entity_id: str
    entity_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source_system: str = ""
    changes: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    related_entities: List[str] = field(default_factory=list)
    processing_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'update_id': self.update_id,
            'update_type': self.update_type.value,
            'entity_id': self.entity_id,
            'entity_type': self.entity_type,
            'timestamp': self.timestamp.isoformat(),
            'source_system': self.source_system,
            'changes': self.changes,
            'metadata': self.metadata,
            'related_entities': self.related_entities,
            'processing_time': self.processing_time,
        }


@dataclass
class RealtimeStats:
    """Statistics for real-time tracking."""
    events_processed: int = 0
    updates_generated: int = 0
    errors: int = 0
    avg_processing_time: float = 0.0
    last_event_time: Optional[datetime] = None
    active_streams: int = 0
    buffer_size: int = 0
    throughput_per_second: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'events_processed': self.events_processed,
            'updates_generated': self.updates_generated,
            'errors': self.errors,
            'avg_processing_time': self.avg_processing_time,
            'last_event_time': self.last_event_time.isoformat() if self.last_event_time else None,
            'active_streams': self.active_streams,
            'buffer_size': self.buffer_size,
            'throughput_per_second': self.throughput_per_second,
        }


class RealtimeTracker:
    """Real-time lineage tracker for streaming data."""
    
    def __init__(self, 
                 buffer_size: int = 10000,
                 batch_size: int = 100,
                 flush_interval: float = 1.0,
                 enable_deduplication: bool = True,
                 deduplication_window: int = 300):
        self.buffer_size = buffer_size
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.enable_deduplication = enable_deduplication
        self.deduplication_window = deduplication_window
        
        # Internal state
        self.running = False
        self.event_buffer: deque = deque(maxlen=buffer_size)
        self.update_buffer: deque = deque(maxlen=buffer_size)
        self.processed_events: Set[str] = set()
        self.entity_cache: Dict[str, Dict[str, Any]] = {}
        self.stats = RealtimeStats()
        
        # Event handlers
        self.event_processors: List[Callable] = []
        self.update_handlers: List[Callable] = []
        
        # Threading
        self._lock = threading.Lock()
        self._processing_task: Optional[asyncio.Task] = None
        self._flush_task: Optional[asyncio.Task] = None
        
        # Performance tracking
        self._processing_times: deque = deque(maxlen=1000)
        self._throughput_counter = 0
        self._last_throughput_time = time.time()
    
    async def start(self):
        """Start the real-time tracker."""
        if self.running:
            return
        
        self.running = True
        
        # Start processing tasks
        self._processing_task = asyncio.create_task(self._process_events())
        self._flush_task = asyncio.create_task(self._flush_updates())
        
        logger.info("Real-time tracker started")
    
    async def stop(self):
        """Stop the real-time tracker."""
        if not self.running:
            return
        
        self.running = False
        
        # Cancel tasks
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining updates
        await self._flush_all_updates()
        
        logger.info("Real-time tracker stopped")
    
    async def process_streaming_event(self, event: StreamingEvent):
        """Process a streaming event for lineage tracking."""
        if not self.running:
            return
        
        start_time = time.time()
        
        try:
            # Check for deduplication
            if self.enable_deduplication and event.event_id in self.processed_events:
                return
            
            # Add to buffer
            with self._lock:
                self.event_buffer.append(event)
                if self.enable_deduplication:
                    self.processed_events.add(event.event_id)
                    # Clean old processed events
                    if len(self.processed_events) > self.buffer_size * 2:
                        self.processed_events.clear()
            
            # Update stats
            processing_time = time.time() - start_time
            self._update_stats(processing_time)
            
        except Exception as e:
            logger.error(f"Error processing streaming event: {e}")
            with self._lock:
                self.stats.errors += 1
    
    async def add_lineage_update(self, update: LineageUpdate):
        """Add a lineage update to the buffer."""
        with self._lock:
            self.update_buffer.append(update)
            self.stats.updates_generated += 1
    
    def add_event_processor(self, processor: Callable):
        """Add an event processor function."""
        self.event_processors.append(processor)
    
    def add_update_handler(self, handler: Callable):
        """Add an update handler function."""
        self.update_handlers.append(handler)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tracker statistics."""
        with self._lock:
            return self.stats.to_dict()
    
    def get_buffer_status(self) -> Dict[str, Any]:
        """Get buffer status information."""
        with self._lock:
            return {
                'event_buffer_size': len(self.event_buffer),
                'update_buffer_size': len(self.update_buffer),
                'event_buffer_capacity': self.buffer_size,
                'update_buffer_capacity': self.buffer_size,
                'processed_events_count': len(self.processed_events),
            }
    
    async def _process_events(self):
        """Process events from the buffer."""
        while self.running:
            try:
                # Get events from buffer
                events_to_process = []
                with self._lock:
                    while self.event_buffer and len(events_to_process) < self.batch_size:
                        events_to_process.append(self.event_buffer.popleft())
                
                # Process events
                for event in events_to_process:
                    await self._process_single_event(event)
                
                # Small delay if no events
                if not events_to_process:
                    await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}")
                await asyncio.sleep(0.1)
    
    async def _process_single_event(self, event: StreamingEvent):
        """Process a single streaming event."""
        try:
            # Generate lineage updates based on event type
            updates = await self._generate_lineage_updates(event)
            
            # Add updates to buffer
            for update in updates:
                await self.add_lineage_update(update)
            
            # Call event processors
            for processor in self.event_processors:
                try:
                    if asyncio.iscoroutinefunction(processor):
                        await processor(event)
                    else:
                        processor(event)
                except Exception as e:
                    logger.error(f"Error in event processor: {e}")
            
        except Exception as e:
            logger.error(f"Error processing single event: {e}")
            with self._lock:
                self.stats.errors += 1
    
    async def _generate_lineage_updates(self, event: StreamingEvent) -> List[LineageUpdate]:
        """Generate lineage updates from streaming event."""
        updates = []
        
        try:
            # Create node update for source
            if event.source_topic:
                source_update = LineageUpdate(
                    update_id=f"{event.event_id}_source",
                    update_type=LineageUpdateType.NODE_UPDATED,
                    entity_id=event.source_topic,
                    entity_type="topic",
                    source_system="kafka",
                    changes={
                        'last_seen': event.timestamp.isoformat(),
                        'partition': event.partition,
                        'offset': event.offset,
                    },
                    metadata=event.payload,
                )
                updates.append(source_update)
            
            # Create node update for target
            if event.target_topic:
                target_update = LineageUpdate(
                    update_id=f"{event.event_id}_target",
                    update_type=LineageUpdateType.NODE_UPDATED,
                    entity_id=event.target_topic,
                    entity_type="topic",
                    source_system="kafka",
                    changes={
                        'last_seen': event.timestamp.isoformat(),
                    },
                    metadata=event.payload,
                )
                updates.append(target_update)
                
                # Create edge update
                edge_update = LineageUpdate(
                    update_id=f"{event.event_id}_edge",
                    update_type=LineageUpdateType.EDGE_UPDATED,
                    entity_id=f"{event.source_topic}->{event.target_topic}",
                    entity_type="data_flow",
                    source_system="kafka",
                    changes={
                        'last_seen': event.timestamp.isoformat(),
                        'processor': event.processor_name,
                        'application': event.application_id,
                    },
                    related_entities=[event.source_topic, event.target_topic],
                )
                updates.append(edge_update)
            
            # Handle schema changes
            if event.schema_info:
                schema_update = LineageUpdate(
                    update_id=f"{event.event_id}_schema",
                    update_type=LineageUpdateType.SCHEMA_CHANGED,
                    entity_id=event.source_topic,
                    entity_type="topic",
                    source_system="kafka",
                    changes=event.schema_info,
                    metadata={'event_type': event.event_type.value},
                )
                updates.append(schema_update)
            
        except Exception as e:
            logger.error(f"Error generating lineage updates: {e}")
        
        return updates
    
    async def _flush_updates(self):
        """Flush updates periodically."""
        while self.running:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_batch_updates()
            except Exception as e:
                logger.error(f"Error in flush loop: {e}")
    
    async def _flush_batch_updates(self):
        """Flush a batch of updates."""
        updates_to_flush = []
        
        with self._lock:
            while self.update_buffer and len(updates_to_flush) < self.batch_size:
                updates_to_flush.append(self.update_buffer.popleft())
        
        if updates_to_flush:
            await self._send_updates(updates_to_flush)
    
    async def _flush_all_updates(self):
        """Flush all remaining updates."""
        updates_to_flush = []
        
        with self._lock:
            while self.update_buffer:
                updates_to_flush.append(self.update_buffer.popleft())
        
        if updates_to_flush:
            await self._send_updates(updates_to_flush)
    
    async def _send_updates(self, updates: List[LineageUpdate]):
        """Send updates to handlers."""
        for handler in self.update_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(updates)
                else:
                    handler(updates)
            except Exception as e:
                logger.error(f"Error in update handler: {e}")
    
    def _update_stats(self, processing_time: float):
        """Update performance statistics."""
        with self._lock:
            self.stats.events_processed += 1
            self.stats.last_event_time = datetime.utcnow()
            self.stats.buffer_size = len(self.event_buffer) + len(self.update_buffer)
            
            # Update processing time
            self._processing_times.append(processing_time)
            if self._processing_times:
                self.stats.avg_processing_time = sum(self._processing_times) / len(self._processing_times)
            
            # Update throughput
            self._throughput_counter += 1
            current_time = time.time()
            if current_time - self._last_throughput_time >= 1.0:
                self.stats.throughput_per_second = self._throughput_counter / (current_time - self._last_throughput_time)
                self._throughput_counter = 0
                self._last_throughput_time = current_time


def create_realtime_tracker(
    buffer_size: int = 10000,
    batch_size: int = 100,
    flush_interval: float = 1.0,
    **kwargs
) -> RealtimeTracker:
    """Factory function to create real-time tracker."""
    return RealtimeTracker(
        buffer_size=buffer_size,
        batch_size=batch_size,
        flush_interval=flush_interval,
        **kwargs
    )
