"""
Connection pool manager for enterprise integrations.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, AsyncContextManager, Callable
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import weakref
from enum import Enum
import time

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Connection states."""
    IDLE = "idle"
    ACTIVE = "active"
    CLOSED = "closed"
    ERROR = "error"


@dataclass
class PoolConfig:
    """Connection pool configuration."""
    min_size: int = 1
    max_size: int = 10
    max_overflow: int = 20
    pool_timeout: float = 30.0
    pool_recycle: int = 3600  # Recycle connections after 1 hour
    pool_pre_ping: bool = True
    retry_on_disconnect: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    health_check_interval: float = 60.0
    connection_timeout: float = 30.0
    idle_timeout: float = 300.0  # Close idle connections after 5 minutes


@dataclass
class ConnectionInfo:
    """Connection information."""
    connection_id: str
    created_at: datetime
    last_used: datetime
    state: ConnectionState
    use_count: int = 0
    error_count: int = 0
    connection: Any = None
    
    @property
    def age(self) -> float:
        """Get connection age in seconds."""
        return (datetime.utcnow() - self.created_at).total_seconds()
    
    @property
    def idle_time(self) -> float:
        """Get idle time in seconds."""
        return (datetime.utcnow() - self.last_used).total_seconds()
    
    @property
    def is_stale(self) -> bool:
        """Check if connection is stale."""
        return self.age > 3600  # 1 hour


