"""
Connector manager for handling multiple enterprise platform integrations.
"""

import asyncio
import logging
import threading
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid

from .base_connector import BaseConnector, ConnectorConfig, ConnectionStatus

logger = logging.getLogger(__name__)


class RegistryStatus(Enum):
    """Registry status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"


@dataclass
class ConnectorRegistration:
    """Connector registration information."""
    connector_id: str
    connector: BaseConnector
    registered_at: datetime = field(default_factory=datetime.now)
    last_health_check: Optional[datetime] = None
    health_status: bool = True
    error_count: int = 0
    last_error: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConnectorRegistry:
    """Registry for managing connector instances."""
    
    def __init__(self):
        """Initialize the connector registry."""
        self.connectors: Dict[str, ConnectorRegistration] = {}
        self.lock = threading.RLock()
        self.status = RegistryStatus.ACTIVE
        self.logger = logging.getLogger(f"{__name__}.ConnectorRegistry")
    
    def register(self, connector: BaseConnector, tags: List[str] = None, 
                metadata: Dict[str, Any] = None) -> str:
        """Register a connector in the registry."""
        connector_id = str(uuid.uuid4())
        
        with self.lock:
            registration = ConnectorRegistration(
                connector_id=connector_id,
                connector=connector,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            self.connectors[connector_id] = registration
            self.logger.info(f"Registered connector: {connector.config.name} ({connector_id})")
        
        return connector_id
    
    def unregister(self, connector_id: str) -> bool:
        """Unregister a connector from the registry."""
        with self.lock:
            if connector_id in self.connectors:
                registration = self.connectors.pop(connector_id)
                self.logger.info(f"Unregistered connector: {registration.connector.config.name}")
                return True
            return False
    
    def get_connector(self, connector_id: str) -> Optional[BaseConnector]:
        """Get a connector by ID."""
        with self.lock:
            registration = self.connectors.get(connector_id)
            return registration.connector if registration else None
    
    def get_connectors_by_type(self, connector_type: str) -> List[BaseConnector]:
        """Get all connectors of a specific type."""
        with self.lock:
            return [
                reg.connector for reg in self.connectors.values()
                if reg.connector.config.connector_type.value == connector_type
            ]
    
    def get_connectors_by_tag(self, tag: str) -> List[BaseConnector]:
        """Get all connectors with a specific tag."""
        with self.lock:
            return [
                reg.connector for reg in self.connectors.values()
                if tag in reg.tags
            ]
    
    def get_all_connectors(self) -> List[BaseConnector]:
        """Get all registered connectors."""
        with self.lock:
            return [reg.connector for reg in self.connectors.values()]
    
    def get_registry_status(self) -> Dict[str, Any]:
        """Get registry status and statistics."""
        with self.lock:
            total_connectors = len(self.connectors)
            healthy_connectors = sum(1 for reg in self.connectors.values() if reg.health_status)
            
            status_counts = {}
            for reg in self.connectors.values():
                status = reg.connector.get_status().value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                'registry_status': self.status.value,
                'total_connectors': total_connectors,
                'healthy_connectors': healthy_connectors,
                'unhealthy_connectors': total_connectors - healthy_connectors,
                'status_breakdown': status_counts,
                'last_updated': datetime.now().isoformat()
            }


class ConnectorManager:
    """Manager for handling multiple connectors and their lifecycle."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the connector manager."""
        self.config = config or {}
        self.registry = ConnectorRegistry()
        self.health_check_interval = self.config.get('health_check_interval', 60)  # seconds
        self.auto_reconnect = self.config.get('auto_reconnect', True)
        self.max_reconnect_attempts = self.config.get('max_reconnect_attempts', 3)
        
        self.lock = threading.RLock()
        self.running = False
        self.health_check_task = None
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        self.logger = logging.getLogger(f"{__name__}.ConnectorManager")
        self.logger.info("Connector manager initialized")
    
    def add_connector(self, connector: BaseConnector, tags: List[str] = None,
                     metadata: Dict[str, Any] = None) -> str:
        """Add a connector to the manager."""
        connector_id = self.registry.register(connector, tags, metadata)
        self._emit_event('connector_added', {
            'connector_id': connector_id,
            'connector_name': connector.config.name,
            'connector_type': connector.config.connector_type.value
        })
        return connector_id
    
    def remove_connector(self, connector_id: str) -> bool:
        """Remove a connector from the manager."""
        connector = self.registry.get_connector(connector_id)
        if connector:
            # Disconnect before removing
            asyncio.create_task(connector.disconnect())
            
            success = self.registry.unregister(connector_id)
            if success:
                self._emit_event('connector_removed', {
                    'connector_id': connector_id,
                    'connector_name': connector.config.name
                })
            return success
        return False
    
    def get_connector(self, connector_id: str) -> Optional[BaseConnector]:
        """Get a connector by ID."""
        return self.registry.get_connector(connector_id)
    
    def get_connectors_by_type(self, connector_type: str) -> List[BaseConnector]:
        """Get all connectors of a specific type."""
        return self.registry.get_connectors_by_type(connector_type)
    
    def get_connectors_by_tag(self, tag: str) -> List[BaseConnector]:
        """Get all connectors with a specific tag."""
        return self.registry.get_connectors_by_tag(tag)
    
    async def connect_all(self) -> Dict[str, bool]:
        """Connect all registered connectors."""
        results = {}
        connectors = self.registry.get_all_connectors()
        
        self.logger.info(f"Connecting {len(connectors)} connectors")
        
        # Connect all connectors concurrently
        tasks = []
        for connector in connectors:
            task = asyncio.create_task(self._connect_with_retry(connector))
            tasks.append((connector.config.name, task))
        
        # Wait for all connections to complete
        for name, task in tasks:
            try:
                success = await task
                results[name] = success
            except Exception as e:
                self.logger.error(f"Failed to connect {name}: {e}")
                results[name] = False
        
        successful = sum(1 for success in results.values() if success)
        self.logger.info(f"Connected {successful}/{len(connectors)} connectors")
        
        return results
    
    async def disconnect_all(self) -> Dict[str, bool]:
        """Disconnect all registered connectors."""
        results = {}
        connectors = self.registry.get_all_connectors()
        
        self.logger.info(f"Disconnecting {len(connectors)} connectors")
        
        # Disconnect all connectors concurrently
        tasks = []
        for connector in connectors:
            task = asyncio.create_task(connector.disconnect())
            tasks.append((connector.config.name, task))
        
        # Wait for all disconnections to complete
        for name, task in tasks:
            try:
                success = await task
                results[name] = success
            except Exception as e:
                self.logger.error(f"Failed to disconnect {name}: {e}")
                results[name] = False
        
        return results
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all connectors."""
        results = {}
        connectors = self.registry.get_all_connectors()
        
        # Run health checks concurrently
        tasks = []
        for connector in connectors:
            task = asyncio.create_task(connector.health_check())
            tasks.append((connector.config.name, task))
        
        # Collect results
        for name, task in tasks:
            try:
                health_data = await task
                results[name] = health_data
                
                # Update registry health status
                with self.registry.lock:
                    for reg in self.registry.connectors.values():
                        if reg.connector.config.name == name:
                            reg.last_health_check = datetime.now()
                            reg.health_status = health_data.get('healthy', False)
                            if not reg.health_status:
                                reg.error_count += 1
                                reg.last_error = health_data.get('error')
                            break
                            
            except Exception as e:
                self.logger.error(f"Health check failed for {name}: {e}")
                results[name] = {
                    'connector_name': name,
                    'healthy': False,
                    'error': str(e)
                }
        
        return results
    
    async def start_health_monitoring(self):
        """Start periodic health monitoring."""
        if self.running:
            return
        
        self.running = True
        self.health_check_task = asyncio.create_task(self._health_monitor_loop())
        self.logger.info("Started health monitoring")
    
    async def stop_health_monitoring(self):
        """Stop periodic health monitoring."""
        self.running = False
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Stopped health monitoring")
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """Add an event handler."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def remove_event_handler(self, event_type: str, handler: Callable):
        """Remove an event handler."""
        if event_type in self.event_handlers:
            try:
                self.event_handlers[event_type].remove(handler)
            except ValueError:
                pass
    
    def get_manager_status(self) -> Dict[str, Any]:
        """Get manager status and statistics."""
        registry_status = self.registry.get_registry_status()
        
        return {
            'manager_status': 'running' if self.running else 'stopped',
            'health_monitoring': self.running,
            'health_check_interval': self.health_check_interval,
            'auto_reconnect': self.auto_reconnect,
            'registry': registry_status,
            'event_handlers': {
                event_type: len(handlers) 
                for event_type, handlers in self.event_handlers.items()
            }
        }
    
    async def _connect_with_retry(self, connector: BaseConnector) -> bool:
        """Connect a connector with retry logic."""
        for attempt in range(self.max_reconnect_attempts):
            try:
                success = await connector.connect()
                if success:
                    return True
                
                if attempt < self.max_reconnect_attempts - 1:
                    await asyncio.sleep(connector.config.retry_delay * (2 ** attempt))
                    
            except Exception as e:
                self.logger.error(f"Connection attempt {attempt + 1} failed for {connector.config.name}: {e}")
                if attempt < self.max_reconnect_attempts - 1:
                    await asyncio.sleep(connector.config.retry_delay * (2 ** attempt))
        
        return False
    
    async def _health_monitor_loop(self):
        """Main health monitoring loop."""
        while self.running:
            try:
                health_results = await self.health_check_all()
                
                # Handle unhealthy connectors
                if self.auto_reconnect:
                    for name, health_data in health_results.items():
                        if not health_data.get('healthy', False):
                            connector = next(
                                (c for c in self.registry.get_all_connectors() 
                                 if c.config.name == name), None
                            )
                            if connector and connector.get_status() == ConnectionStatus.ERROR:
                                self.logger.warning(f"Attempting to reconnect unhealthy connector: {name}")
                                asyncio.create_task(connector.reconnect())
                
                # Emit health check event
                self._emit_event('health_check_completed', {
                    'timestamp': datetime.now().isoformat(),
                    'results': health_results
                })
                
                await asyncio.sleep(self.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to registered handlers."""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(event_type, data)
                except Exception as e:
                    self.logger.error(f"Event handler error for {event_type}: {e}")
    
    async def shutdown(self):
        """Shutdown the connector manager."""
        self.logger.info("Shutting down connector manager")
        
        # Stop health monitoring
        await self.stop_health_monitoring()
        
        # Disconnect all connectors
        await self.disconnect_all()
        
        self.logger.info("Connector manager shutdown complete")
