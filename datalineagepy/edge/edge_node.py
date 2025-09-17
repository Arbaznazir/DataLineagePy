"""
Edge Node Implementation for DataLineagePy

Provides edge computing capabilities with offline support, local processing,
and synchronization with central systems.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from threading import Lock
import hashlib
import os
import sqlite3
import gzip
import time

logger = logging.getLogger(__name__)

class EdgeNodeStatus(Enum):
    """Edge node status enumeration."""
    INITIALIZING = "initializing"
    ONLINE = "online"
    OFFLINE = "offline"
    SYNCING = "syncing"
    ERROR = "error"
    SHUTDOWN = "shutdown"

class EdgeCapability(Enum):
    """Edge node capability enumeration."""
    LINEAGE_TRACKING = "lineage_tracking"
    DATA_PROCESSING = "data_processing"
    STORAGE = "storage"
    ANALYTICS = "analytics"
    MONITORING = "monitoring"
    ALERTING = "alerting"
    CACHING = "caching"
    TRANSFORMATION = "transformation"

@dataclass
class EdgeNodeConfig:
    """Edge node configuration."""
    node_id: Optional[str] = None
    node_name: str = "edge-node"
    location: str = "unknown"
    capabilities: List[str] = field(default_factory=lambda: ["lineage_tracking", "data_processing", "storage"])
    max_storage_mb: int = 1024
    max_memory_mb: int = 512
    heartbeat_interval: int = 30
    sync_interval: int = 300
    offline_mode: bool = True
    compression_enabled: bool = True
    encryption_enabled: bool = True
    central_endpoint: Optional[str] = None
    auth_token: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EdgeEvent:
    """Represents an edge event."""
    id: str
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    node_id: str
    processed: bool = False
    synced: bool = False
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "node_id": self.node_id,
            "processed": self.processed,
            "synced": self.synced,
            "retry_count": self.retry_count,
            "metadata": self.metadata
        }

@dataclass
class EdgeMetrics:
    """Edge node metrics."""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    storage_usage: float = 0.0
    network_latency: float = 0.0
    events_processed: int = 0
    events_synced: int = 0
    errors: int = 0
    uptime: timedelta = field(default_factory=lambda: timedelta(0))
    last_sync: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "storage_usage": self.storage_usage,
            "network_latency": self.network_latency,
            "events_processed": self.events_processed,
            "events_synced": self.events_synced,
            "errors": self.errors,
            "uptime": self.uptime.total_seconds(),
            "last_sync": self.last_sync.isoformat() if self.last_sync else None
        }

class EdgeNode:
    """Edge computing node with offline capabilities."""
    
    def __init__(self, config: EdgeNodeConfig):
        self.config = config
        self.node_id = config.node_id or f"edge_{uuid.uuid4().hex[:8]}"
        self.status = EdgeNodeStatus.INITIALIZING
        self.lock = Lock()
        self.running = False
        self.start_time = datetime.now()
        
        # Storage
        self.storage_path = f"edge_data_{self.node_id}"
        self.db_path = os.path.join(self.storage_path, "edge_node.db")
        self.events: List[EdgeEvent] = []
        self.event_handlers: Dict[str, Callable] = {}
        
        # Metrics
        self.metrics = EdgeMetrics()
        
        # Sync state
        self.last_heartbeat = datetime.now()
        self.sync_in_progress = False
        
        # Background tasks
        self.heartbeat_task = None
        self.sync_task = None
        self.metrics_task = None
        
        # Initialize storage
        self._initialize_storage()
        
    async def start(self):
        """Start the edge node."""
        logger.info(f"Starting edge node {self.node_id}")
        
        with self.lock:
            if self.running:
                return
            
            self.running = True
            self.status = EdgeNodeStatus.OFFLINE if self.config.offline_mode else EdgeNodeStatus.ONLINE
        
        # Start background tasks
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self.sync_task = asyncio.create_task(self._sync_loop())
        self.metrics_task = asyncio.create_task(self._metrics_loop())
        
        # Load persisted events
        await self._load_events()
        
        logger.info(f"Edge node {self.node_id} started successfully")
        
    async def stop(self):
        """Stop the edge node."""
        logger.info(f"Stopping edge node {self.node_id}")
        
        with self.lock:
            if not self.running:
                return
            
            self.running = False
            self.status = EdgeNodeStatus.SHUTDOWN
        
        # Cancel background tasks
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.sync_task:
            self.sync_task.cancel()
        if self.metrics_task:
            self.metrics_task.cancel()
        
        # Final sync
        await self._sync_events()
        
        # Persist events
        await self._persist_events()
        
        logger.info(f"Edge node {self.node_id} stopped")
        
    async def process_event(self, event_type: str, data: Dict[str, Any],
                           metadata: Dict[str, Any] = None) -> EdgeEvent:
        """Process an event on the edge node."""
        event_id = f"event_{uuid.uuid4().hex[:8]}"
        
        event = EdgeEvent(
            id=event_id,
            event_type=event_type,
            timestamp=datetime.now(),
            data=data,
            node_id=self.node_id,
            metadata=metadata or {}
        )
        
        # Add to local storage
        with self.lock:
            self.events.append(event)
            self.metrics.events_processed += 1
        
        # Process with registered handler
        if event_type in self.event_handlers:
            try:
                await self.event_handlers[event_type](event)
                event.processed = True
            except Exception as e:
                logger.error(f"Error processing event {event_id}: {e}")
                self.metrics.errors += 1
        
        # Persist event
        await self._persist_event(event)
        
        logger.debug(f"Processed event {event_id} of type {event_type}")
        return event
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler."""
        self.event_handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")
    
    async def get_events(self, event_type: str = None, limit: int = 100,
                        synced_only: bool = False) -> List[EdgeEvent]:
        """Get events from the edge node."""
        with self.lock:
            events = self.events.copy()
        
        # Filter by type
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Filter by sync status
        if synced_only:
            events = [e for e in events if e.synced]
        
        # Sort by timestamp (newest first)
        events.sort(key=lambda x: x.timestamp, reverse=True)
        
        return events[:limit]
    
    async def get_metrics(self) -> EdgeMetrics:
        """Get current node metrics."""
        await self._update_metrics()
        return self.metrics
    
    async def get_status(self) -> Dict[str, Any]:
        """Get node status information."""
        return {
            "node_id": self.node_id,
            "node_name": self.config.node_name,
            "status": self.status.value,
            "location": self.config.location,
            "capabilities": self.config.capabilities,
            "uptime": (datetime.now() - self.start_time).total_seconds(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "events_count": len(self.events),
            "sync_in_progress": self.sync_in_progress,
            "metrics": self.metrics.to_dict()
        }
    
    async def sync_now(self) -> bool:
        """Trigger immediate synchronization."""
        if self.sync_in_progress:
            return False
        
        return await self._sync_events()
    
    async def clear_synced_events(self):
        """Clear events that have been successfully synced."""
        with self.lock:
            original_count = len(self.events)
            self.events = [e for e in self.events if not e.synced]
            cleared_count = original_count - len(self.events)
        
        if cleared_count > 0:
            logger.info(f"Cleared {cleared_count} synced events")
    
    async def _heartbeat_loop(self):
        """Background heartbeat loop."""
        while self.running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self.config.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(self.config.heartbeat_interval)
    
    async def _sync_loop(self):
        """Background synchronization loop."""
        while self.running:
            try:
                await self._sync_events()
                await asyncio.sleep(self.config.sync_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Sync error: {e}")
                await asyncio.sleep(self.config.sync_interval)
    
    async def _metrics_loop(self):
        """Background metrics update loop."""
        while self.running:
            try:
                await self._update_metrics()
                await asyncio.sleep(60)  # Update metrics every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics update error: {e}")
                await asyncio.sleep(60)
    
    async def _send_heartbeat(self):
        """Send heartbeat to central system."""
        self.last_heartbeat = datetime.now()
        
        # In a real implementation, this would send to central system
        # For now, just update status based on connectivity
        if self.config.central_endpoint:
            try:
                # Simulate network check
                await asyncio.sleep(0.1)
                if self.status == EdgeNodeStatus.OFFLINE:
                    self.status = EdgeNodeStatus.ONLINE
                    logger.info(f"Edge node {self.node_id} is now online")
            except Exception:
                if self.status == EdgeNodeStatus.ONLINE:
                    self.status = EdgeNodeStatus.OFFLINE
                    logger.warning(f"Edge node {self.node_id} is now offline")
    
    async def _sync_events(self) -> bool:
        """Synchronize events with central system."""
        if self.sync_in_progress:
            return False
        
        self.sync_in_progress = True
        
        try:
            # Get unsynced events
            unsynced_events = [e for e in self.events if not e.synced]
            
            if not unsynced_events:
                return True
            
            # In a real implementation, this would sync with central system
            # For now, simulate sync process
            logger.info(f"Syncing {len(unsynced_events)} events")
            
            # Simulate network delay
            await asyncio.sleep(0.5)
            
            # Mark events as synced
            for event in unsynced_events:
                event.synced = True
                self.metrics.events_synced += 1
            
            self.metrics.last_sync = datetime.now()
            
            # Persist updated events
            await self._persist_events()
            
            logger.info(f"Successfully synced {len(unsynced_events)} events")
            return True
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            self.metrics.errors += 1
            return False
        finally:
            self.sync_in_progress = False
    
    async def _update_metrics(self):
        """Update node metrics."""
        # Simulate system metrics collection
        import psutil
        
        try:
            self.metrics.cpu_usage = psutil.cpu_percent()
            self.metrics.memory_usage = psutil.virtual_memory().percent
            
            # Calculate storage usage
            if os.path.exists(self.storage_path):
                storage_size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(self.storage_path)
                    for filename in filenames
                )
                self.metrics.storage_usage = (storage_size / (1024 * 1024)) / self.config.max_storage_mb * 100
            
            self.metrics.uptime = datetime.now() - self.start_time
            
        except ImportError:
            # Fallback if psutil not available
            self.metrics.cpu_usage = 0.0
            self.metrics.memory_usage = 0.0
            self.metrics.storage_usage = 0.0
    
    def _initialize_storage(self):
        """Initialize local storage."""
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Initialize SQLite database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                data TEXT NOT NULL,
                node_id TEXT NOT NULL,
                processed BOOLEAN DEFAULT FALSE,
                synced BOOLEAN DEFAULT FALSE,
                retry_count INTEGER DEFAULT 0,
                metadata TEXT DEFAULT '{}'
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def _persist_event(self, event: EdgeEvent):
        """Persist a single event to storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO events 
            (id, event_type, timestamp, data, node_id, processed, synced, retry_count, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.id,
            event.event_type,
            event.timestamp.isoformat(),
            json.dumps(event.data),
            event.node_id,
            event.processed,
            event.synced,
            event.retry_count,
            json.dumps(event.metadata)
        ))
        
        conn.commit()
        conn.close()
    
    async def _persist_events(self):
        """Persist all events to storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for event in self.events:
            cursor.execute('''
                INSERT OR REPLACE INTO events 
                (id, event_type, timestamp, data, node_id, processed, synced, retry_count, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.id,
                event.event_type,
                event.timestamp.isoformat(),
                json.dumps(event.data),
                event.node_id,
                event.processed,
                event.synced,
                event.retry_count,
                json.dumps(event.metadata)
            ))
        
        conn.commit()
        conn.close()
    
    async def _load_events(self):
        """Load events from storage."""
        if not os.path.exists(self.db_path):
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM events ORDER BY timestamp DESC LIMIT 1000')
        rows = cursor.fetchall()
        
        events = []
        for row in rows:
            event = EdgeEvent(
                id=row[0],
                event_type=row[1],
                timestamp=datetime.fromisoformat(row[2]),
                data=json.loads(row[3]),
                node_id=row[4],
                processed=bool(row[5]),
                synced=bool(row[6]),
                retry_count=row[7],
                metadata=json.loads(row[8])
            )
            events.append(event)
        
        with self.lock:
            self.events = events
        
        conn.close()
        logger.info(f"Loaded {len(events)} events from storage")