class ConnectionPool:
    """Manages connection pooling for enterprise integrations."""
    
    def __init__(self, config: PoolConfig, connection_factory: Callable):
        self.config = config
        self.connection_factory = connection_factory
        self.connections: Dict[str, ConnectionInfo] = {}
        self.available_connections: asyncio.Queue = asyncio.Queue()
        self.active_connections: Dict[str, ConnectionInfo] = {}
        self.lock = asyncio.Lock()
        self.closed = False
        self.stats = {
            'total_created': 0,
            'total_closed': 0,
            'current_size': 0,
            'current_active': 0,
            'total_requests': 0,
            'total_errors': 0,
            'pool_hits': 0,
            'pool_misses': 0
        }
        
        # Start background tasks
        self._health_check_task = None
        self._cleanup_task = None
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background maintenance tasks."""
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _health_check_loop(self):
        """Background health check loop."""
        while not self.closed:
            try:
                await self._health_check()
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(5)
    
    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while not self.closed:
            try:
                await self._cleanup_idle_connections()
                await asyncio.sleep(60)  # Run cleanup every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                await asyncio.sleep(5)
    
    async def _create_connection(self) -> ConnectionInfo:
        """Create a new connection."""
        try:
            connection = await self.connection_factory()
            connection_id = f"conn_{int(time.time() * 1000000)}"
            
            conn_info = ConnectionInfo(
                connection_id=connection_id,
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow(),
                state=ConnectionState.IDLE,
                connection=connection
            )
            
            self.connections[connection_id] = conn_info
            self.stats['total_created'] += 1
            self.stats['current_size'] += 1
            
            logger.debug(f"Created connection {connection_id}")
            return conn_info
            
        except Exception as e:
            self.stats['total_errors'] += 1
            logger.error(f"Failed to create connection: {e}")
            raise
    
    async def _close_connection(self, conn_info: ConnectionInfo):
        """Close a connection."""
        try:
            if conn_info.connection and hasattr(conn_info.connection, 'close'):
                await conn_info.connection.close()
            
            conn_info.state = ConnectionState.CLOSED
            
            if conn_info.connection_id in self.connections:
                del self.connections[conn_info.connection_id]
            
            if conn_info.connection_id in self.active_connections:
                del self.active_connections[conn_info.connection_id]
            
            self.stats['total_closed'] += 1
            self.stats['current_size'] -= 1
            
            logger.debug(f"Closed connection {conn_info.connection_id}")
            
        except Exception as e:
            logger.error(f"Error closing connection {conn_info.connection_id}: {e}")
    
    async def _validate_connection(self, conn_info: ConnectionInfo) -> bool:
        """Validate if connection is still healthy."""
        try:
            if not self.config.pool_pre_ping:
                return True
            
            # Check if connection has a ping method
            if hasattr(conn_info.connection, 'ping'):
                return await conn_info.connection.ping()
            
            # Check if connection has a test method
            if hasattr(conn_info.connection, 'test_connection'):
                return await conn_info.connection.test_connection()
            
            # Default to assuming connection is valid
            return True
            
        except Exception as e:
            logger.warning(f"Connection validation failed for {conn_info.connection_id}: {e}")
            return False
    
    async def _health_check(self):
        """Perform health check on all connections."""
        async with self.lock:
            unhealthy_connections = []
            
            for conn_id, conn_info in self.connections.items():
                if conn_info.state == ConnectionState.IDLE:
                    if not await self._validate_connection(conn_info):
                        unhealthy_connections.append(conn_info)
                        conn_info.error_count += 1
                    elif conn_info.is_stale:
                        unhealthy_connections.append(conn_info)
            
            # Close unhealthy connections
            for conn_info in unhealthy_connections:
                await self._close_connection(conn_info)
    
    async def _cleanup_idle_connections(self):
        """Clean up idle connections."""
        async with self.lock:
            idle_connections = []
            
            for conn_id, conn_info in self.connections.items():
                if (conn_info.state == ConnectionState.IDLE and 
                    conn_info.idle_time > self.config.idle_timeout):
                    idle_connections.append(conn_info)
            
            # Close idle connections (but keep minimum pool size)
            current_size = len(self.connections)
            for conn_info in idle_connections:
                if current_size > self.config.min_size:
                    await self._close_connection(conn_info)
                    current_size -= 1
    
    async def _ensure_min_connections(self):
        """Ensure minimum number of connections."""
        current_size = len(self.connections)
        
        while current_size < self.config.min_size:
            try:
                conn_info = await self._create_connection()
                await self.available_connections.put(conn_info)
                current_size += 1
            except Exception as e:
                logger.error(f"Failed to create minimum connections: {e}")
                break
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool."""
        if self.closed:
            raise RuntimeError("Connection pool is closed")
        
        self.stats['total_requests'] += 1
        conn_info = None
        
        try:
            # Try to get an available connection
            try:
                conn_info = await asyncio.wait_for(
                    self.available_connections.get(),
                    timeout=self.config.pool_timeout
                )
                self.stats['pool_hits'] += 1
                
                # Validate connection
                if not await self._validate_connection(conn_info):
                    await self._close_connection(conn_info)
                    conn_info = None
                    
            except asyncio.TimeoutError:
                self.stats['pool_misses'] += 1
                
                # Check if we can create a new connection
                async with self.lock:
                    total_connections = len(self.connections) + len(self.active_connections)
                    
                    if total_connections < (self.config.max_size + self.config.max_overflow):
                        conn_info = await self._create_connection()
                    else:
                        raise RuntimeError("Connection pool exhausted")
            
            # If we still don't have a connection, create one
            if not conn_info:
                conn_info = await self._create_connection()
            
            # Mark connection as active
            conn_info.state = ConnectionState.ACTIVE
            conn_info.last_used = datetime.utcnow()
            conn_info.use_count += 1
            
            async with self.lock:
                self.active_connections[conn_info.connection_id] = conn_info
                self.stats['current_active'] = len(self.active_connections)
            
            logger.debug(f"Acquired connection {conn_info.connection_id}")
            yield conn_info.connection
            
        except Exception as e:
            self.stats['total_errors'] += 1
            logger.error(f"Error getting connection: {e}")
            raise
        
        finally:
            # Return connection to pool
            if conn_info:
                await self._return_connection(conn_info)
    
    async def _return_connection(self, conn_info: ConnectionInfo):
        """Return a connection to the pool."""
        try:
            async with self.lock:
                if conn_info.connection_id in self.active_connections:
                    del self.active_connections[conn_info.connection_id]
                    self.stats['current_active'] = len(self.active_connections)
            
            # Check if connection should be recycled
            if (conn_info.age > self.config.pool_recycle or 
                conn_info.error_count > 0 or
                not await self._validate_connection(conn_info)):
                
                await self._close_connection(conn_info)
                logger.debug(f"Recycled connection {conn_info.connection_id}")
                return
            
            # Return to available pool
            conn_info.state = ConnectionState.IDLE
            conn_info.last_used = datetime.utcnow()
            
            await self.available_connections.put(conn_info)
            logger.debug(f"Returned connection {conn_info.connection_id}")
            
        except Exception as e:
            logger.error(f"Error returning connection {conn_info.connection_id}: {e}")
            await self._close_connection(conn_info)
    
    async def initialize(self):
        """Initialize the connection pool."""
        logger.info("Initializing connection pool")
        await self._ensure_min_connections()
        logger.info(f"Connection pool initialized with {len(self.connections)} connections")
    
    async def close(self):
        """Close the connection pool."""
        logger.info("Closing connection pool")
        self.closed = True
        
        # Cancel background tasks
        if self._health_check_task:
            self._health_check_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Close all connections
        async with self.lock:
            all_connections = list(self.connections.values()) + list(self.active_connections.values())
            
            for conn_info in all_connections:
                await self._close_connection(conn_info)
        
        # Clear queues
        while not self.available_connections.empty():
            try:
                self.available_connections.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        logger.info("Connection pool closed")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            **self.stats,
            'available_connections': self.available_connections.qsize(),
            'pool_size': len(self.connections),
            'active_connections': len(self.active_connections),
            'pool_utilization': len(self.active_connections) / max(1, len(self.connections))
        }
    
    def get_connection_info(self) -> List[Dict[str, Any]]:
        """Get information about all connections."""
        info = []
        
        for conn_info in self.connections.values():
            info.append({
                'connection_id': conn_info.connection_id,
                'state': conn_info.state.value,
                'age': conn_info.age,
                'idle_time': conn_info.idle_time,
                'use_count': conn_info.use_count,
                'error_count': conn_info.error_count,
                'is_stale': conn_info.is_stale
            })
        
        return info


def create_connection_pool(connection_factory: Callable, config: Optional[PoolConfig] = None) -> ConnectionPool:
    """Factory function to create a connection pool."""
    if config is None:
        config = PoolConfig()
    
    return ConnectionPool(config, connection_factory)
