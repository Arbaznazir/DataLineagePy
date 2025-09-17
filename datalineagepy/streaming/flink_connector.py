"""
Apache Flink connector for real-time data lineage tracking.
Provides integration with Flink streaming applications for lineage extraction.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, AsyncGenerator
from datetime import datetime, timedelta
from enum import Enum
import threading
import aiohttp
import time

from .kafka_streams_connector import StreamingEvent, StreamingEventType, BaseStreamingConnector

logger = logging.getLogger(__name__)


@dataclass
class FlinkConfig:
    """Configuration for Flink connector."""
    job_manager_host: str = "localhost"
    job_manager_port: int = 8081
    job_manager_url: Optional[str] = None
    parallelism: int = 1
    checkpoint_interval: int = 5000
    restart_strategy: str = "fixed-delay"
    restart_attempts: int = 3
    restart_delay: int = 10000
    polling_interval: float = 5.0
    timeout: int = 30
    enable_metrics: bool = True
    enable_checkpoints: bool = True
    enable_savepoints: bool = True
    
    def __post_init__(self):
        if not self.job_manager_url:
            self.job_manager_url = f"http://{self.job_manager_host}:{self.job_manager_port}"


@dataclass
class FlinkJob:
    """Represents a Flink job."""
    job_id: str
    name: str
    state: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    parallelism: int = 1
    vertices: List[Dict[str, Any]] = field(default_factory=list)
    execution_graph: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'job_id': self.job_id,
            'name': self.name,
            'state': self.state,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'parallelism': self.parallelism,
            'vertices': self.vertices,
            'execution_graph': self.execution_graph,
            'metrics': self.metrics,
            'checkpoints': self.checkpoints,
        }


@dataclass
class FlinkVertex:
    """Represents a Flink job vertex."""
    vertex_id: str
    name: str
    parallelism: int
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'vertex_id': self.vertex_id,
            'name': self.name,
            'parallelism': self.parallelism,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'tasks': self.tasks,
            'metrics': self.metrics,
        }


class FlinkConnector(BaseStreamingConnector):
    """Apache Flink connector for real-time lineage tracking."""
    
    def __init__(self, config: FlinkConfig):
        self.config = config
        self.running = False
        self.session: Optional[aiohttp.ClientSession] = None
        self.jobs: Dict[str, FlinkJob] = {}
        self.event_handlers: Dict[StreamingEventType, List[Callable]] = {}
        self.stats = {
            'jobs_tracked': 0,
            'events_generated': 0,
            'api_calls': 0,
            'errors': 0,
            'last_poll_time': None,
        }
        self._lock = threading.Lock()
        self._polling_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the Flink connector."""
        try:
            # Create HTTP session
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            # Test connection
            await self._test_connection()
            
            self.running = True
            
            # Start polling task
            self._polling_task = asyncio.create_task(self._poll_jobs())
            
            logger.info(f"Flink connector started, connected to {self.config.job_manager_url}")
            
        except Exception as e:
            logger.error(f"Failed to start Flink connector: {e}")
            if self.session:
                await self.session.close()
                self.session = None
            raise
    
    async def stop(self):
        """Stop the Flink connector."""
        self.running = False
        
        # Cancel polling task
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
        
        # Close HTTP session
        if self.session:
            await self.session.close()
            self.session = None
        
        logger.info("Flink connector stopped")
    
    async def consume_events(self) -> AsyncGenerator[StreamingEvent, None]:
        """Consume streaming events from Flink."""
        if not self.running:
            return
        
        while self.running:
            try:
                # Get current jobs
                jobs = await self._get_jobs()
                
                # Process each job
                for job in jobs:
                    # Generate events for job state changes
                    async for event in self._generate_job_events(job):
                        yield event
                    
                    # Generate events for vertices
                    vertices = await self._get_job_vertices(job.job_id)
                    for vertex in vertices:
                        async for event in self._generate_vertex_events(job, vertex):
                            yield event
                
                # Wait before next poll
                await asyncio.sleep(self.config.polling_interval)
                
            except Exception as e:
                logger.error(f"Error consuming Flink events: {e}")
                with self._lock:
                    self.stats['errors'] += 1
                await asyncio.sleep(self.config.polling_interval)
    
    async def publish_lineage(self, event: StreamingEvent):
        """Publish lineage event (not applicable for Flink connector)."""
        # Flink connector is read-only, doesn't publish back to Flink
        logger.debug(f"Lineage event {event.event_id} processed (Flink connector is read-only)")
    
    async def _test_connection(self):
        """Test connection to Flink JobManager."""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        try:
            url = f"{self.config.job_manager_url}/config"
            async with self.session.get(url) as response:
                if response.status == 200:
                    config_data = await response.json()
                    logger.info(f"Connected to Flink cluster: {config_data.get('flink-version', 'unknown')}")
                else:
                    raise Exception(f"HTTP {response.status}: {await response.text()}")
        except Exception as e:
            raise Exception(f"Failed to connect to Flink JobManager: {e}")
    
    async def _poll_jobs(self):
        """Poll for job updates."""
        while self.running:
            try:
                # Get current jobs
                jobs = await self._get_jobs()
                
                # Update job tracking
                with self._lock:
                    for job in jobs:
                        self.jobs[job.job_id] = job
                    self.stats['jobs_tracked'] = len(self.jobs)
                    self.stats['last_poll_time'] = datetime.utcnow()
                
                await asyncio.sleep(self.config.polling_interval)
                
            except Exception as e:
                logger.error(f"Error polling jobs: {e}")
                await asyncio.sleep(self.config.polling_interval)
    
    async def _get_jobs(self) -> List[FlinkJob]:
        """Get list of Flink jobs."""
        if not self.session:
            return []
        
        try:
            url = f"{self.config.job_manager_url}/jobs"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    jobs = []
                    
                    for job_data in data.get('jobs', []):
                        job = FlinkJob(
                            job_id=job_data['id'],
                            name=job_data.get('name', 'Unknown'),
                            state=job_data['state'],
                            start_time=datetime.fromtimestamp(job_data['start-time'] / 1000),
                            end_time=datetime.fromtimestamp(job_data['end-time'] / 1000) if job_data.get('end-time') else None,
                            duration=job_data.get('duration'),
                        )
                        jobs.append(job)
                    
                    with self._lock:
                        self.stats['api_calls'] += 1
                    
                    return jobs
                else:
                    logger.error(f"Failed to get jobs: HTTP {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting jobs: {e}")
            with self._lock:
                self.stats['errors'] += 1
            return []
    
    async def _get_job_vertices(self, job_id: str) -> List[FlinkVertex]:
        """Get vertices for a specific job."""
        if not self.session:
            return []
        
        try:
            url = f"{self.config.job_manager_url}/jobs/{job_id}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    vertices = []
                    
                    for vertex_data in data.get('vertices', []):
                        vertex = FlinkVertex(
                            vertex_id=vertex_data['id'],
                            name=vertex_data['name'],
                            parallelism=vertex_data['parallelism'],
                            status=vertex_data['status'],
                            start_time=datetime.fromtimestamp(vertex_data['start-time'] / 1000) if vertex_data.get('start-time') else None,
                            end_time=datetime.fromtimestamp(vertex_data['end-time'] / 1000) if vertex_data.get('end-time') else None,
                            duration=vertex_data.get('duration'),
                        )
                        vertices.append(vertex)
                    
                    with self._lock:
                        self.stats['api_calls'] += 1
                    
                    return vertices
                else:
                    logger.error(f"Failed to get job vertices: HTTP {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting job vertices: {e}")
            with self._lock:
                self.stats['errors'] += 1
            return []
    
    async def _generate_job_events(self, job: FlinkJob) -> AsyncGenerator[StreamingEvent, None]:
        """Generate events for job state changes."""
        try:
            # Check if this is a new job or state change
            existing_job = self.jobs.get(job.job_id)
            if not existing_job or existing_job.state != job.state:
                event = StreamingEvent(
                    event_id=f"flink_job_{job.job_id}_{job.state}_{int(time.time())}",
                    event_type=StreamingEventType.DATA_TRANSFORMATION,
                    source_topic=f"flink_job_{job.job_id}",
                    application_id=job.name,
                    processor_name="flink_job_manager",
                    timestamp=datetime.utcnow(),
                    payload={
                        'job_id': job.job_id,
                        'job_name': job.name,
                        'state': job.state,
                        'parallelism': job.parallelism,
                        'start_time': job.start_time.isoformat(),
                        'end_time': job.end_time.isoformat() if job.end_time else None,
                        'duration': job.duration,
                    },
                    lineage_info={
                        'entity_type': 'flink_job',
                        'entity_id': job.job_id,
                        'state_change': {
                            'from': existing_job.state if existing_job else None,
                            'to': job.state,
                        }
                    }
                )
                
                with self._lock:
                    self.stats['events_generated'] += 1
                
                yield event
                
        except Exception as e:
            logger.error(f"Error generating job events: {e}")
    
    async def _generate_vertex_events(self, job: FlinkJob, vertex: FlinkVertex) -> AsyncGenerator[StreamingEvent, None]:
        """Generate events for vertex state changes."""
        try:
            # Generate event for vertex
            event = StreamingEvent(
                event_id=f"flink_vertex_{vertex.vertex_id}_{vertex.status}_{int(time.time())}",
                event_type=StreamingEventType.DATA_TRANSFORMATION,
                source_topic=f"flink_vertex_{vertex.vertex_id}",
                application_id=job.name,
                processor_name=vertex.name,
                timestamp=datetime.utcnow(),
                payload={
                    'job_id': job.job_id,
                    'vertex_id': vertex.vertex_id,
                    'vertex_name': vertex.name,
                    'status': vertex.status,
                    'parallelism': vertex.parallelism,
                    'start_time': vertex.start_time.isoformat() if vertex.start_time else None,
                    'end_time': vertex.end_time.isoformat() if vertex.end_time else None,
                    'duration': vertex.duration,
                },
                lineage_info={
                    'entity_type': 'flink_vertex',
                    'entity_id': vertex.vertex_id,
                    'parent_job': job.job_id,
                }
            )
            
            with self._lock:
                self.stats['events_generated'] += 1
            
            yield event
            
        except Exception as e:
            logger.error(f"Error generating vertex events: {e}")
    
    def add_event_handler(self, event_type: StreamingEventType, handler: Callable):
        """Add event handler for specific event type."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def remove_event_handler(self, event_type: StreamingEventType, handler: Callable):
        """Remove event handler."""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].remove(handler)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connector statistics."""
        with self._lock:
            return self.stats.copy()
    
    def get_jobs(self) -> Dict[str, FlinkJob]:
        """Get currently tracked jobs."""
        with self._lock:
            return {job_id: job for job_id, job in self.jobs.items()}
    
    async def get_job_metrics(self, job_id: str) -> Dict[str, Any]:
        """Get metrics for a specific job."""
        if not self.session:
            return {}
        
        try:
            url = f"{self.config.job_manager_url}/jobs/{job_id}/metrics"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    with self._lock:
                        self.stats['api_calls'] += 1
                    
                    return data
                else:
                    logger.error(f"Failed to get job metrics: HTTP {response.status}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Error getting job metrics: {e}")
            with self._lock:
                self.stats['errors'] += 1
            return {}
    
    async def get_job_checkpoints(self, job_id: str) -> List[Dict[str, Any]]:
        """Get checkpoints for a specific job."""
        if not self.session:
            return []
        
        try:
            url = f"{self.config.job_manager_url}/jobs/{job_id}/checkpoints"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    with self._lock:
                        self.stats['api_calls'] += 1
                    
                    return data.get('history', [])
                else:
                    logger.error(f"Failed to get job checkpoints: HTTP {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting job checkpoints: {e}")
            with self._lock:
                self.stats['errors'] += 1
            return []


def create_flink_connector(
    job_manager_host: str = "localhost",
    job_manager_port: int = 8081,
    polling_interval: float = 5.0,
    **kwargs
) -> FlinkConnector:
    """Factory function to create Flink connector."""
    config = FlinkConfig(
        job_manager_host=job_manager_host,
        job_manager_port=job_manager_port,
        polling_interval=polling_interval,
        **kwargs
    )
    return FlinkConnector(config)
